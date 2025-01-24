from typing import Literal

from utils.request import make_request


def accept_chat(user, accept_chat_from: Literal['everyone', 'friend_only', 'none'] = 'everyone'):
    return make_request(
        endpoint='users/me/',
        method='PATCH',
        token=user['token'],
        data={'accept_chat_from': accept_chat_from}
    )


def create_chat(user1, username=None, data=None, method: Literal['GET', 'POST'] = 'POST', query=None):
    if data is None and method == 'POST':
        data = {'username': username}
    endpoint = 'chat/'
    if query is not None:
        endpoint += f'?q={query}'
    return make_request(
        endpoint=endpoint,
        method=method,
        token=user1['token'],
        data=data,
    )


def request_chat_id(user1, chat_id, method: Literal['GET', 'DELETE'] = 'GET'):
    return make_request(
        endpoint=f'chat/{chat_id}/',
        method=method,
        token=user1['token'],
    )


def create_message(user, chat_id, message=None, data=None, method: Literal['GET', 'POST'] = 'POST'):
    if data is None and method == 'POST':
        data = {'content': message}

    kwargs = {'endpoint': f'private/chat/{chat_id}/messages/', 'method': method, 'token': user['token'], 'data': data, 'port': 8002}
    if method == 'GET':
        kwargs.pop('data')
        kwargs.pop('port')
        kwargs['endpoint'] = f'chat/{chat_id}/messages/'

    return make_request(**kwargs)
