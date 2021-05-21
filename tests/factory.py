import random
from typing import Optional, List

from tests.models import Team, User, UserType
from tests.utils import _random_name


class Factory:

    @classmethod
    async def team(cls):
        return await Team.create()

    @classmethod
    async def user(
            cls,
            team: Optional[Team] = None,
            required: Optional[str] = None,
            nickname: Optional[str] = None,
            usertype: Optional[UserType] = None,
            realname: Optional[str] = None,
            age: Optional[int] = None,
            birthday: Optional[str] = None,
            email_list: Optional[List] = None

    ):

        return await User.create(
            team_id=(team or await cls.team()).id,
            required=required or _random_name(),
            nickname=nickname or _random_name(),
            type=usertype or random.choice([UserType.ADMIN, UserType.USER]),
            realname=realname or _random_name(),
            age=age or random.randint(1, 100),
            birthday=birthday,
            email_list=email_list,
        )
