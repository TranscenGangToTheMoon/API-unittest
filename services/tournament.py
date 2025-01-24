from typing import Literal

from utils.generate_random import rnstr
from utils.request import make_request

tj = 'tournament-join'
tsa = 'tournament-start-at'
ts = 'tournament-start'
gs = 'game-start'
tmf = 'tournament-match-finish'
tf = 'tournament-finish'


def create_tournament(user, data=None, method: Literal['GET', 'POST', 'PATCH', 'DELETE'] = 'POST', private=None, size=4):
    if data is None:
        data = {'name': 'Tournoi ' + rnstr(), 'size': size}
    if private is not None:
        data['private'] = private
    return make_request(
        endpoint='play/tournament/',
        method=method,
        token=user['token'],
        data=data,
    )


def join_tournament(user, code, method: Literal['GET', 'POST', 'PATCH', 'DELETE'] = 'POST', data=None):
    if data is None:
        data = {}
    else:
        method = 'PATCH'
    return make_request(
        endpoint=f'play/tournament/{code}/',
        method=method,
        token=user['token'],
        data=data,
    )


def search_tournament(user, query):
    return make_request(
        endpoint=f'play/tournament/search/?q={query}',
        token=user['token'],
    )


def ban_user(user, user_ban, code):
    return make_request(
        endpoint=f'play/tournament/{code}/ban/{user_ban["id"]}/',
        token=user['token'],
        method='DELETE',
    )


def invite_user(user, user_invite, code):
    return make_request(
        endpoint=f'play/tournament/{code}/invite/{user_invite["id"]}/',
        token=user['token'],
        method='POST',
    )


def post_message(user, code, message=None, data=None):
    if data is None:
        data = {}
    if message is not None:
        data['content'] = message
    return make_request(
        endpoint=f'play/tournament/{code}/message/',
        token=user['token'],
        method='POST',
        data=data,
    )
