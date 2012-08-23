from __future__ import unicode_literals, print_function, division
from .case import test_hook
from .case import get_executing_test

test_datas = {}

@test_hook
def reset_test_datas():
    get_executing_test().addCleanup(test_datas.clear)


def test_data(func):
    def wrapper():
        test_data_name = func.__name__
        if test_data_name not in test_datas:
            test_datas[test_data_name] = func()
        return test_datas[test_data_name]

    return wrapper