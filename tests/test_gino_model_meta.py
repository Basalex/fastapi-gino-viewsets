import pytest

from fastapi_gino_viewsets.base_schemas import BaseModelSchema
from fastapi_gino_viewsets.utils import create_meta_class
from fastapi_gino_viewsets.gino_model_meta import GinoModelMeta
from tests.models import User


@pytest.mark.parametrize('required, expected', [
    ((), ()),
    (None, ('id', 'required')),
    (('nickname', 'realname', 'required'), ('nickname', 'realname', 'required')),
])
def test_required_fields(required, expected):
    meta = create_meta_class(model=User, required=required)
    schema = GinoModelMeta('UserSchema', (BaseModelSchema,), {'Meta': meta, })
    assert all(schema.__fields__[field_name].required for field_name in expected)


@pytest.mark.parametrize('exclude', [
    (),
    ('id', 'required'),
    ('name', 'realname', 'required'),
])
def test_excluded_fields(exclude):
    meta = create_meta_class(model=User, exclude=exclude)
    schema = GinoModelMeta('UserSchema', (BaseModelSchema,), {'Meta': meta, })
    assert not any(schema.__fields__.get(field_name) for field_name in exclude)


@pytest.mark.parametrize('use_db_names', [True, False])
def test_excluded_fields(use_db_names):
    meta = create_meta_class(model=User, use_db_names=use_db_names)
    schema = GinoModelMeta('UserSchema', (BaseModelSchema,), {'Meta': meta, })
    assert schema.__fields__['name'] if use_db_names else schema.__fields__['nickname']
