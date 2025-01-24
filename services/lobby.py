from typing import Literal

from utils.request import make_request


def create_lobby(user, data=None, method: Literal['GET', 'POST', 'PATCH', 'DELETE'] = 'POST', game_mode='clash'):
    if data is None:
        data = {'game_mode': game_mode}
    return make_request(
        endpoint='play/lobby/',
        method=method,
        token=user['token'],
        data=data,
    )


def join_lobby(user, code, method: Literal['GET', 'POST', 'PATCH', 'DELETE'] = 'POST', data=None):
    if data is None:
        data = {}
    else:
        method = 'PATCH'
    return make_request(
        endpoint=f'play/lobby/{code}/',
        method=method,
        token=user['token'],
        data=data,
    )


def ban_user(user, user_ban, code):
    return make_request(
        endpoint=f'play/lobby/{code}/ban/{user_ban["id"]}/',
        token=user['token'],
        method='DELETE',
    )


def invite_user(user, user_invite, code):
    return make_request(
        endpoint=f'play/lobby/{code}/invite/{user_invite["id"]}/',
        token=user['token'],
        method='POST',
    )


def post_message(user, code, message=None, data=None):
    if data is None:
        data = {}
    if message is not None:
        data['content'] = message
    return make_request(
        endpoint=f'play/lobby/{code}/message/',
        token=user['token'],
        method='POST',
        data=data,
    )
