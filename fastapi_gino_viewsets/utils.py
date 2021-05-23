import re

from fastapi import HTTPException, status


def is_method_overloaded(cls, method_name) -> bool:
    method = getattr(cls, method_name, False)
    return method and method != getattr(super(cls, cls), method_name, None)


def camel_to_snake_case(words: str):
    return re.sub('([A-Z][a-z]+)', r'\1_', words).rstrip('_').lower()


def create_meta_class(model, **kwargs):
    return type("Meta", (), {"model": model, **kwargs})


async def get_object_or_404(model, *, where):
    obj = await model.query.where(where).gino.one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return obj
