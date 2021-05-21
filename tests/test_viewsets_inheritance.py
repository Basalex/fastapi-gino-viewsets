from typing import Optional

from fastapi import FastAPI, Request
from pydantic.main import BaseModel
from starlette.testclient import TestClient

from fastapi_gino_viewsets import MainRouter, ViewSet, BaseModelSchema
from tests.models import User, UserType
from tests.utils import NoNoneDict

app = FastAPI()
router = MainRouter()

client = TestClient(app)
test_data = {
    'age': 18,
    'nickname': 'Admin',
    'realname': 'Alex',
    'required': 'req',
    'type': UserType.USER.value,
}


class UserSchema(BaseModelSchema):
    hello: Optional[str] = None

    class Meta:
        model = User


class UserCreateSchema(BaseModelSchema):
    class Meta:
        model = User
        exclude = ('id', )


class UserPutSchema(BaseModelSchema):
    class Meta:
        model = User


class UserUpdateSchema(BaseModelSchema):
    class Meta:
        model = User
        exclude = ('id', )
        required = ()


class UserOutputSchema(BaseModelSchema):
    data: UserSchema


class UserListSchema(BaseModel):
    data: Optional[UserSchema] = None


class BaseDeleteSchema(BaseModel):
    id: int


class UserDeleteSchema(BaseModel):
    data: BaseDeleteSchema


@router.add_view('/main')
class UserViewSet(ViewSet):
    model = User


@router.add_view('/second')
class InheritedUserReadOnlyView(UserViewSet):
    model = User
    create_schema = UserCreateSchema
    patch_schema = UserUpdateSchema
    put_schema = UserPutSchema
    list_schema = UserListSchema
    output_schema = UserOutputSchema
    delete_schema = UserDeleteSchema

    @classmethod
    async def retrieve(cls, request: Request, id: int):
        user = await super().retrieve(request=request, param=id)
        return {'data': user}

    @classmethod
    async def retrieve_list(cls):
        return {'data': None}

    @classmethod
    async def create(cls, request: Request):
        user = await super().create(
            request=cls.create_schema(
                **await request.json()
            ),
        )
        return {'data': user}

    @classmethod
    async def update_partial(cls, request: UserSchema, id: int):
        user = await super().update_partial(request=request, param=id)
        return {'data': user}

    @classmethod
    async def update(cls, request: UserCreateSchema, id: int):
        user = await super().update(request=request, param=id)
        return {'data': user}

    @classmethod
    async def delete(cls, id: int):
        user_id = await super().delete(param=id)
        return {'data': user_id}


def test_retrieve(engine, create_users):
    with client:
        result = client.get('/second/1').json()
        assert result['data']['id'] == 1


def test_retrieve_list(engine, create_users):
    with client:
        result = client.get('/second/1').json()
        assert result['data']['id'] == 1


def test_create(engine):
    with client:
        result = client.post('/second', json=test_data).json()
        assert result['data']['nickname'] == 'Admin'


def test_update_partial(engine, create_users):
    with client:
        partial_data = {
            'nickname': 'Vampire',
            'realname': 'Petr',
            'age': 25,
            'type': 'ADMIN'
        }
        result = client.patch('/second/1', json=partial_data).json()
    data = result['data']
    data.pop('id')
    assert all(data[k] == partial_data[k] for k, v in partial_data.items())


def test_update(engine, create_users):
    data = {**test_data, 'id': 1}
    with client:
        result = client.put('/second/1', json=data).json()
    data = result['data']
    data.pop('id')
    assert NoNoneDict(data) == test_data


def test_delete(engine, create_users):
    with client:
        result = client.delete('/second/1').json()
        assert result['data']['id'] == 1


app.include_router(router)
