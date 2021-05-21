from pydantic import BaseConfig as _BaseConfig


class BaseConfig(_BaseConfig):
    allow_population_by_field_name = True
    orm_mode = True
    arbitrary_types_allowed = True
