import time
import unittest

from services.game import create_game, score
from services.play import play
from services.stats import finish_match_stat, get_stats, get_ranked_stats, set_trophies, finish_tournament_stat
from services.tournament import join_tournament, create_tournament
from services.user import me
from utils.config import MAX_SCORE
from utils.my_unittest import UnitTest
from utils.sse_event import gs, tj, ts, tmf, tf, ppu

validata_data = {
    'id': 3,
    'game_mode': 'duel',
    'created_at': '2025-01-09T02:39:48.794986+01:00',
    'game_duration': '00:00:05.206017',
    'tournament_id': 1,
    'tournament_stage_id': 2,
    'tournament_n': 3,
    'teams':
        {
            'a': {'score': 3, 'players': [{'id': 6, 'username': 'user-UVGIYopESD', 'is_guest': False, 'profile_picture': None, 'status': {'is_online': True, 'game_playing': None, 'last_online': '2025-01-09T01:39:38.791177Z'}, 'trophies': 0, 'score': 0}]},
            'b': {'score': 3, 'players': [{'id': 5, 'username': 'user-EXVoWJcIWJ', 'is_guest': False, 'profile_picture': None, 'status': {'is_online': True, 'game_playing': None, 'last_online': '2025-01-09T01:39:37.690417Z'}, 'trophies': 0, 'score': 3}]},
        },
    'winner': 'b',
    'looser': 'a',
    'score_winner': 3,
    'score_looser': 0
}


class Test01_FinishMatch(UnitTest):

    def test_001_finish_match(self):
        self.assertResponse(finish_match_stat(validata_data), 201)

    def test_002_validation_error(self):
        self.assertResponse(finish_match_stat(), 400)
        self.assertResponse(finish_match_stat({**validata_data, 'game_mode': 'caca'}), 400)
        self.assertResponse(finish_match_stat({**validata_data, 'teams': 'caca'}), 400)
        self.assertResponse(finish_match_stat({**validata_data, 'teams': {'1': [], '2': []}}), 400)
        self.assertResponse(finish_match_stat({**validata_data, 'teams': {'a': [{'id': 6, 'score': 0}], 'b': [{'id': 5}]}}), 400)


class Test02_Stats(UnitTest):

    def test_001_stats(self):
        user1 = self.user()

        response = self.assertResponse(get_stats(user1), 200)
        self.assertEqual(response[0]['wins'], 0)
        data = validata_data
        data['teams']['b']['players'][0]['id'] = user1['id']
        self.assertResponse(finish_match_stat(data), 201)
        response = self.assertResponse(get_stats(user1), 200)
        self.assertEqual(response[0]['wins'], 1)
        self.assertThread(user1)

    def test_002_ended_from_game(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        response = self.assertResponse(get_stats(user1), 200)
        for game_mode in response:
            if game_mode['game_mode'] == 'tournament':
                self.assertEqual(game_mode['tournament_wins'], 0)
                break

        self.assertResponse(create_game(user1, user2), 201)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        time.sleep(1)

        response = self.assertResponse(get_stats(user1), 200)
        for game_mode in response:
            if game_mode['game_mode'] == 'duel':
                self.assertEqual(game_mode['wins'], 1)
                break

        self.assertThread(user1, user2)

    def test_003_win_tournament_from_endpoint(self):
        user1 = self.user([ppu])

        self.assertResponse(finish_tournament_stat(user1), 201)
        response = self.assertResponse(get_stats(user1), 200)
        for game_mode in response:
            if game_mode['game_mode'] == 'tournament':
                self.assertEqual(game_mode['tournament_wins'], 1)
                break
        self.assertThread(user1)

    def test_004_win_tournament(self):
        user1 = self.user([tj, tj, tj, ts, gs, tmf, tmf, gs, tmf, tf, ppu])
        user2 = self.user([tj, tj, ts, gs, tmf, tmf, gs, tmf, tf])
        user3 = self.user([tj, ts, gs, tmf, tmf, tmf, tf])
        user4 = self.user([ts, gs, tmf, tmf, tmf, tf])

        self.assertResponse(set_trophies(user1, 10), 201)
        self.assertResponse(set_trophies(user2, 7), 201)
        self.assertResponse(set_trophies(user3, 4), 201)

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)

        time.sleep(5)

        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)

        time.sleep(5)

        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        time.sleep(5)
        response = self.assertResponse(get_stats(user1), 200)
        for game_mode in response:
            if game_mode['game_mode'] == 'tournament':
                self.assertEqual(game_mode['tournament_wins'], 1)
                break
        self.assertThread(user1, user2, user3, user4)

    def test_005_finish_tournament_error(self):
        self.assertResponse(finish_tournament_stat({'id': 123456}), 404)
        self.assertResponse(finish_tournament_stat(data={'looser': 2}), 400)


class Test03_StatsRanked(UnitTest):

    def test_001_ranked_stats(self):
        user1 = self.user()

        self.assertResponse(get_ranked_stats(user1), 200, count=1)
        data = validata_data
        data['teams']['b']['players'][0]['id'] = user1['id']
        data['teams']['b']['players'][0]['trophies'] = 30
        data['game_mode'] = 'ranked'
        self.assertResponse(finish_match_stat(data), 201)
        data['teams']['b']['players'][0]['trophies'] = 28
        self.assertResponse(finish_match_stat(data), 201)
        response = self.assertResponse(get_ranked_stats(user1), 200, count=3)
        self.assertEqual(response['results'][-1]['total_trophies'], 58)
        self.assertThread(user1)

    def test_002_trophies_test(self):
        user1 = self.user([gs, gs, gs])
        user2 = self.user([gs, gs, gs, gs])
        user3 = self.user([gs])

        self.assertResponse(play(user1, 'ranked'), 201)
        self.assertResponse(play(user2, 'ranked'), 201)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        self.assertResponse(play(user1, 'ranked'), 201)
        self.assertResponse(play(user2, 'ranked'), 201)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        self.assertEqual(68, self.assertResponse(me(user1), 200, get_field='trophies'))
        self.assertEqual(0, self.assertResponse(me(user2), 200, get_field='trophies'))

        self.assertResponse(play(user2, 'ranked'), 201)
        self.assertResponse(play(user3, 'ranked'), 201)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)
        self.assertEqual(36, self.assertResponse(me(user2), 200, get_field='trophies'))

        self.assertResponse(play(user1, 'ranked'), 201)
        self.assertResponse(play(user2, 'ranked'), 201)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)
        self.assertEqual(47, self.assertResponse(me(user1), 200, get_field='trophies'))
        self.assertEqual(75, self.assertResponse(me(user2), 200, get_field='trophies'))

        self.assertThread(user1, user2, user3)


if __name__ == '__main__':
    unittest.main()
