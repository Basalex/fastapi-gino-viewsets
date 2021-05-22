from dataclasses import asdict
from typing import Iterable

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy import asc, desc
from sqlalchemy.sql import ClauseElement, operators as op
from starlette import status
from starlette.requests import Request

from .schemas import BaseDeleteSchema, BaseSchema, BaseModelSchema, BasePaginatedListSchema
from .dynamic_methods import MethodFactory
from .schema_factory import SchemaFactory
from .utils import is_method_overloaded, get_object_or_404

__all__ = [
    'AggregateObjectMixin',
    'CreateModelMixin',
    'DeleteModelMixin',
    'BaseListModelMixin',
    'ListModelMixin',
    'RetrieveModelMixin',
    'UpdateModelMixin',
    'UpdatePartialModelMixin',
]


class BaseMixin:
    base_schema = BaseModelSchema
    input_schema = None
    output_schema = None
    wrapper_schema = None
    params = {}


class ViewSetMeta(type):

    def __new__(mcs, name, bases, attrs):
        model = attrs.get('model')
        if model is not None:
            for base in bases:
                base_schema = getattr(base, 'base_schema', None)
                if base_schema:
                    break
            else:
                raise NotImplementedError(f'Base schema is not implemented for class {name}')
            attrs['input_schema'] = attrs.get(
                'input_schema',
            ) or SchemaFactory.input_schema(
                model,
                base_schema=base_schema,
                exclude=('id', 'created_at', 'updated_at')
            )
            output_schema = attrs.get('output_schema') or SchemaFactory.output_schema(model, base_schema)
            wrapper_schema = attrs.get('wrapper_schema')
            if wrapper_schema is not None:
                output_schema = type(
                    f'{output_schema.__name__}',
                    (wrapper_schema, ),
                    {
                        '__annotations__': {
                            **wrapper_schema.__annotations__,
                            wrapper_schema.__wrapper_key__: output_schema,
                        },
                    },
                )
            attrs['output_schema'] = output_schema
        return super().__new__(mcs, name, bases, attrs)


class BaseModelMixin(BaseMixin, metaclass=ViewSetMeta):
    model = None


class BaseFilterMixin(BaseMixin):
    filter_schema = BaseSchema

    @classmethod
    def _handler_filter(cls, model, field_name, value):
        field_name, _, method = field_name.partition('__')
        field = getattr(model, field_name)

        if method:
            return getattr(op, method)(field, value)

        if isinstance(value, Iterable) and not isinstance(value, str):
            if issubclass(field.type.python_type, (dict, list)):
                return field.contains(value)
            else:
                return field.in_(value)

        if value is None or isinstance(value, bool):
            return field.is_(value)

        return op.eq(field, value)

    @classmethod
    def filter_query(cls, request: Request, query, filter_schema):
        if hasattr(filter_schema, 'dict'):
            filters = filter_schema.dict(exclude_defaults=True).items()
        else:
            filters = [
                (k, v) for k, v in asdict(filter_schema).items() if v is not None
            ]
        return query.where(
            sa.and_(
                cls._handler_filter(cls.model, field_name, value)
                for field_name, value in filters
            ),
        )


class SingleObjectMixin:
    key_name = 'id'
    key_type = int
    retrieve_function = get_object_or_404


class RetrieveModelMixin(SingleObjectMixin, BaseModelMixin):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_method_overloaded(cls, 'retrieve'):
            cls.retrieve = classmethod(
                MethodFactory.make_retrieve(
                    cls.key_name,
                    cls.key_type,
                    cls.wrapper_schema and cls.wrapper_schema.__wrapper_key__,
                ),
            )


class AggregateObjectMixin(BaseFilterMixin):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_method_overloaded(cls, 'retrieve_single_object_data'):
            cls.retrieve_single_object_data = classmethod(
                MethodFactory.make_retrieve_single_object_data(cls.filter_schema)
            )

    @classmethod
    def get_query(cls, request, f=None):
        return NotImplementedError


