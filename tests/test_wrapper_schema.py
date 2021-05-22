from functools import wraps

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from fastapi_gino_viewsets.schemas import BaseWrapperSchema
from fastapi_gino_viewsets.mixins import (
    AggregateObjectMixin,
    CreateModelMixin,
    DeleteModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    UpdatePartialModelMixin,
    RetrieveModelMixin,
)
from fastapi_gino_viewsets.router import MainRouter
from tests.models import User, UserType, db
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


class TestWrapperSchema(BaseWrapperSchema):
    __wrapper_key__ = 'data'


@router.add_view('/get', response_class=JSONResponse)
class UserRetrieveView(RetrieveModelMixin):
    model = User
    wrapper_schema = TestWrapperSchema


@router.add_view('/create', response_class=JSONResponse)
class UserCreateView(CreateModelMixin):
    model = User
    wrapper_schema = TestWrapperSchema


@router.add_view('/update_partial', response_class=JSONResponse)
class UserUpdatePartialView(UpdatePartialModelMixin):
    model = User
    wrapper_schema = TestWrapperSchema


@router.add_view('/update', response_class=JSONResponse)
class UserUpdateView(UpdateModelMixin):
    model = User
    wrapper_schema = TestWrapperSchema


@router.add_view('/delete', response_class=JSONResponse)
class UserDeleteView(DeleteModelMixin):
    model = User
    wrapper_schema = TestWrapperSchema


app.include_router(router)


def test_retrieve_with_wrapper_schema(engine, create_users):
    with client:
        response = client.get('/get/1').json()
        assert response['data']['nickname'] == 'Alex1'
        assert response['data']['age'] == 10


def test_delete_mixin(engine, create_users):
    user = create_users[0]
    with client:
        response = client.delete(f'/delete/{user.id}').json()
        assert response['data']['id'] == user.id


def test_create_mixin(engine):
    with client:
        data = client.post('/create', json=test_data).json()['data']
    data.pop('id')
    assert NoNoneDict(data) == test_data


def test_update_mixin(engine, create_users):
    with client:
        data = client.put('/update/1', json=test_data).json()['data']
    data.pop('id')
    assert NoNoneDict(data) == test_data


def test_update_partial_mixin(engine, create_users):
    partial_data = {
        'nickname': 'Vampire',
        'realname': 'Petr',
        'age': 25,
        'type': 'ADMIN'
    }
    with client:
        data = client.patch('/update_partial/1', json=partial_data).json()['data']
    data.pop('id')
    assert {data[k] == partial_data[k] for k, v in partial_data.items()}
