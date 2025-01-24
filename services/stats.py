from utils.request import make_request


def finish_match_stat(data=None):
    if data is None:
        data = {}
    return make_request(
        endpoint='private/users/result-match/',
        port=8005,
        method='POST',
        data=data,
    )


def finish_tournament_stat(user=None, data=None):
    if data is None:
        data = {'winner': user['id']}
    return make_request(
        endpoint='private/users/result-tournament/',
        port=8005,
        method='POST',
        data=data,
    )


def get_stats(user):
    return make_request(
        endpoint='users/me/stats/',
        token=user['token'],
    )


def get_ranked_stats(user):
    return make_request(
        endpoint='users/me/stats/ranked/',
        token=user['token'],
    )


def set_trophies(user, trophies):
    data = {
        'id': 3,
        'game_mode': 'ranked',
        'created_at': '2025-01-09T02:39:48.794986+01:00',
        'game_duration': '00:00:05.206017',
        'teams':
            {
                'a': {'players': [{'id': user['id'], 'trophies': trophies, 'score': 3}], 'score': 3},
                'b': {'players': [{'id': 732, 'trophies': 0, 'score': 0}], 'score': 0},
            },
        'winner': 'a',
        'looser': 'b',
    }
    return make_request(
        endpoint='private/users/result-match/',
        port=8005,
        method='POST',
        data=data,
    )
