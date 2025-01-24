from typing import Literal

from utils.request import make_request


def create_game(user1=None, user2=None, game_mode: Literal['ranked', 'duel'] = 'duel', data=None, method: Literal['GET', 'POST', 'PATCH', 'DELETE'] = 'POST'):
    if data is None:
        data = {'game_mode': game_mode, 'teams': {'a': [user1['id']], 'b': [user2['id']]}}
    return make_request(
        endpoint='private/match/create/',
        method=method,
        data=data,
        port=8003,
    )


def is_in_game(user1, match_id=None):
    if match_id is not None:
        return make_request(
            endpoint=f'private/match/{match_id}/{user1["id"]}/',
            port=8003,
        )
    return make_request(
        endpoint=f'private/match/{user1["id"]}/',
        port=8003,
    )


def score(user_id, own_goal=None):
    data = {}
    if own_goal is not None:
        data['own_goal'] = own_goal
    return make_request(
        endpoint=f'private/match/score/{user_id}/',
        method='PUT',
        port=8003,
        data=data,
    )


def finish_match(match_id, finish_reason=None, user_id=None, data=None):
    if data is None:
        data = {}
    if finish_reason is not None:
        data['finish_reason'] = finish_reason
    if user_id is not None:
        data['user_id'] = user_id
    return make_request(
        endpoint=f'private/match/finish/{match_id}/',
        method='PATCH',
        data=data,
        port=8003,
    )


def get_tournament(tournament_id, user):
    return make_request(
        endpoint=f'game/tournaments/{tournament_id}/',
        token=user['token'],
    )


def get_games(user):
    return make_request(
        endpoint=f'game/matches/{user["id"]}/',
        token=user['token'],
    )
