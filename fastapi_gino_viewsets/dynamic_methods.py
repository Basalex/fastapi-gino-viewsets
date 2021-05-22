import asyncio
from functools import wraps
from typing import List, Optional

from fastapi import Depends, Path, Query, Request


def wrap_schema(fn, wrapped_key):
    @wraps(fn)
    async def wrapped(*args, **kwargs):
        response = await fn(*args, **kwargs)
        return {wrapped_key: response}

    return wrapped


class MethodFactory:

    @classmethod
    def make_create(cls, schema, wrapped_key: Optional[str] = None):
        async def create(cls, request: schema):
            entity = await cls.model.create(**request.dict())
            return entity
        if wrapped_key is not None:
            return wrap_schema(create, wrapped_key)
        return create

    @classmethod
    def make_update(cls, schema, key_name, key_type, wrapped_key: Optional[str] = None):
        async def update(
                cls,
                request: schema,
                param: key_type = Path(..., alias=key_name),
        ):
            field = getattr(cls.model, cls.key_name)
            entity = await cls.retrieve_function(cls.model, where=field == param)
            updated_fields = cls.get_put_schema().from_orm(request)
            await entity.update(**updated_fields.dict(exclude_unset=True)).apply()
            return entity
        if wrapped_key is not None:
            return wrap_schema(update, wrapped_key)
        return update

    @classmethod
    def make_update_partial(cls, schema, key_name, key_type, wrapped_key: Optional[str] = None):
        async def update_partial(
                cls,
                request: schema,
                param: key_type = Path(..., alias=key_name),
        ):
            field = getattr(cls.model, cls.key_name)
            entity = await cls.retrieve_function(cls.model, where=field == param)
            updated_fields = cls.get_patch_schema().from_orm(request)
            await entity.update(**updated_fields.dict(exclude_defaults=True)).apply()
            return entity
        if wrapped_key is not None:
            return wrap_schema(update_partial, wrapped_key)
        return update_partial

    @classmethod
    def make_delete(cls, key_name, key_type, wrapped_key: Optional[str] = None):
        async def delete(cls, param: key_type = Path(..., alias=key_name)):
            field = getattr(cls.model, cls.key_name)
            entity = await cls.retrieve_function(cls.model, where=field == param)
            key_value = getattr(entity, key_name)
            await entity.delete()
            return {key_name: key_value}
        if wrapped_key is not None:
            return wrap_schema(delete, wrapped_key)
        return delete

    @classmethod
    def make_retrieve(cls, key_name, key_type, wrapped_key: Optional[str] = None):
        async def retrieve(
                cls,
                request: Request,
                param: key_type = Path(..., alias=key_name),
        ):
            field = getattr(cls.model, cls.key_name)
            entity = await cls.retrieve_function(cls.model, where=field == param)
            return entity
        if wrapped_key is not None:
            return wrap_schema(retrieve, wrapped_key)
        return retrieve

    @classmethod
    def make_retrieve_list(cls, schema, wrapped_key: Optional[str] = None):
        async def retrieve_list(
            cls,
            request: Request,
            *,
            offset: int = 0,
            limit: int = 0,
            sort: List[str] = Query(None),
            filters: schema = Depends(schema),
        ):
            query = cls.get_query(request, filters)
            if asyncio.iscoroutine(query):
                query = await query
            if filters:
                query = cls.filter_query(request, query, filters)
            if sort is not None:
                query = cls.sort_query(request, query, sort)
            total = await cls.total(query)
            query = cls.paginate(query, offset, limit)
            data = list(await cls.prepare_data_hook(query))
            return cls.prepare_response(data, offset, limit, total)
        return retrieve_list

    @classmethod
    def make_retrieve_single_object_data(cls, schema):
        async def retrieve_single_object_data(cls, request: Request, filters: schema = Depends(schema)):
            query = cls.get_query(request, filters)
            if asyncio.iscoroutine(query):
                query = await query
            if filters:
                query = cls.filter_query(request, query, filters)
            data = await query.gino.first()
            return data
        return retrieve_single_object_data
