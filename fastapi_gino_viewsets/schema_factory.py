from collections import defaultdict
from typing import List

from ginodantic.gino_model_meta import GinoModelMeta
from pydantic.main import ModelMetaclass

from .utils import create_meta_class

__all__ = ['SchemaFactory']
FIELD_METHODS_BY_TYPE = {
    int: ('lt', 'gt', 'le', 'ge'),
    float: ('lt', 'gt', 'le', 'ge'),
}


class SchemaFactory:
    used_schema_names = defaultdict(int)
    config = type('Config', (), {'orm_mode': True})

    @classmethod
    def _register_schema_name(cls, schema_name):
        used_before = cls.used_schema_names.get(schema_name)
        if used_before is not None:
            schema_name = f'{schema_name}{used_before}'
        cls.used_schema_names[schema_name] += 1
        return schema_name

    @classmethod
    def input_schema(cls, model, base_schema, schema_name=None, **meta_kwargs):
        schema_name = schema_name or f'{model.__name__.title()}InputSchema'
        meta = create_meta_class(model, **meta_kwargs)
        return GinoModelMeta(schema_name, (base_schema,), {'Meta': meta})

    @classmethod
    def output_schema(cls, model, base_schema, schema_name=None, postfix='', **meta_kwargs):
        schema_name = schema_name or f'{model.__name__.title()}{postfix}OutputSchema'
        meta = create_meta_class(model, **meta_kwargs)
        config = type('Config', (), {'orm_mode': True})
        return GinoModelMeta(schema_name, (base_schema,), {'Meta': meta, 'Config': config})

    @classmethod
    def put_schema(cls, model, base_schema, schema_name=None):
        schema_name = schema_name or f'{model.__name__.title()}PutSchema'
        meta = create_meta_class(model=model, exclude=('id',))
        return GinoModelMeta(schema_name, (base_schema,), {'Meta': meta,},)

    @classmethod
    def patch_schema(cls, model, base_schema, schema_name=None):
        schema_name = schema_name or f'{model.__name__.title()}PatchSchema'
        meta = create_meta_class(model=model, required=(), exclude=('id',))
        return GinoModelMeta(schema_name, (base_schema,), {'Meta': meta,},)

    @classmethod
    def filter_schema(cls, model, schema_name: str):
        meta = create_meta_class(
            model=model,
            as_dataclass=True,
            list_pk=True,
            field_methods=True,
            required=()
        )
        return GinoModelMeta(schema_name, (), {'Meta': meta})

    @classmethod
    def list_schema(cls, base_schema, base_list_schema, schema_name=None):
        return ModelMetaclass(
            schema_name,
            (base_list_schema,),
            {'__annotations__': {'data': List[base_schema]}},
        )
