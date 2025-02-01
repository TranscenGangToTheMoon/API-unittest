import random
import time
import unittest

from services.game import create_game, is_in_game, score, finish_match, get_tournament, get_games
from services.stats import set_trophies
from services.tournament import join_tournament, create_tournament
from utils.config import MAX_SCORE
from utils.my_unittest import UnitTest
from utils.sse_event import tj, ts, gs, tmf, tf, ppu


class Test01_Game(UnitTest):

    @staticmethod
    def ran():
        return random.randint(500, 1500)

    def test_001_create_game(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        self.assertResponse(create_game(user1, user2), 201)
        time.sleep(1)
        self.assertThread(user1, user2)

    def test_002_already_in_game(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        self.assertResponse(is_in_game(user1), 404)
        self.assertResponse(create_game(user1, user2), 201)
        self.assertResponse(is_in_game(user1), 200)
        self.assertThread(user1, user2)

    def test_003_invalid_game_mode(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(create_game(user1, user2, game_mode='caca'), 400)
        self.assertThread(user1, user2)

    def test_004_no_game_mode(self):
        self.assertResponse(create_game(data={'teams': {'a': [{'id': self.ran()}], 'b': [{'id': self.ran()}]}}), 400, {'game_mode': ['This field is required.']})

    def test_005_invalid_teams(self):
        n = self.ran()
        invalid_teams = [
            {'a': [], 'b': []},
            {'a': [self.ran()], 'b': []},
            {'a': [], 'b': [self.ran()]},
            {'a': 'coucou', 'b': ['hey']},
            {'a': [self.ran(), self.ran()], 'b': [self.ran()]},
            {'a': [n], 'b': [n]},
            {'a': [self.ran(), self.ran(), self.ran()], 'b': [self.ran(), self.ran(), self.ran()]},
            {'a': [self.ran()]},
            {'a': 'bonjour'},
            {'a': [self.ran(), self.ran(), self.ran()], 'b': 'bonjour'},
            {'a': [self.ran(), self.ran(), self.ran()], 'b': self.ran()},
        ]

        for invalid_team in invalid_teams:
            self.assertResponse(create_game(data={'game_mode': 'ranked', 'teams': invalid_team}), 400)

    def test_006_no_teams(self):
        self.assertResponse(create_game(data={'game_mode': 'ranked'}), 400, {'teams': ['This field is required.']})

    def test_007_game_timeout(self):
        user1 = self.user([gs], connect_game=False)
        user2 = self.user([gs], connect_game=False)

        self.assertResponse(create_game(user1, user2), 201)
        self.assertResponse(is_in_game(user1), 200)
        time.sleep(15)
        self.assertResponse(is_in_game(user1), 404)
        self.assertThread(user1, user2)

    def test_008_game_does_not_timeout(self):
        user1 = self.user([gs], connect_game=False)
        user2 = self.user([gs], connect_game=False)

        id = self.assertResponse(create_game(user1, user2), 201, get_field=True)
        self.assertResponse(is_in_game(user1, id), 200)
        time.sleep(15)
        self.assertResponse(is_in_game(user1), 200)
        self.assertThread(user1, user2)

    def test_009_get_games(self):
        n = random.randint(2, 9)
        user1 = self.user([gs] * n)
        users = [self.user([gs]) for _ in range(n)]

        for u in users:
            self.assertResponse(create_game(user1, u), 201)
            for _ in range(MAX_SCORE):
                self.assertResponse(score(user1['id']), 200)
            time.sleep(0.5)

        results = self.assertResponse(get_games(user1), 200, get_field='results', count=n)
        self.assertEqual(users[-1]['id'], results[0]['teams']['b']['players'][0]['id'])
        self.assertThread(user1, *users)


class Test02_Score(UnitTest):

    def test_001_score(self):
        user1 = self.user([gs])
        score_1 = random.randint(0, MAX_SCORE - 1)
        user2 = self.user([gs])
        score_2 = random.randint(0, MAX_SCORE - 1)

        game_id = self.assertResponse(create_game(user1, user2), 201, get_field=True)
        for _ in range(score_1):
            self.assertResponse(score(user1['id']), 200)
        for _ in range(score_2):
            self.assertResponse(score(user2['id']), 200)
        response = self.assertResponse(is_in_game(user1, game_id), 200)
        self.assertEqual(score_1, response['teams']['a']['players'][0]['score'])
        self.assertEqual(score_2, response['teams']['b']['players'][0]['score'])
        self.assertThread(user1, user2)

    def test_002_not_in_game(self):
        user1 = self.user()

        self.assertResponse(score(user1['id']), 404, {'detail': 'This user does not belong to any match.'})
        self.assertThread(user1)


class Test03_Finish(UnitTest):

    def test_001_finish_game(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        self.assertResponse(create_game(user1, user2), 201)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)
        self.assertResponse(is_in_game(user1), 404)
        self.assertResponse(is_in_game(user2), 404)
        self.assertThread(user1, user2)

    def test_002_finish_disconnect(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        match_id = self.assertResponse(create_game(user1, user2), 201, get_field=True)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user1['id']), 200)
        self.assertResponse(finish_match(match_id, 'player-disconnect', user2['id']), 200)
        self.assertThread(user1, user2)

    def test_003_finish_clash(self):
        user1 = self.user([gs])
        user2 = self.user([gs])
        user3 = self.user([gs])
        user4 = self.user([gs])
        user5 = self.user([gs])
        user6 = self.user([gs])

        self.assertResponse(create_game(data={'game_mode': 'clash', 'teams': {'a': [{'id': user1['id']}, {'id': user2['id']}, {'id': user3['id']}], 'b': [{'id': user4['id']}, {'id': user5['id']}, {'id': user6['id']}]}}), 201)
        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user2['id'], own_goal=True), 200)
        self.assertResponse(score(user3['id'], own_goal=True), 200)
        self.assertResponse(score(user3['id']), 200)
        for _ in range(MAX_SCORE - 2):
            self.assertResponse(score(user1['id'], own_goal=False), 200)

        for user in [user1, user2, user3, user4, user5, user6]:
            self.assertResponse(is_in_game(user), 404)

        self.assertThread(user1, user2, user3, user4, user5, user6)

    def test_004_finish_disconnect_winning(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        match_id = self.assertResponse(create_game(user1, user2), 201, get_field=True)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user2['id']), 200)
        self.assertResponse(finish_match(match_id, 'player-disconnect', user2['id']), 200)

        for u in (user1, user2):
            match = self.assertResponse(get_games(u), 200, get_field='results', count=1)[0]
            self.assertEqual(user1['id'], match['teams'][match['winner']]['players'][0]['id'])

        self.assertThread(user1, user2)

    def test_005_finish_disconnect_not_winning(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        match_id = self.assertResponse(create_game(user1, user2), 201, get_field=True)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user2['id']), 200)
        self.assertResponse(finish_match(match_id, 'player-disconnect', user1['id']), 200)

        for u in (user1, user2):
            match = self.assertResponse(get_games(u), 200, get_field='results', count=1)[0]
            self.assertEqual(user2['id'], match['teams'][match['winner']]['players'][0]['id'])

        self.assertThread(user1, user2)

    def test_005_finish_disconnect_not_score(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        match_id = self.assertResponse(create_game(user1, user2), 201, get_field=True)
        self.assertResponse(finish_match(match_id, 'player-disconnect', user1['id']), 200)

        for u in (user1, user2):
            match = self.assertResponse(get_games(u), 200, get_field='results', count=1)[0]
            self.assertEqual(user2['id'], match['teams'][match['winner']]['players'][0]['id'])

        self.assertThread(user1, user2)

    def test_006_finish_disconnect_not_score(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        match_id = self.assertResponse(create_game(user1, user2), 201, get_field=True)
        self.assertResponse(finish_match(match_id, 'player-disconnect', user2['id']), 200)

        for u in (user1, user2):
            match = self.assertResponse(get_games(u), 200, get_field='results', count=1)[0]
            self.assertEqual(user1['id'], match['teams'][match['winner']]['players'][0]['id'])

        self.assertThread(user1, user2)


class Test04_Tournament(UnitTest):

    def test_001_tournament(self):
        user1 = self.user([tj, tj, tj, ts, gs, tmf, tmf, gs, tmf, tf, ppu])
        user2 = self.user([tj, tj, ts, gs, tmf, tmf, gs, tmf, tf])
        user3 = self.user([tj, ts, gs, tmf, tmf, tmf, tf])
        user4 = self.user([ts, gs, tmf, tmf, tmf, tf])

        self.assertResponse(set_trophies(user1, 30), 201)
        self.assertResponse(set_trophies(user2, 20), 201)
        self.assertResponse(set_trophies(user3, 10), 201)

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

        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user2['id']), 200)
        self.assertResponse(score(user2['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user1['id']), 200)

        time.sleep(5)

        response = self.assertResponse(get_games(user1), 200, count=2)
        self.assertResponse(get_tournament(response['results'][0]['tournament_id'], user1), 200)
        self.assertThread(user1, user2, user3, user4)

    def test_002_tournament_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(get_tournament(123456, user1), 404)
        self.assertThread(user1)


if __name__ == '__main__':
    unittest.main()
