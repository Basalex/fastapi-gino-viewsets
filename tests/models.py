import enum
import os
from datetime import datetime

import sqlalchemy as sa
from gino.ext.starlette import Gino
from sqlalchemy.dialects.postgresql import JSONB

from tests.utils import _random_name

DB_ARGS = dict(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', 5433),
    username=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASS', 'postgres'),
    database=os.getenv('DB_NAME', 'postgres'),
)
PG_URL = 'postgresql://{username}:{password}@{host}:{port}/{database}'.format(**DB_ARGS)
db = Gino()


class UserType(enum.Enum):
    USER = 'USER'
    ADMIN = 'ADMIN'


class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.BigInteger(), primary_key=True)
    name = db.Column(db.String(), default=_random_name)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.BigInteger(), primary_key=True)
    required = db.Column(db.String(), nullable=False)
    nickname = db.Column('name', db.Unicode(), default=_random_name)
    team_id = db.Column(db.ForeignKey('teams.id'))

    profile = db.Column('props', JSONB(), nullable=False, server_default='{}')
    type = db.Column(sa.Enum(UserType), nullable=False, default=UserType.USER)

    realname = db.StringProperty()
    age = db.IntegerProperty(default=18)
    birthday = db.DateTimeProperty(default=lambda i: datetime.utcfromtimestamp(0))
    email_list = db.ArrayProperty()
