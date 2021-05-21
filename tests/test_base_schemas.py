from dataclasses import fields
from datetime import datetime
from typing import List

import pytest
from pydantic import ValidationError, BaseModel

from fastapi_gino_viewsets import BaseModelSchema
from tests.models import User, UserType
from gino.json_support import DATETIME_FORMAT

from fastapi_gino_viewsets.utils import create_meta_class


now = datetime.utcnow()
now_str = now.strftime(DATETIME_FORMAT)

test_dict = {
        'id': 1,
        'realname': 'John',
        'birthday': now_str,
        'team_id': 4,
        'nickname': 'JonSnow',
        'type': UserType.USER,
        'required': 'test_string',
        'email_list': ['user@gmail.com', 'user@yahoo.com'],
    }


def f(*args):
    return {arg: test_dict[arg] for arg in args}


def e(*args):
    return {k: v for k, v in test_dict.items() if k not in args}


@pytest.mark.parametrize('meta_attrs, fields', [
    ({}, {'id', 'required', 'nickname', 'team_id', 'type', 'realname', 'age', 'birthday', 'email_list'}),
    ({'exclude': ('id', 'required')}, {'nickname', 'team_id', 'type', 'realname', 'age', 'birthday', 'email_list'}),
    ({'fields': ('id', 'required', 'realname')}, {'id', 'required', 'realname'}),
    ({'use_db_names': True, 'fields': ('name', )}, {'name'}),
    ({'field_methods': True, 'fields': ('age', )}, {'age__le', 'age__ge'}),
    (
            {
                'field_methods_by_name': {'id': ('le', 'ge', 'lt', 'gt')},
                'fields': ('id', )
            },
            {'id__le', 'id__ge', 'id__gt', 'id__lt'}
    ),
])
def test_base_model_schema(meta_attrs, fields):
    class UserSchema(BaseModelSchema):
        Meta = create_meta_class(model=User, **meta_attrs)
    assert not (UserSchema.__fields__.keys() - fields)


@pytest.mark.parametrize('required_fields', (
        (),
        ('age', 'nickname'),
        ('id', 'age'),
))
def test_base_model_required(required_fields):
    class UserSchema(BaseModelSchema):
        class Meta:
            model = User
            required = required_fields

    try:
        UserSchema()
    except ValidationError as e:
        assert required_fields
        errors = e.json()
        for field_name in required_fields:
            assert field_name in errors


def test_list_pk():
    class UserSchema(BaseModelSchema):
        class Meta:
            model = User
            list_pk = True
    u = UserSchema(id=[1, 2, 3], team_id=[2, 3], required='required', realname='John')
    data = u.dict()
    assert data["id"] == [1, 2, 3]
    assert data["team_id"] == [2, 3]


@pytest.mark.parametrize('user_id, team_id', (
        ('1', '2'),
        (1, [1, 2, 3]),
        ([1, 2, 3], '1'),
        (['1', '2', '3'], [1, 2, 3]),
        ([1, 2, 3], ['1', '2', '3']),
))
def test_list_pk_fail(user_id, team_id):
    class UserSchema(BaseModelSchema):
        class Meta:
            model = User
            list_pk = True
    u = UserSchema(id=[1, 2, 3], team_id=[2, 3], required='required', realname='John')
    with pytest.raises(ValidationError):
        UserSchema(id=user_id)


def test_as_list_fields():
    class UserSchema(BaseModelSchema):
        class Meta:
            model = User
            as_list_fields = ('age', 'name')
            use_db_names = True
    u = UserSchema(id=1, team_id=1, age=[20, 30], name=['Alex', 'John'], required='required')
    data = u.dict()
    assert data["age"] == [20, 30]
    assert data["name"] == ['Alex', 'John']


@pytest.mark.parametrize('age, name', (
        ('1', '2'),
        (1, [1, 2, 3]),
        ([1, 2, 3], '1'),
        (['a', 'b', 'c'], [1, 2, 3]),
))
def test_as_list_fields_fail(age, name):
    class UserSchema(BaseModelSchema):
        class Meta:
            model = User
            as_list_fields = ('age', 'name')
            use_db_names = True
    with pytest.raises(ValidationError):
        UserSchema(id=1, team_id=1, age=age, name=name, required='required')


def test_as_dataclass():
    class UserSchema(BaseModelSchema):
        class Meta:
            model = User
            as_dataclass = True
    assert fields(UserSchema)


def test_with_extra_fields():
    class Item(BaseModel):
        id: int

    class UserSchema(BaseModelSchema):
        amount: float
        items: List[Item]

        class Meta:
            model = User

    schema = UserSchema(
        age=18,
        amount=10,
        id=1,
        items=[{'id': 1}, {'id': 2}],
        team_id=1,
        required='required'
    )
    expected = dict(age=18, amount=10, id=1, items=[{'id': 1}, {'id': 2}], team_id=1, required='required')
    assert schema.dict(exclude_none=True) == expected
