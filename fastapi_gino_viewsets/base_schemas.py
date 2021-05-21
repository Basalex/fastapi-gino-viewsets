from typing import List, Any

from pydantic import BaseModel

from fastapi_gino_viewsets.base_config import BaseConfig
from fastapi_gino_viewsets.gino_model_meta import GinoModelMeta

__all__ = [
    'BaseDeleteSchema',
    'BaseFilterMeta',
    'BaseListSchema',
    'BaseModelSchema',
    'BasePaginatedListSchema',
    'BaseSchema',
    'BaseWrapperSchema',
]


class BaseListSchema(BaseModel):
    data: List[Any]

    class Config(BaseConfig):
        allow_population_by_field_name = True
        orm_mode = True
        arbitrary_types_allowed = True


class Pagination(BaseModel):
    offset: int
    limit: int
    total: int


class BasePaginatedListSchema(BaseListSchema):
    pagination: Pagination


class BaseSchema(BaseModel):
    class Config(BaseConfig):
        use_enum_values = True


class BaseModelSchema(BaseModel, metaclass=GinoModelMeta):
    class Config(BaseConfig):
        pass


class BaseWrapperSchema(BaseModel):
    __wrapper_key__: str = 'data'

    class Config:
        arbitrary_types_allowed = True


class BaseFilterMeta:
    as_dataclass = True
    list_pk = True,
    field_methods = True
    required = ()


class BaseDeleteSchema(BaseModel):
    id: int
