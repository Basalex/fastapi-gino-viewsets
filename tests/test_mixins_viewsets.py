import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from fastapi_gino_viewsets.base_schemas import BaseSchema
from fastapi_gino_viewsets.mixins import (
    AggregateObjectMixin,
    CreateModelMixin,
    DeleteModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    UpdatePartialModelMixin,
    RetrieveModelMixin,

)
from fastapi_gino_viewsets.viewsets import ReadOnlyViewSet, ViewSet
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


class AggOutputSchema(BaseSchema):
    sum: int
    id_sum: int


@router.add_view('/aggregate', response_class=JSONResponse)
class UserAggregationView(AggregateObjectMixin):
    output_schema = AggOutputSchema

    def get_query(cls, request, f=None):
        return db.select([
            db.func.sum(User.id).label('id_sum'),
            db.func.sum(User.age).label('sum')
        ]).select_from(User)


@router.add_view('/get', response_class=JSONResponse)
class UserRetrieveView(RetrieveModelMixin):
    model = User


@router.add_view('/list', response_class=JSONResponse)
class UserListView(ListModelMixin):
    model = User


@router.add_view('/create', response_class=JSONResponse)
class UserCreateView(CreateModelMixin):
    model = User


@router.add_view('/update', response_class=JSONResponse)
class UserUpdateView(UpdateModelMixin):
    model = User


@router.add_view('/update_partial', response_class=JSONResponse)
class UserUpdatePartialView(UpdatePartialModelMixin):
    model = User


@router.add_view('/delete', response_class=JSONResponse)
class UserDeleteView(DeleteModelMixin):
    model = User


@router.add_view('/read_only', response_class=JSONResponse)
class UserReadOnlyView(ReadOnlyViewSet):
    model = User


@router.add_view('/viewset', response_class=JSONResponse)
class UserViewset(ViewSet):
    model = User


app.include_router(router)


def test_retrieve_mixin(engine, get_users):
    user = get_users()[0]
    with client:
        data = client.get(f'/get/{user.id}').json()
        assert data['id'] == user.id
        assert data['age'] == 10


def test_list_mixin(engine, get_users):
    users = get_users()
    with client:
        data = client.get('/list').json()
        assert [x['id'] for x in data['data']] == [u.id for u in users]
        assert data['pagination']['total'] == 5


@pytest.mark.parametrize('filters, expected_total', [
        ('?id=1&id=2', 2),
        ('?age__le=30', 3),
        ('?nickname=Alex2', 1),
        ('?ignore_me=true', 5),
        ('?email_list=user1@gmail.com&email_list=user1@yahoo.com', 1),
])
def test_list_mixin_filters(engine, create_users, filters, expected_total):
    with client:
        data = client.get('/list' + filters).json()
        assert data['pagination']['total'] == expected_total


@pytest.mark.parametrize('sort, expected_id_list', [
        ('?sort=-name', [5, 4, 3, 2, 1]),
        ('?sort=type&sort=-age', [4, 2, 5, 3, 1]),
        ('?sort=-age', [5, 4, 3, 2, 1]),
])
def test_sort(engine, create_users, sort, expected_id_list):
    with client:
        data = client.get('/list' + sort).json()
        assert [item["id"] for item in data["data"]] == expected_id_list


def test_aggregation_mixin(engine, create_users):
    with client:
        data = client.get('/aggregate').json()
        assert data['sum'] == 150
        assert data['id_sum'] == 15


def test_create_mixin(engine):
    with client:
        data = client.post('/create', json=test_data).json()
    data.pop('id')
    assert NoNoneDict(data) == test_data


def test_update_mixin(engine, create_users):
    with client:
        data = client.put('/update/1', json=test_data).json()
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
        data = client.patch('/update_partial/1', json=partial_data).json()
    data.pop('id')
    assert {data[k] == partial_data[k] for k, v in partial_data.items()}


def test_delete_mixin(engine, create_users):
    user = create_users[0]
    with client:
        data = client.delete(f'/delete/{user.id}').json()
        assert data['id'] == user.id
        data = client.delete(f'/delete/{user.id}')
        assert data.status_code == 404


def test_read_only_viewset(engine, get_users):
    users = get_users()
    with client:
        data = client.get('/read_only').json()
        assert [x['id'] for x in data['data']] == [u.id for u in users]
        assert data['pagination']['total'] == 5
        data = client.get(f'/read_only/{users[1].id}').json()
        assert data['id'] == users[1].id
        assert data['age'] == 20


def test_viewset(engine):
    with client:
        result = client.post('/viewset', json=test_data).json()
        result = client.get(f'/viewset/{result["id"]}').json()
        obj_id = result.pop('id')
        assert NoNoneDict(result) == test_data

        put_data = test_data.copy()
        put_data.update({
            'age': 21,
            'nickname': 'Flash',
            'realname': 'Vladimir',
            'type': 'ADMIN',
        })
        result = client.put(f'/viewset/{obj_id}', json=put_data).json()
        result.pop('id')
        assert NoNoneDict(result) == put_data

        patch_data = {'nickname': 'spiderman', 'realname': 'Peter Parker'}
        result = client.patch(f'/viewset/{obj_id}', json=patch_data).json()
        assert result['nickname'] == 'spiderman'
        assert result['realname'] == 'Peter Parker'

        data = client.delete(f'/viewset/{obj_id}').json()
        assert data['id'] == obj_id
        data = client.delete(f'/delete/{obj_id}')
        assert data.status_code == 404


GET, POST, PUT, PATCH, DELETE = client.get, client.post, client.put, client.patch, client.delete


@pytest.mark.parametrize('url, methods', [
    ('/get/1', {PUT, PATCH, DELETE}),
    ('/list', {POST}),
    ('/aggregate', {POST, PUT, PATCH, DELETE}),
    ('/create', {GET, PUT, PATCH, DELETE}),
    ('/update/1', {GET, POST, PATCH, DELETE}),
    ('/update_partial/1', {GET, POST, PUT, DELETE}),
    ('/delete/1', {GET, POST, PUT, PATCH}),
    ('/read_only', {POST}),
    ('/read_only/1', {PUT, PATCH, DELETE}),
])
def test_all_405(engine, create_users, url, methods):
    with client:
        for method in methods:
            result = method(url)
            assert result.status_code == 405


@pytest.mark.parametrize('url, methods', [
    ('/get', {GET, POST}),
    ('/list/1', {PUT, PATCH, DELETE}),
    ('/update', {GET, POST}),
    ('/update_partial', {GET, POST}),
    ('/delete', {GET, POST}),
])
def test_all_404(engine, create_users, url, methods):
    with client:
        for method in methods:
            result = method(url)
            assert result.status_code == 404
