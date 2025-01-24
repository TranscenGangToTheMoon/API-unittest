from typing import Literal

from utils.request import make_request


def get_user(user, user2_id):
    return make_request(
        endpoint=f'users/{user2_id}/',
        token=user['token'],
    )


def me(user, method: Literal['GET', 'DELETE', 'PATCH'] = 'GET', data=None, password=False):
    if method in ('PATCH', 'DELETE') and password:
        data = {'password': user['password']}
    elif data is None:
        data = {}
    return make_request(
        endpoint=f'users/me/',
        token=user['token'],
        method=method,
        data=data,
    )


def get_data(user):
    return make_request(
        endpoint=f'users/me/download-data/',
        token=user['token'],
    )


def get_chat_data(user):
    return make_request(
        endpoint=f'private/export-data/{user["id"]}/',
        port=8002,
    )


def get_game_data(user):
    return make_request(
        endpoint=f'private/export-data/{user["id"]}/',
        port=8003,
    )
