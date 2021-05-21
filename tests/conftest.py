import asyncio
from itertools import cycle

import pytest
from gino import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .factory import Factory
from .models import db, PG_URL, UserType


@pytest.fixture(scope="session")
async def engine():
    db_engine = await create_engine(PG_URL)
    db.bind = db_engine
    async with db_engine.acquire():
        # await db.status(db.text("DROP TYPE usertype CASCADE"))

        await db.status(db.text("DROP TABLE IF EXISTS users;"))
        await db.status(db.text("DROP TABLE IF EXISTS teams;"))
        await db.status(db.text("DROP TYPE IF EXISTS usertype;"))
        await db.status(db.text("CREATE TYPE  usertype AS ENUM ('USER', 'ADMIN');"))
        await db.gino.create_all()

        yield db_engine

        await db.status(db.text("DROP TYPE usertype CASCADE"))
        await db.status(db.text("DROP TABLE users"))
        await db.status(db.text("DROP TABLE teams"))

    await db_engine.close()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop


@pytest.fixture(scope='function', autouse=True)
async def clear_db(engine):
    yield
    await db.status(db.text("TRUNCATE users RESTART IDENTITY CASCADE"))
    await db.status(db.text("TRUNCATE users RESTART IDENTITY CASCADE"))


@pytest.fixture
async def create_users():
    team = await Factory.team()
    users = []
    types = cycle([UserType.ADMIN, UserType.USER])
    for n in range(1, 6):
        user = await Factory.user(
            team=team,
            age=n * 10,
            nickname=f'Alex{n}',
            email_list=[f'user{n}@gmail.com', f'user{n}@yahoo.com'],
            usertype=next(types),
        )
        users.append(user)
    return users


@pytest.fixture
async def get_users(create_users):
    def wrapped():
        return create_users
    return wrapped

