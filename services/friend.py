from typing import Literal

from utils.request import make_request


def friend_requests(sender, receiver=None, method: Literal['POST', 'GET'] = 'POST', data=None):
    if method == 'POST':
        if data is None:
            data = {'username': receiver['username']}
    else:
        data = {}
    return make_request(
        endpoint='users/me/friend_requests/',
        method=method,
        token=sender['token'],
        data=data,
    )


def get_friend_requests_received(user):
    return make_request(
        endpoint='users/me/friend_requests/received/',
        token=user['token'],
    )


def get_friends(user, online=None):
    return make_request(
        endpoint='users/me/friends/' + ('' if online is None else f'?online={online}'),
        token=user['token'],
    )


def friend(user, friendship_id, method: Literal['GET', 'DELETE'] = 'GET'):
    return make_request(
        endpoint=f'users/me/friends/{friendship_id}/',
        method=method,
        token=user['token'],
    )


def friend_request(friend_request_id, user, method: Literal['POST', 'GET', 'DELETE'] = 'POST'):
    return make_request(
        endpoint=f'users/me/friend_requests/{friend_request_id}/',
        method=method,
        token=user['token'],
    )


def create_friendship(user1, user2):
    response_request = friend_requests(user1, user2)
    response_accept = friend_request(response_request.json['id'], user2)
    return [response_request, response_accept]
