import random
import string
from collections import UserDict


def _random_name(length=8):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


class NoNoneDict(UserDict):

    def __setitem__(self, key, value):
        if value is not None:
            self.data[key] = value
