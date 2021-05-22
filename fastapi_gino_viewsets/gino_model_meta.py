from typing import List, Optional, no_type_check

from fastapi import Query
from pydantic import create_model
from pydantic.main import ModelMetaclass
from sqlalchemy import Column

from .utils import get_model_fields, make_pydantic_dataclass

FIELD_METHODS_BY_TYPE = {
    int: ('le', 'ge'),
    float: ('le', 'ge'),
}

DefaultValue = object()


class MetaWrapper:
    '''
        class Meta params:
            @param: model -> required, must set to generate schema for given db model
            @param: required -> if set, only listed fields will be considered as required ones
            @param: fields -> only listed fields will be used for producing schema
            @param: exclude -> listed fields will be excluded from producing schema
            @param: use_db_names -> if True, database field names will be used instead of model field names
            @list_pk: creates List[field_type] fields for primary and foreign keys fields
            @as_dataclass: produces pydantic dataclass instead of BaseModel descendant
            @param: field_methods, field_methods_by_name ->
                field_methods if set to True, default mapping will be used
                @example:
                class Meta:
                    field_methods = {int: ('lt', 'gt)}
                    field_methods_by_name = {'field_name': ('le', 'ge')}
                following schema fields will be produced:
                class Schema:
                    integer_field_name__lt
                    integer_field_name__gt
                    field_name__lte
                    field_name__gte
    '''

    __slots__ = (
        'model',
        'required',
        'fields',
        'exclude',
        'use_db_names',
        'list_pk',
        'as_dataclass',
        'as_list_fields',
        'field_methods',
        'field_methods_by_name',
    )

    def __init__(self, meta):
        self.model = meta.model
        self.required = getattr(meta, 'required', None)
        self.fields = getattr(meta, 'fields', None)
        self.exclude = getattr(meta, 'exclude', None)
        self.use_db_names = getattr(meta, 'use_db_names', None)
        self.field_methods = getattr(meta, 'field_methods', {})
        if self.field_methods is True:
            self.field_methods = FIELD_METHODS_BY_TYPE
        self.field_methods_by_name = getattr(meta, 'field_methods_by_name', None)
        self.list_pk = getattr(meta, 'list_pk', False)
        self.as_list_fields = getattr(meta, 'as_list_fields', None)
        self.as_dataclass = getattr(meta, 'as_dataclass', False)

    def is_excluded(self, field_name):
        if self.fields:
            if isinstance(self.fields, str):
                raise ValueError('Meta class `fields` attribute should not be a string!')
            return field_name not in self.fields
        if self.exclude:
            return field_name in self.exclude
        return False

    def get_methods(self, field_name, field_type):
        if self.field_methods_by_name is not None:
            methods = self.field_methods_by_name.get(field_name)
        else:
            methods = self.field_methods.get(field_type)
        return methods


class FieldWrapper:
    __slots__ = ('field', '_is_required', 'field_name')

    def __init__(
        self, field, field_name: str, is_required: Optional[bool] = None,
    ):
        self.field = field
        self._is_required = is_required
        self.field_name = field_name

    @property
    def is_required(self) -> bool:
        if self._is_required is not None:
            return self._is_required
        if isinstance(self.field, Column):
            return not (
                self.field.nullable or self.field.server_default or self.field.default
            )
        return False

    @property
    def type(self):
        try:
            field_type = self.field.type.python_type
        except NotImplementedError:
            field_type = str
        return field_type

    @property
    def is_primary_or_fk(self):
        return self.field.primary_key or self.field.foreign_keys


class GinoModelMeta(ModelMetaclass):
    @no_type_check
    def __new__(mcs, name, bases, attrs):
        meta = attrs.pop('Meta', None)  # None for abstract schemas
        if meta:
            try:
                model = getattr(meta, 'model')
            except AttributeError:
                raise NotImplementedError(
                    'Attribute `model` of class Meta is required!'
                ) from None

            meta = MetaWrapper(meta)
            types = {}
            for field_name, (field, python_type) in get_model_fields(model).items():
                if meta.use_db_names and isinstance(field, Column):
                    field_name = str(field.name)
                if meta.is_excluded(field_name):
                    continue

                is_required = (
                    None if meta.required is None else field_name in meta.required
                )
                field = FieldWrapper(field, field_name, is_required=is_required)

                required = ... if field.is_required else None
                if python_type is list:
                    types[field_name] = (List[str], Query(None))
                elif (
                        meta.list_pk and field.is_primary_or_fk
                        or meta.as_list_fields and field_name in meta.as_list_fields
                        or python_type is list
                ):
                    types[field_name] = (List[python_type], Query(None))
                else:
                    methods = meta.get_methods(field_name, python_type)
                    if methods is not None:
                        for method in methods:
                            f_field_name = f'{field_name}__{method}'
                            types[f_field_name] = (python_type, required)
                    else:
                        types[field_name] = (python_type, required)

            if meta.as_dataclass:
                fields = []
                for field_name, (type_, default) in types.items():
                    field = (field_name, type_) if default is ... else (field_name, type_, default)
                    fields.append(field)

                for field_name, field_type in attrs.get('__annotations__', {}).items():
                    attrs = getattr(field_type, '__args__', None)
                    if attrs is not None and type(None) in attrs:
                        fields.append((field_name, attrs[0], None))
                    else:
                        fields.append((field_name, field_type))

                fields.sort(key=lambda f: len(f))
                return make_pydantic_dataclass(name, fields=fields)

            for field_name, field_type in attrs.get('__annotations__', {}).items():
                if field_name in attrs:
                    types[field_name] = (field_type, attrs[field_name])
                else:
                    types[field_name] = (field_type, ...)

            return create_model(
                name,
                __base__=super().__new__(mcs, name, bases, attrs),
                __module__=attrs.get('__module__'),
                **types
            )
        return super().__new__(mcs, name, bases, attrs)
