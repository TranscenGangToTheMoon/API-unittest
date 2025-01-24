from typing import Literal

from utils.request import make_request


def play(user, game_mode: Literal['ranked', 'duel'] = 'duel', method: Literal['POST', 'DELETE'] = 'POST'):
    return make_request(
        endpoint=f'play/{game_mode}/',
        method=method,
        token=user['token'],
    )
