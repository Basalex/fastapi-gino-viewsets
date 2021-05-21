from datetime import datetime

import pytest
from pydantic import ValidationError

from fastapi_gino_viewsets import BaseModelSchema
from tests.models import User, UserType
from fastapi_gino_viewsets.schema_factory import SchemaFactory
from gino.json_support import DATETIME_FORMAT


now = datetime.utcnow()
now_str = now.strftime(DATETIME_FORMAT)

test_dict = {
        'id': 1,
        'realname': 'John',
        'birthday': now_str,
        'team_id': 4,
        'nickname': 'JonSnow',
        'type': UserType.USER,
        'required': 'test_string'
    }


def f(*args):
    return {arg: test_dict[arg] for arg in args}


def e(*args):
    return {k: v for k, v in test_dict.items() if k not in args}


@pytest.mark.parametrize('data, expected_dif', [
    (test_dict, {'birthday': now}),
    (f('id', 'required'), {}),
])
def test_input_schema_valid(data, expected_dif):
    UserInputSchema = SchemaFactory.input_schema(User, base_schema=BaseModelSchema)
    obj = UserInputSchema(**data)
    assert UserInputSchema.__name__ == 'UserInputSchema'
    expected = {**data, **expected_dif}
    assert obj.dict(exclude_unset=True) == expected


@pytest.mark.parametrize('data, expected_dif', [(f('realname'), None),])
def test_input_schema_not_valid(data, expected_dif):

    UserInputSchema = SchemaFactory.input_schema(User, base_schema=BaseModelSchema)
    with pytest.raises(ValidationError):
        UserInputSchema(**data)


@pytest.mark.parametrize('data, expected_dif', [
    (test_dict, {'birthday': now}),
    (f('id', 'required'), {}),
])
def test_output_schema_valid(data, expected_dif):
    UserOutputSchema = SchemaFactory.output_schema(User, base_schema=BaseModelSchema)
    obj = UserOutputSchema(**data)
    assert UserOutputSchema.__name__ == 'UserOutputSchema'
    expected = {**data, **expected_dif}
    assert obj.dict(exclude_unset=True) == expected


@pytest.mark.parametrize('data', [f('realname'), f('required'), f('id')])
def test_output_schema_not_valid(data):
    UserOutputSchema = SchemaFactory.output_schema(User, base_schema=BaseModelSchema)
    with pytest.raises(ValidationError):
        UserOutputSchema(**data)


@pytest.mark.parametrize('data, expected_dif', [
    (e('id'), {'birthday': now}),
    ({}, {}),
])
def test_patch_schema_valid(data, expected_dif):
    UserPatchSchema = SchemaFactory.patch_schema(User, base_schema=BaseModelSchema)
    obj = UserPatchSchema(**data)
    assert UserPatchSchema.__name__ == 'UserPatchSchema'
    expected = {**data, **expected_dif}
    assert obj.dict(exclude_unset=True) == expected
