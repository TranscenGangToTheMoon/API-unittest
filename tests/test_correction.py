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
        user1 = self.user(False, username='florian', password='')
        user2 = self.user(False, username='jules', password='')
        user3 = self.user(False, username='nino', password='')
        user4 = self.user(False, username='basile', password='')
        user5 = self.user(False, username='xavier', password='')
        user6 = self.user(False)
        user7 = self.user(False)
        user8 = self.user(False)

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

        user2 = self.user(False)
        user3 = self.user(False)
        user4 = self.user(False)
        user5 = self.user(False)
        user6 = self.user(False)

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
        self.assertThread(user1, user2, user3, user4, user5, user6, user7, user8)