class BaseListModelMixin(BaseFilterMixin):
    base_list_schema = BasePaginatedListSchema
    list_schema = None
    filter_schema = None
    model = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        model = getattr(cls, 'model', None)
        if model is not None:
            if cls.list_schema is None:
                cls.list_schema = SchemaFactory.list_schema(
                    cls.output_schema,
                    cls.base_list_schema,
                    f'{model.__name__.title()}ListSchema',
                )
            if cls.filter_schema is None:
                cls.filter_schema = SchemaFactory.filter_schema(
                    model, f'{cls.__name__}FilterSchema'
                )
            if not is_method_overloaded(cls, 'retrieve_list'):
                cls.retrieve_list = classmethod(
                    MethodFactory.make_retrieve_list(
                        cls.filter_schema,
                    ),
                )

    @classmethod
    def get_query(cls, request, f=None):
        return cls.model.query

    @classmethod
    def sort_query(cls, request, query, sort):
        columns = query.c
        sort_fields = []
        for field_name in sort:
            _, is_desc, field_name = field_name.rpartition('-')
            field = getattr(columns, field_name, None)
            if field is None and cls.model is not None:
                field = getattr(cls.model, field_name)
            if field is not None:
                sort_fields.append(desc(field) if is_desc else asc(field))
        return query.order_by(*sort_fields) if sort_fields else query

    @classmethod
    async def total(cls, query):
        return await sa.select([sa.func.count()]).select_from(query.alias()).gino.scalar()

    @classmethod
    def paginate(cls, query: ClauseElement, offset: int, limit: int) -> ClauseElement:
        if limit:
            query = query.limit(limit)
        return query.offset(offset)

    @classmethod
    async def prepare_data_hook(cls, query):
        return await query.gino.all()

    @classmethod
    def prepare_response(cls, data, offset, limit, total):
        data = {
            'data': data,
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
            },
        }
        return data


class ListModelMixin(BaseModelMixin, BaseListModelMixin):
    pass


class BaseModelUpdateMixin(BaseModelMixin):
    @classmethod
    async def _update(cls, request, id: int, schema: BaseModel):
        entity = await cls.model.get(id)
        updated_fields = schema.from_orm(request)
        await entity.update(**updated_fields.dict(exclude_unset=True)).apply()
        return cls.output_schema.from_orm(entity)


class CreateModelMixin(BaseModelMixin):
    create_schema = None
    create_status = status.HTTP_201_CREATED

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_method_overloaded(cls, 'create'):
            cls.create = classmethod(
                MethodFactory.make_create(
                    cls.get_create_schema(),
                    cls.wrapper_schema and cls.wrapper_schema.__wrapper_key__,
                )
            )

    @classmethod
    def get_create_schema(cls):
        return cls.create_schema or cls.input_schema


class UpdateModelMixin(SingleObjectMixin, BaseModelMixin):
    put_schema = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.put_schema is None and cls.model is not None:
            cls.put_schema = SchemaFactory.put_schema(cls.model, cls.base_schema)
        if not is_method_overloaded(cls, 'update'):
            cls.update = classmethod(
                MethodFactory.make_update(
                    cls.get_put_schema(),
                    cls.key_name,
                    cls.key_type,
                    cls.wrapper_schema and cls.wrapper_schema.__wrapper_key__,
                )
            )

    @classmethod
    def get_put_schema(cls):
        return cls.put_schema or cls.input_schema


class UpdatePartialModelMixin(SingleObjectMixin, BaseModelUpdateMixin):
    patch_schema = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.patch_schema is None and cls.model is not None:
            cls.patch_schema = SchemaFactory.patch_schema(cls.model, cls.base_schema)
        if not is_method_overloaded(cls, 'update_partial'):
            cls.update_partial = classmethod(
                MethodFactory.make_update_partial(
                    cls.get_patch_schema(),
                    cls.key_name,
                    cls.key_type,
                    cls.wrapper_schema and cls.wrapper_schema.__wrapper_key__,
                )
            )

    @classmethod
    def get_patch_schema(cls):
        return cls.patch_schema


class DeleteModelMixin(SingleObjectMixin, BaseMixin):
    delete_schema = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_method_overloaded(cls, 'delete'):
            cls.delete = classmethod(
                MethodFactory.make_delete(
                    cls.key_name,
                    cls.key_type,
                    cls.wrapper_schema and cls.wrapper_schema.__wrapper_key__,
                ),
            )

    @classmethod
    def get_delete_schema(cls):
        delete_schema = cls.delete_schema or BaseDeleteSchema
        if cls.wrapper_schema is not None:
            delete_schema = type(
                f'W{delete_schema.__name__}',
                (cls.wrapper_schema,),
                {
                    '__annotations__': {
                        **cls.wrapper_schema.__annotations__,
                        cls.wrapper_schema.__wrapper_key__: delete_schema,
                    },
                },
            )
        return delete_schema
