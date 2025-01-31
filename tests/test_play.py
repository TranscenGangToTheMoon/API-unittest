import time
import unittest

from services.blocked import blocked_user
from services.game import create_game, is_in_game
from services.lobby import create_lobby, join_lobby
from services.play import play
from services.stats import set_trophies
from services.tournament import join_tournament, create_tournament
from utils.my_unittest import UnitTest
from utils.sse_event import lj, lup, gs, ts, tj, ppu


class Test01_Play(UnitTest):

    def test_001_play_duel(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        self.assertResponse(play(user1), 201)
        self.assertResponse(play(user2), 201)
        time.sleep(1)
        self.assertThread(user1, user2)

    def test_002_play_ranked(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        self.assertResponse(play(user1, game_mode='ranked'), 201)
        self.assertResponse(play(user2, game_mode='ranked'), 201)
        time.sleep(1)
        self.assertThread(user1, user2)

    def test_003_play_clash(self):
        user1 = self.user([lj, lup, gs])
        user2 = self.user([lup, gs])
        user3 = self.user([gs])
        user4 = self.user([lj, lj, lup, lup, gs])
        user5 = self.user([lj, lup, lup, gs])
        user6 = self.user([lup, lup, gs])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user1, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user2, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user3), 201, get_field='code')
        self.assertResponse(join_lobby(user3, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user4), 201, get_field='code')
        self.assertResponse(join_lobby(user5, code), 201)
        self.assertResponse(join_lobby(user6, code), 201)
        self.assertResponse(join_lobby(user4, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user5, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user6, code, data={'is_ready': True}), 200)

        time.sleep(2)
        self.assertThread(user1, user2, user3, user4, user5, user6)

    def test_004_play_custom_game(self):
        user1 = self.user([lj, lj, lj, lj, lj, lup, lup, lup, lup, lup, gs])
        user2 = self.user([lj, lj, lj, lj, lup, lup, lup, lup, lup, gs])
        user3 = self.user([lj, lj, lj, lup, lup, lup, lup, lup, gs])
        user4 = self.user([lj, lj, lup, lup, lup, lup, lup, gs])
        user5 = self.user([lj, lup, lup, lup, lup, lup, gs])
        user6 = self.user([lup, lup, lup, lup, lup, gs])

        code = self.assertResponse(create_lobby(user1, data={'game_mode': 'custom_game', 'match_type': '3v3'}), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(join_lobby(user4, code), 201)
        self.assertResponse(join_lobby(user5, code), 201)
        self.assertResponse(join_lobby(user6, code), 201)

        self.assertResponse(join_lobby(user1, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user2, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user3, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user4, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user5, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user6, code, data={'is_ready': True}), 200)

        time.sleep(2)
        self.assertThread(user1, user2, user3, user4, user5, user6)

    def test_005_play_duel_guest(self):
        user1 = self.user([gs])
        user2 = self.user([gs], guest=True)

        self.assertResponse(play(user1), 201)
        self.assertResponse(play(user2), 201)
        time.sleep(1)
        self.assertThread(user1, user2)


class Test02_PlayError(UnitTest):

    def test_001_already_in_game(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        self.assertResponse(create_game(user1, user2), 201)
        self.assertResponse(play(user1), 409, {'detail': 'You are already in a game or a tournament.'})
        self.assertThread(user1, user2)

    def test_002_already_in_tournament(self):
        user1 = self.user([tj, tj, tj, ts])
        users = [self.user([tj] * (2 - i) + [ts]) for i in range(3)]

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        for user_tmp in users:
            self.assertResponse(join_tournament(user_tmp, code), 201)

        self.assertResponse(play(user1), 409, {'detail': 'You are already in a game or a tournament.'})
        self.assertThread(user1, *users)

    def test_003_guest_cannot_play_ranked(self):
        user1 = self.user(guest=True)

        self.assertResponse(play(user1, 'ranked'), 403, {'detail': 'Guest users cannot perform this action.'})
        self.assertThread(user1)

    def test_004_user_in_lobby(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        self.assertResponse(play(user2), 201)

        self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(play(user1), 201)
        self.assertResponse(create_lobby(user1, method='GET'), 404, {'detail': 'You do not belong to any lobby.'})
        self.assertThread(user1, user2)

    def test_005_user_in_tournament(self):
        user1 = self.user([gs])
        user2 = self.user([gs])

        self.assertResponse(play(user2), 201)

        self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(play(user1), 201)
        self.assertResponse(create_tournament(user1, method='GET'), 404, {'detail': 'You do not belong to any tournament.'})
        self.assertThread(user1, user2)

    def test_006_delete(self):
        while True:
            user1 = self.user()

            self.assertResponse(play(user1), 201)
            time.sleep(1)
            response = is_in_game(user1)
            if response.status_code == 404:
                break
            self.assertThread(user1)

        self.assertResponse(play(user1, method='DELETE'), 204)
        self.assertThread(user1)

    def test_006_delete_not_play(self):
        user1 = self.user()

        self.assertResponse(play(user1, method='DELETE'), 404, {'detail': 'You are not currently playing.'})
        self.assertThread(user1)

    def test_007_not_connected_sse(self):
        user1 = self.user(sse=False)

        self.assertResponse(play(user1), 401, {'code': 'sse_connection_required', 'detail': 'You need to be connected to SSE to access this resource.'})

    def test_008_ranked_trophies(self):
        user1 = self.user([ppu, ppu, ppu, gs])
        user2 = self.user([ppu, ppu, gs])
        user3 = self.user([ppu, ppu, gs])
        user4 = self.user([ppu, ppu, ppu, gs])

        self.assertResponse(set_trophies(user1, 1000), 201)
        self.assertResponse(set_trophies(user2, 900), 201)
        self.assertResponse(set_trophies(user3, 870), 201)
        self.assertResponse(set_trophies(user4, 1000), 201)

        self.assertResponse(play(user1, game_mode='ranked'), 201)
        self.assertResponse(play(user2, game_mode='ranked'), 201)
        time.sleep(1)
        self.assertResponse(is_in_game(user1), 404)
        self.assertResponse(play(user3, game_mode='ranked'), 201)
        self.assertResponse(play(user4, game_mode='ranked'), 201)
        time.sleep(1)
        self.assertThread(user1, user2, user3, user4)

    def test_009_ranked_trophies_closer(self):
        user1 = self.user([ppu, ppu, ppu, gs])
        user2 = self.user([ppu, ppu, gs])
        user3 = self.user([ppu, ppu, gs])
        user4 = self.user([ppu, ppu, ppu, gs])

        self.assertResponse(set_trophies(user1, 1000), 201)
        self.assertResponse(set_trophies(user2, 949), 201)
        self.assertResponse(set_trophies(user3, 960), 201)
        self.assertResponse(set_trophies(user4, 1000), 201)

        self.assertResponse(play(user1, game_mode='ranked'), 201)
        self.assertResponse(play(user2, game_mode='ranked'), 201)
        time.sleep(1)
        self.assertResponse(is_in_game(user1), 404)
        self.assertResponse(play(user3, game_mode='ranked'), 201)
        self.assertResponse(play(user4, game_mode='ranked'), 201)
        time.sleep(1)
        self.assertThread(user1, user2, user3, user4)

    def test_010_blocked_user(self):
        user1 = self.user([lj, lup, gs])
        user2 = self.user([lup, gs])
        user3 = self.user()
        user4 = self.user([lj, lj, lup, lup, gs])
        user5 = self.user([lj, lup, lup, gs])
        user6 = self.user([lup, lup, gs])
        user7 = self.user([gs])

        self.assertResponse(blocked_user(user3, user1['id']), 201)
        self.assertResponse(blocked_user(user6, user1['id']), 201)

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user1, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user2, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user3), 201, get_field='code')
        self.assertResponse(join_lobby(user3, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user4), 201, get_field='code')
        self.assertResponse(join_lobby(user5, code), 201)
        self.assertResponse(join_lobby(user6, code), 201)
        self.assertResponse(join_lobby(user4, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user5, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user6, code, data={'is_ready': True}), 200)

        self.assertResponse(is_in_game(user1), 404)
        self.assertResponse(is_in_game(user3), 404)

        code = self.assertResponse(create_lobby(user7), 201, get_field='code')
        self.assertResponse(join_lobby(user7, code, data={'is_ready': True}), 200)

        time.sleep(2)

        self.assertResponse(is_in_game(user1), 200)
        self.assertResponse(is_in_game(user3), 404)
        self.assertResponse(is_in_game(user4), 200)
        self.assertResponse(is_in_game(user7), 200)

        self.assertThread(user1, user2, user3, user4, user5, user6, user7)

    def test_011_blocked_by_user(self):
        user1 = self.user([lj, lup, gs])
        user2 = self.user([lup, gs])
        user3 = self.user()
        user4 = self.user([lj, lj, lup, lup, gs])
        user5 = self.user([lj, lup, lup, gs])
        user6 = self.user([lup, lup, gs])
        user7 = self.user([gs])

        self.assertResponse(blocked_user(user1, user3['id']), 201)
        self.assertResponse(blocked_user(user6, user1['id']), 201)

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user1, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user2, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user3), 201, get_field='code')
        self.assertResponse(join_lobby(user3, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user4), 201, get_field='code')
        self.assertResponse(join_lobby(user5, code), 201)
        self.assertResponse(join_lobby(user6, code), 201)
        self.assertResponse(join_lobby(user4, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user5, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user6, code, data={'is_ready': True}), 200)

        self.assertResponse(is_in_game(user1), 404)
        self.assertResponse(is_in_game(user3), 404)

        code = self.assertResponse(create_lobby(user7), 201, get_field='code')
        self.assertResponse(join_lobby(user7, code, data={'is_ready': True}), 200)

        time.sleep(2)

        self.assertResponse(is_in_game(user1), 200)
        self.assertResponse(is_in_game(user3), 404)
        self.assertResponse(is_in_game(user4), 200)
        self.assertResponse(is_in_game(user7), 200)

        self.assertThread(user1, user2, user3, user4, user5, user6, user7)


if __name__ == '__main__':
    unittest.main()
