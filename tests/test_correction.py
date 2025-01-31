import time

from services.friend import friend_requests, friend_request
from services.game import score
from services.lobby import create_lobby, join_lobby
from services.play import play
from services.stats import set_trophies
from services.tournament import create_tournament, join_tournament
from services.user import me
from utils.config import MAX_SCORE
from utils.my_unittest import UnitTest
from utils.sse_event import gs, ppu, lup, lj, ll, tj, ts, tmf, tf, afr, rfr


class Test01_Correction(UnitTest):

    def test_001_user_flo(self):
        scorer = int(100 / MAX_SCORE - 10)
        game = [lup, lup, gs]
        user1_duel = [gs] * 10 + [ppu, ppu] + [gs] * scorer + [ppu] + [gs] * (40 - scorer) + [ppu] + [gs] * 50 + [ppu]
        user1_clash = [lj, lj] + game * 10 + [ppu] + game * int(100 / MAX_SCORE) + [ppu] + game * (40 - scorer) + [ppu] + game * 50 + [ppu]
        user1_ranked = [ppu, ppu, ppu, ppu, ppu, ppu]
        user1_fun_player = [gs, gs] + [lj, lj, lup, lup, gs] + [ppu, ppu, ppu, tj, tj, tj, ts, gs, tmf, ppu, tmf, gs, tmf, tf, ppu]
        user1_scorer = [afr, ppu] + [afr] * 49 + [ppu]
        rel = ['game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'profile-picture-unlocked', 'profile-picture-unlocked', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'profile-picture-unlocked', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'profile-picture-unlocked', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'game-start', 'profile-picture-unlocked', 'lobby-join', 'lobby-join', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'profile-picture-unlocked', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'profile-picture-unlocked', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'profile-picture-unlocked', 'profile-picture-unlocked', 'profile-picture-unlocked', 'profile-picture-unlocked', 'profile-picture-unlocked', 'profile-picture-unlocked', 'profile-picture-unlocked', 'profile-picture-unlocked', 'lobby-leave', 'lobby-leave', 'game-start', 'lobby-join', 'lobby-join', 'lobby-update-participant', 'lobby-update-participant', 'game-start', 'tournament-join', 'tournament-join', 'tournament-join', 'tournament-start', 'game-start', 'tournament-match-finish', 'profile-picture-unlocked', 'tournament-match-finish', 'game-start', 'tournament-match-finish', 'tournament-finish', 'profile-picture-unlocked']
        user1 = self.user(user1_duel + user1_clash + user1_ranked + user1_fun_player + user1_scorer)
        user2 = self.user([gs] * 100)

# Duel ------------------------------------------------------------- #
        for ngame, pp in ((10, 7), (40, 8), (50, 9)):
            for _ in range(ngame):
                self.assertResponse(play(user1), 201)
                self.assertResponse(play(user2), 201)
                time.sleep(1)
                for _ in range(MAX_SCORE):
                    self.assertResponse(score(user1['id']), 200)
        self.assertThread(user2)

# Clash ------------------------------------------------------------- #
        def set_ready():
            for u_ in (user1, user2, user3):
                self.assertResponse(join_lobby(u_, code1, data={'is_ready': True}), 200)

            for u_ in (user4, user5, user6):
                self.assertResponse(join_lobby(u_, code2, data={'is_ready': True}), 200)

        user2 = self.user([lj] + game * 10 + [ppu, ppu] + game * 40 + [ppu] + game * 50 + [ppu])
        user3 = self.user(game * 10 + [ppu, ppu] + game * 40 + [ppu] + game * 50 + [ppu])
        user4 = self.user([lj, lj] + game * 100)
        user5 = self.user([lj] + game * 100)
        user6 = self.user(game * 100)

        code1 = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code1), 201)
        self.assertResponse(join_lobby(user3, code1), 201)

        code2 = self.assertResponse(create_lobby(user4), 201, get_field='code')
        self.assertResponse(join_lobby(user5, code2), 201)
        self.assertResponse(join_lobby(user6, code2), 201)

        for game, pp in ((10, 4), (40, 5), (50, 6)):
            for _ in range(game):
                set_ready()
                for _ in range(MAX_SCORE):
                    self.assertResponse(score(user1['id']), 200)

        self.assertThread(user2, user3, user4, user5, user6)

# Ranked ------------------------------------------------------------- #
        for trophies, pp in ((100, 10), (400, 11), (500, 12), (1000, 13), (1000, 14), (2000, 15)):
            self.assertResponse(set_trophies(user1, trophies), 201)

# Fun Player  ------------------------------------------------------------- #
        user2 = self.user([gs] + [lj, lup, lup, gs, ll, lup])
        user3 = self.user([gs] + [lup, lup, gs, ll, lup])
        user4 = self.user([lj, lj, lup, lup, gs])
        user5 = self.user([lj, lup, lup, gs])
        user6 = self.user([lup, lup, gs])
        user7 = self.user([ppu, ppu, tj, tj, ts, gs, tmf, tmf, gs, tmf, tf])
        user8 = self.user([ppu, tj, ts, gs, tmf, tmf, tmf, tf])
        user9 = self.user([ts, gs, tmf, tmf, tmf, tf])

        # Duel
        self.assertResponse(play(user1), 201)
        self.assertResponse(play(user2), 201)
        time.sleep(1)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        # Clash
        code1 = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code1), 201)
        self.assertResponse(join_lobby(user3, code1), 201)
        code2 = self.assertResponse(create_lobby(user4), 201, get_field='code')
        self.assertResponse(join_lobby(user5, code2), 201)
        self.assertResponse(join_lobby(user6, code2), 201)
        for u in (user1, user2, user3):
            self.assertResponse(join_lobby(u, code1, data={'is_ready': True}), 200)
        for u in (user4, user5, user6):
            self.assertResponse(join_lobby(u, code2, data={'is_ready': True}), 200)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        # Tournament
        self.assertResponse(set_trophies(user1, 1000), 201)
        self.assertResponse(set_trophies(user7, 500), 201)
        self.assertResponse(set_trophies(user8, 200), 201)
        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user7, code), 201)
        self.assertResponse(join_tournament(user8, code), 201)
        self.assertResponse(join_tournament(user9, code), 201)
        time.sleep(5)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user7['id']), 200)
        time.sleep(5)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        self.assertThread(user2, user3, user4, user5, user6, user7, user8, user9)

# Friend ------------------------------------------------------------- #
        for nb, pp in ((1, 19), (49, 20)):
            for _ in range(nb):
                user2 = self.user([rfr, ppu])
                id = self.assertResponse(friend_requests(user1, user2), 201, get_field=True)
                self.assertResponse(friend_request(id, user2), 201)
                self.assertThread(user2)

        self.assertResponse(me(user1, 'PATCH', data={'username': 'flo'}), 200)
        print('User1:', user1)
        self.assertThread(user1)
