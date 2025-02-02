import time
import unittest

from services.blocked import blocked_user, unblocked_user
from services.friend import create_friendship
from services.game import score, get_games, get_tournament
from services.lobby import create_lobby, join_lobby
from services.stats import set_trophies
from services.tournament import create_tournament, join_tournament, ban_user, search_tournament, invite_user, post_message
from utils.config import MAX_SCORE
from utils.generate_random import rnstr
from utils.my_unittest import UnitTest
from utils.sse_event import ppu, tj, ts, gs, tmf, tf, tsa, lj, afr, rfr, it, tl, tm


class Test01_Tournament(UnitTest):

    def test_001_create_tournament(self):
        user1 = self.user()

        self.assertResponse(create_tournament(user1), 201)
        self.assertThread(user1)

    def test_002_join_tournament(self):
        user1 = self.user([tj])
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertThread(user1, user2)

    def test_003_join_two_tournament(self):
        user1 = self.user([tj, tl, tj])
        user2 = self.user()
        user3 = self.user([tj])
        user4 = self.user(guest=True)

        code1 = self.assertResponse(create_tournament(user1), 201, get_field='code')
        code2 = self.assertResponse(create_tournament(user3), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code1), 201)
        self.assertResponse(join_tournament(user2, code1, method='DELETE'), 204)
        self.assertResponse(join_tournament(user2, code2), 201)
        self.assertResponse(join_tournament(user4, code1), 201)
        self.assertThread(user1, user2, user3, user4)


class Test02_ErrorTournament(UnitTest):

    def test_001_tournament_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(join_tournament(user1, '123456'), 404, {'detail': 'Tournament not found.'})
        self.assertThread(user1)

    def test_002_already_join(self):
        user1 = self.user([tj])
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user1, code), 409, {'detail': 'You already joined this tournament.'})
        self.assertResponse(join_tournament(user2, code), 409, {'detail': 'You already joined this tournament.'})
        self.assertThread(user1, user2)

    def test_003_already_started_not_full(self):
        user1 = self.user([tj] * 6 + [tsa, ts])
        user2 = self.user()
        users = [self.user([tj] * (5 - i) + [tsa, ts, gs]) for i in range(6)]

        self.assertResponse(set_trophies(user1, 1), 201)
        code = self.assertResponse(create_tournament(user1, size=8), 201, get_field='code')

        for user_tmp in users:
            self.assertResponse(join_tournament(user_tmp, code), 201)
        time.sleep(30)
        self.assertResponse(join_tournament(user2, code), 403, {'detail': 'Tournament already started.'})
        self.assertThread(user1, user2, *users)

    def test_004_already_started(self):
        user1 = self.user([tj] * 3 + [ts, gs])
        user2 = self.user()
        users = [self.user([tj] * (2 - i) + [ts, gs]) for i in range(3)]

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        for user_tmp in users:
            self.assertResponse(join_tournament(user_tmp, code), 201)
        time.sleep(5)
        self.assertResponse(join_tournament(user2, code), 403, {'detail': 'Tournament already started.'})
        self.assertThread(user1, user2, *users)

    def test_005_guest_create_tournament(self):
        user1 = self.user(guest=True)

        self.assertResponse(create_tournament(user1), 403, {'detail': 'Guest users cannot perform this action.'})
        self.assertThread(user1)

    def test_006_no_name(self):
        user1 = self.user()

        self.assertResponse(create_tournament(user1, data={}), 400, {'name': ['This field is required.']})
        self.assertThread(user1)

    def test_007_blocked_user_cannot_join(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(blocked_user(user1, user2['id']), 201)
        self.assertResponse(join_tournament(user2, code), 404, {'detail': 'Tournament not found.'})
        self.assertThread(user1, user2)

    def test_008_blocked_user(self):
        user1 = self.user([tj, tl])
        user2 = self.user(['tournament-banned'])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(blocked_user(user1, user2['id']), 201)

        response = self.assertResponse(create_tournament(user1, method='GET'), 200, get_field='participants')
        self.assertEqual(1, len(response))

        self.assertResponse(create_tournament(user2, method='GET'), 404, {'detail': 'You do not belong to any tournament.'})
        self.assertThread(user1, user2)

    def test_009_blocked_user_not_creator(self):
        user1 = self.user([tj, tj])
        user2 = self.user([tj])
        user3 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(blocked_user(user2, user3['id']), 201)

        response = self.assertResponse(create_tournament(user1, method='GET'), 200, get_field='participants')
        self.assertEqual(3, len(response))
        self.assertThread(user1, user2, user3)

    def test_010_blocked_then_unblock(self):
        user1 = self.user([tj, tl, tj])
        user2 = self.user(['tournament-banned'])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)
        blocked_id = self.assertResponse(blocked_user(user1, user2['id']), 201, get_field=True)

        response = self.assertResponse(create_tournament(user1, method='GET'), 200, get_field='participants')
        self.assertEqual(1, len(response))

        self.assertResponse(join_tournament(user2, code), 404, {'detail': 'Tournament not found.'})
        self.assertResponse(unblocked_user(user1, blocked_id), 204)
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertThread(user1, user2)

    def test_011_create_two_tournament(self):
        user1 = self.user()

        self.assertResponse(create_tournament(user1), 201)
        self.assertResponse(create_tournament(user1), 403, {'detail': 'You cannot create more than one tournament at the same time.'})
        self.assertThread(user1)

    def test_012_create_two_tournament_leave_first(self):
        user1 = self.user([tj])
        user2 = self.user([tl])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)

        self.assertResponse(join_tournament(user1, code, 'DELETE'), 204)
        self.assertResponse(create_tournament(user1), 403, {'detail': 'You cannot create more than one tournament at the same time.'})
        self.assertResponse(join_tournament(user2, code, 'DELETE'), 204)
        self.assertResponse(create_tournament(user1), 201)
        self.assertThread(user1, user2)

    def test_013_join_tournament_without_sse(self):
        user1 = self.user(sse=False)
        user2 = self.user()

        self.assertResponse(create_tournament(user1), 401, {'code': 'sse_connection_required', 'detail': 'You need to be connected to SSE to access this resource.'})
        code = self.assertResponse(create_tournament(user2), 201, get_field='code')
        self.assertResponse(join_tournament(user1, code), 401, {'code': 'sse_connection_required', 'detail': 'You need to be connected to SSE to access this resource.'})
        self.assertThread(user2)

    def test_014_wrong_size(self):
        user1 = self.user()

        self.assertResponse(create_tournament(user1, size=14), 400)
        self.assertResponse(create_tournament(user1, size=2), 400)
        self.assertResponse(create_tournament(user1, size=7), 400)
        self.assertThread(user1)

    def test_015_user_blocked_creator(self):
        user1 = self.user([tj, tj, tl])
        user2 = self.user([tj, tl])
        user3 = self.user(['tournament-banned'])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(blocked_user(user3, user1['id']), 201)
        response = self.assertResponse(create_tournament(user1, method='GET'), 200, get_field='participants')
        self.assertEqual(2, len(response))
        self.assertThread(user1, user2, user3)


class Test03_BanTournament(UnitTest):

    def test_001_ban_tournament(self):
        user1 = self.user([tj, tl])
        user2 = self.user(['tournament-banned'])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(ban_user(user1, user2, code), 204)
        self.assertResponse(join_tournament(user2, code), 404, {'detail': 'Tournament not found.'})

        response = self.assertResponse(create_tournament(user1, method='GET'), 200, get_field='participants')
        self.assertEqual(1, len(response))
        self.assertThread(user1, user2)

    def test_002_user_ban_not_join_tournament(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(ban_user(user2, user1, code), 403, {'detail': 'You do not belong to this tournament.'})
        self.assertThread(user1, user2)

    def test_003_user_banned_not_join_tournament(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(ban_user(user1, user2, code), 404, {'detail': 'This user does not belong to this tournament.'})
        self.assertThread(user1, user2)

    def test_004_invalid_tournament(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(ban_user(user1, user2, '123456'), 403, {'detail': 'You do not belong to this tournament.'})
        self.assertThread(user1, user2)

    def test_005_not_creator(self):
        user1 = self.user([tj])
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(ban_user(user2, user1, code), 403, {'detail': 'Only the tournament creator can ban a user.'})
        self.assertThread(user1, user2)

    def test_006_users_does_exist(self):
        user1 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(ban_user(user1, {'id': 123456789}, code), 404, {'detail': 'This user does not belong to this tournament.'})
        self.assertThread(user1)


class Test04_UpdateTournament(UnitTest):

    def test_001_update_tournament(self):
        user1 = self.user()

        self.assertResponse(create_tournament(user1, {'size': 12, 'name': 'coucou'}, 'PATCH'), 405, {'detail': 'Method "PATCH" not allowed.'})
        self.assertThread(user1)


class Test05_UpdateParticipantTournament(UnitTest):

    def test_001_update_participant(self):
        user1 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user1, code, data={'index': 2}), 405, {'detail': 'Method "PATCH" not allowed.'})
        self.assertThread(user1)


class Test06_LeaveTournament(UnitTest):

    def test_001_leave_tournament_then_destroy(self):
        user1 = self.user([tj, tj])
        users = [self.user([tj] * (1 - i) + [tl] * (i + 1)) for i in range(2)]

        response = self.assertResponse(create_tournament(user1), 201)
        code = response['code']
        name = response['name']

        for u in users:
            self.assertResponse(join_tournament(u, code), 201)

        self.assertResponse(join_tournament(user1, code, 'DELETE'), 204)
        self.assertResponse(create_tournament(user1, method='GET'), 404, {'detail': 'You do not belong to any tournament.'})

        self.assertResponse(search_tournament(user1, name), 200, count=1)

        for u in users:
            self.assertResponse(create_tournament(u, method='GET'), 200)

        for u in users:
            self.assertResponse(join_tournament(u, code, 'DELETE'), 204)
            self.assertResponse(create_tournament(u, method='GET'), 404, {'detail': 'You do not belong to any tournament.'})
            self.assertResponse(create_tournament(u, method='GET'), 404, {'detail': 'You do not belong to any tournament.'})

        self.assertResponse(search_tournament(user1, name), 200, count=0)
        self.assertThread(user1, *users)

    def test_002_leave_tournament(self):
        user1 = self.user([tj])
        user2 = self.user([tl])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user1, code, 'DELETE'), 204)

        response = self.assertResponse(create_tournament(user2, method='GET'), 200, get_field='participants')
        self.assertEqual(1, len(response))
        self.assertThread(user1, user2)

    def test_004_leave_tournament_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(join_tournament(user1, '123456', method='DELETE'), 403, {'detail': 'You do not belong to this tournament.'})
        self.assertThread(user1)

    def test_005_leave_tournament_does_not_join(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code, 'DELETE'), 403, {'detail': 'You do not belong to this tournament.'})
        self.assertThread(user1, user2)

    def test_006_leave_tournament_not_creator(self):
        user1 = self.user([tj, tl])
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user2, code, 'DELETE'), 204)

        response = self.assertResponse(create_tournament(user1, method='GET'), 200, get_field='participants')
        self.assertEqual(1, len(response))
        self.assertThread(user1, user2)

    def test_007_leave_tournament_then_come_back_still_creator(self):
        user1 = self.user([tj])
        user2 = self.user([tl, tj])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)

        self.assertResponse(join_tournament(user1, code, 'DELETE'), 204)

        response = self.assertResponse(join_tournament(user1, code), 201)
        for u in response['participants']:
            if u['id'] == user1['id']:
                self.assertTrue(u['creator'])
                break
        self.assertThread(user1, user2)

    def test_008_reconnect(self):
        user1 = self.user([ppu, ppu, ppu, tj, tj, tj, ts, gs, tmf, tmf, gs, tmf, tf, ppu])
        user2 = self.user([ppu, ppu, tj, tj, ts, gs, tmf, tmf, gs, tmf, tf])
        user3 = self.user([ppu, tj, ts, gs, tmf, tmf, tmf, tf])
        user4 = self.user([ts, gs, tmf, tmf, tf])

        self.assertResponse(set_trophies(user1, 1000), 201)
        self.assertResponse(set_trophies(user2, 500), 201)
        self.assertResponse(set_trophies(user3, 200), 201)

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)

        time.sleep(5)

        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        time.sleep(1)
        self.assertResponse(join_tournament(user4, code, method='DELETE'), 204)

        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)

        time.sleep(5)

        self.assertResponse(join_tournament(user4, code), 201)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        self.assertThread(user1, user2, user3, user4)


class Test07_GetTournament(UnitTest):

    def test_001_get_tournament(self):
        user1 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        response = self.assertResponse(create_tournament(user1, method='GET'), 200)
        self.assertEqual(code, response['code'])
        self.assertThread(user1)

    def test_002_get_tournament_does_not_join(self):
        user1 = self.user()

        self.assertResponse(create_tournament(user1, method='GET'), 404, {'detail': 'You do not belong to any tournament.'})
        self.assertThread(user1)

    def test_002_get_tournament_participant(self):
        user1 = self.user([tj])
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')

        self.assertResponse(join_tournament(user2, code), 201)

        response = self.assertResponse(create_tournament(user1, method='GET'), 200, get_field='participants')
        self.assertEqual(2, len(response))
        self.assertThread(user1, user2)

    def test_003_get_tournament_participant_does_not_join(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(create_tournament(user2, method='GET'), 404, {'detail': 'You do not belong to any tournament.'})
        self.assertThread(user1, user2)

    def test_004_search_tournaments(self):
        user1 = self.user()
        user2 = self.user()
        name = rnstr()
        users = [self.user() for _ in range(5)]

        for user_tmp in users:
            self.assertResponse(create_tournament(user_tmp, data={'name': 'Tournoi ' + name + rnstr()}), 201)

        self.assertResponse(create_tournament(user2, data={'name': 'coucou' + name}), 201)

        self.assertResponse(search_tournament(user1, 'coucou' + name), 200, count=1)

        self.assertResponse(search_tournament(user1, 'Tournoi ' + name), 200, count=5)
        [self.assertThread(u) for u in users]
        self.assertThread(user1, user2)

    def test_005_search_private_tournament(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(create_tournament(user1, data={'name': 'private' + rnstr(), 'private': True}), 201)

        self.assertResponse(search_tournament(user2, 'private'), 200, count=0)

        self.assertResponse(search_tournament(user1, 'private'), 200, count=1)
        self.assertThread(user1, user2)

    def test_006_search_tournament_none(self):
        user1 = self.user()

        self.assertResponse(search_tournament(user1, 'caca'), 200, count=0)
        self.assertThread(user1)

    def test_007_search_tournaments_blocked_by_creator_tournament(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()
        name = rnstr()

        self.assertResponse(create_tournament(user3, data={'name': 'Blocked ' + name + rnstr()}), 201)
        self.assertResponse(create_tournament(user1, data={'name': 'Blocked ' + name + rnstr()}), 201)
        blocked_id = self.assertResponse(blocked_user(user1, user2['id']), 201, get_field=True)
        self.assertResponse(search_tournament(user2, 'Blocked ' + name), 200, count=1)
        self.assertResponse(unblocked_user(user1, blocked_id), 204)
        self.assertResponse(search_tournament(user2, 'Blocked ' + name), 200, count=2)
        self.assertThread(user1, user2, user3)

    def test_008_search_tournaments_blocked_by_user_tournament(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()
        name = rnstr()

        self.assertResponse(create_tournament(user3, data={'name': 'Blocked ' + name + rnstr()}), 201)
        self.assertResponse(create_tournament(user1, data={'name': 'Blocked ' + name + rnstr()}), 201)
        blocked_id = self.assertResponse(blocked_user(user2, user1['id']), 201, get_field=True)
        self.assertResponse(search_tournament(user2, 'Blocked ' + name), 200, count=1)
        self.assertResponse(unblocked_user(user2, blocked_id), 204)
        self.assertResponse(search_tournament(user2, 'Blocked ' + name), 200, count=2)
        self.assertThread(user1, user2, user3)

    def test_009_search_tournaments_banned(self):
        user1 = self.user([tj, tl])
        user2 = self.user([tj, tl])
        user3 = self.user(['tournament-banned', 'tournament-banned'])
        user4 = self.user()
        name = 'Banned ' + rnstr()

        for u in (user1, user2):
            code = self.assertResponse(create_tournament(u, data={'name': name + rnstr()}), 201, get_field='code')
            self.assertResponse(search_tournament(user3, name), 200, count=1)
            self.assertResponse(join_tournament(user3, code), 201)
            self.assertResponse(ban_user(u, user3, code), 204)
        self.assertResponse(search_tournament(user3, name), 200, count=0)
        self.assertResponse(search_tournament(user4, name), 200, count=2)
        self.assertThread(user1, user2, user3, user4)


class Test08_InviteTournament(UnitTest):

    def test_001_invite(self):
        user1 = self.user([afr, ppu, tj])
        user2 = self.user([afr, ppu])
        user3 = self.user([rfr, ppu, it])
        user4 = self.user([rfr, ppu, it])

        self.assertFriendResponse(create_friendship(user1, user3))
        self.assertFriendResponse(create_friendship(user2, user4))
        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(invite_user(user1, user3, code), 204)
        self.assertResponse(invite_user(user2, user4, code), 204)
        self.assertThread(user1, user2, user3, user4)

    def test_004_invite_yourself(self):
        user1 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(invite_user(user1, user1, code), 403, {'detail': 'You cannot invite yourself.'})
        self.assertThread(user1)

    def test_005_not_friend(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(invite_user(user1, user2, code), 403, {'detail': 'You can only invite friends.'})
        self.assertThread(user1, user2)

    def test_006_not_creator_private_tournament(self):
        user1 = self.user([tj])
        user2 = self.user()
        user3 = self.user()

        code = self.assertResponse(create_tournament(user1, private=True), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(invite_user(user2, user3, code), 403, {'detail': 'Only the tournament creator can invite users.'})
        self.assertThread(user1, user2, user3)

    def test_007_user_already_in_tournament(self):
        user1 = self.user([tj])
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(invite_user(user1, user2, code), 409, {'detail': 'This user is already in this tournament.'})
        self.assertThread(user1, user2)

    def test_008_not_in_tournament(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(invite_user(user2, user3, code), 403, {'detail': 'You do not belong to this tournament.'})
        self.assertThread(user1, user2, user3)


class Test09_StartTournament(UnitTest):

    def test_001_start_tournament_full(self):
        user1 = self.user([tj] * 3 + [ts])
        user2 = self.user([tj] * 2 + [ts])
        user3 = self.user([tj] + [ts])
        user4 = self.user([ts])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)

        self.assertResponse(create_tournament(user1, method='GET'), 200)
        self.assertThread(user1, user2, user3, user4)

    def test_002_start_tournament_80(self):
        users = [self.user([tj] * (6 - i) + [tsa, tj, ts, gs]) for i in range(7)]
        user1 = self.user([ts, gs])

        code = self.assertResponse(create_tournament(users[0], size=8), 201, get_field='code')
        for u in users[1:]:
            self.assertResponse(join_tournament(u, code), 201)

        time.sleep(5)
        self.assertResponse(join_tournament(user1, code), 201)
        time.sleep(5)
        self.assertThread(user1, *users)

    def test_003_cancel_start(self):
        user1 = self.user([tj, tj, tj, tj, tj, tj, tsa, tl, 'tournament-start-cancel'])
        user2 = self.user([tj, tj, tj, tj, tj, tsa, tl, 'tournament-start-cancel'])
        user3 = self.user([tj, tj, tj, tj, tsa, tl, 'tournament-start-cancel'])
        user4 = self.user([tj, tj, tj, tsa, tl, 'tournament-start-cancel'])
        user5 = self.user([tj, tj, tsa, tl, 'tournament-start-cancel'])
        user6 = self.user([tj, tsa, tl, 'tournament-start-cancel'])
        user7 = self.user([tsa])

        code = self.assertResponse(create_tournament(user1, size=8), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)
        self.assertResponse(join_tournament(user5, code), 201)
        self.assertResponse(join_tournament(user6, code), 201)
        self.assertResponse(join_tournament(user7, code), 201)

        time.sleep(2)
        self.assertResponse(join_tournament(user7, code, method='DELETE'), 204)
        time.sleep(2)

        self.assertThread(user1, user2, user3, user4, user5, user6, user7)

    def test_004_ban_after_start(self):
        user1 = self.user([tj, tj, tj, ts, gs])
        user2 = self.user([tj, tj, ts, gs])
        user3 = self.user([tj, ts, gs])
        user4 = self.user([ts, gs])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)

        time.sleep(5)
        self.assertResponse(ban_user(user1, user4, code), 403)

        self.assertThread(user1, user2, user3, user4)


class Test10_FinishTournament(UnitTest):

    def test_001_finish(self):
        user1 = self.user([tj, tj, tj, ts, gs, tmf, tmf, gs, tmf, tf, ppu])
        user2 = self.user([tj, tj, ts, gs, tmf, tmf, gs, tmf, tf])
        user3 = self.user([tj, ts, gs, tmf, tmf, tmf, tf])
        user4 = self.user([ts, gs, tmf, tmf, tmf, tf])

        self.assertResponse(set_trophies(user1, 10), 201)
        self.assertResponse(set_trophies(user2, 7), 201)
        self.assertResponse(set_trophies(user3, 3), 201)

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
        self.assertThread(user1, user2, user3, user4)

    def test_002_finish_8_seeding(self):
        user1 = self.user([tj, tj, tj, tj, tj, tj, tsa, tj, ts, gs, tmf, tmf, tmf, tmf, gs, tmf, tmf, gs, tmf, tf])
        user2 = self.user([tj, tj, tj, tj, tj, tsa, tj, ts, gs, tmf, tmf, tmf, tmf, gs, tmf, tmf, tmf, tf])
        user3 = self.user([tj, tj, tj, tj, tsa, tj, ts, gs, tmf, tmf, tmf, tmf, gs, tmf, tmf, gs, tmf, tf, ppu])
        user4 = self.user([tj, tj, tj, tsa, tj, ts, gs, tmf, tmf, tmf, tmf, tmf, tmf, tmf, tf])
        user5 = self.user([tj, tj, tsa, tj, ts, gs, tmf, tmf, tmf, tmf, gs, tmf, tmf, tmf, tf])
        user6 = self.user([tj, tsa, tj, ts, gs, tmf, tmf, tmf, tmf, tmf, tmf, tmf, tf])
        user7 = self.user([tsa, tj, ts, gs, tmf, tmf, tmf, tmf, tmf, tmf, tmf, tf])
        user8 = self.user([ts, gs, tmf, tmf, tmf, tmf, tmf, tmf, tmf, tf])

        self.assertResponse(set_trophies(user1, 14), 201)
        self.assertResponse(set_trophies(user2, 12), 201)
        self.assertResponse(set_trophies(user3, 10), 201)
        self.assertResponse(set_trophies(user4, 8), 201)
        self.assertResponse(set_trophies(user5, 6), 201)
        self.assertResponse(set_trophies(user6, 4), 201)
        self.assertResponse(set_trophies(user7, 2), 201)

        code = self.assertResponse(create_tournament(user1, size=8), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)
        self.assertResponse(join_tournament(user5, code), 201)
        self.assertResponse(join_tournament(user6, code), 201)
        self.assertResponse(join_tournament(user7, code), 201)
        time.sleep(5)
        self.assertResponse(join_tournament(user8, code), 201)

        time.sleep(5)

        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        self.assertResponse(score(user7['id']), 200)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)

        self.assertResponse(score(user6['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user6['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user3['id']), 200)

        self.assertResponse(score(user4['id']), 200)
        self.assertResponse(score(user5['id']), 200)
        self.assertResponse(score(user4['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user5['id']), 200)

        time.sleep(5)

        self.assertResponse(score(user5['id']), 200)
        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user5['id']), 200)
        for _ in range(MAX_SCORE - 2):
            self.assertResponse(score(user1['id']), 200)

        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user2['id']), 200)
        for _ in range(MAX_SCORE - 2):
            self.assertResponse(score(user3['id']), 200)

        time.sleep(5)

        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user1['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user3['id']), 200)

        time.sleep(5)
        self.assertThread(user1, user2, user3, user4, user5, user6, user7, user8)

    def test_003_finish_16_seeding(self):
        user1 = self.user([tj] * 13 + [tsa, tj, tj, ts, gs] + [tmf] * 8 + [gs] + [tmf] * 4 + [gs, tmf, tmf, gs, tmf, tf, ppu])
        user2 = self.user([tj] * 12 + [tsa, tj, tj, ts, gs] + [tmf] * 8 + [gs] + [tmf] * 4 + [gs, tmf, tmf, gs, tmf, tf])
        user3 = self.user([tj] * 11 + [tsa, tj, tj, ts, gs] + [tmf] * 8 + [gs] + [tmf] * 4 + [gs, tmf, tmf])
        user4 = self.user([tj] * 10 + [tsa, tj, tj, ts, gs] + [tmf] * 8 + [gs] + [tmf] * 4 + [gs, tmf, tmf])
        user5 = self.user([tj] * 9 + [tsa, tj, tj, ts, gs] + [tmf] * 8 + [gs] + [tmf] * 4)
        user6 = self.user([tj] * 8 + [tsa, tj, tj, ts, gs] + [tmf] * 8 + [gs] + [tmf] * 4)
        user7 = self.user([tj] * 7 + [tsa, tj, tj, ts, gs] + [tmf] * 8 + [gs] + [tmf] * 4)
        user8 = self.user([tj] * 6 + [tsa, tj, tj, ts, gs] + [tmf] * 8)
        user9 = self.user([tj] * 5 + [tsa, tj, tj, ts, gs] + [tmf] * 8 + [gs] + [tmf] * 4)
        user10 = self.user([tj] * 4 + [tsa, tj, tj, ts, gs] + [tmf] * 8)
        user11 = self.user([tj] * 3 + [tsa, tj, tj, ts, gs] + [tmf] * 8)
        user12 = self.user([tj] * 2 + [tsa, tj, tj, ts, gs] + [tmf] * 8)
        user13 = self.user([tj] * 1 + [tsa, tj, tj, ts, gs] + [tmf] * 8)
        user14 = self.user([tsa, tj, tj, ts, gs] + [tmf] * 8)
        user15 = self.user([tj, ts, gs] + [tmf] * 8)
        user16 = self.user([ts, gs] + [tmf] * 8)

        self.assertResponse(set_trophies(user1, 15), 201)
        self.assertResponse(set_trophies(user2, 14), 201)
        self.assertResponse(set_trophies(user3, 13), 201)
        self.assertResponse(set_trophies(user4, 12), 201)
        self.assertResponse(set_trophies(user5, 11), 201)
        self.assertResponse(set_trophies(user6, 10), 201)
        self.assertResponse(set_trophies(user7, 9), 201)
        self.assertResponse(set_trophies(user8, 8), 201)
        self.assertResponse(set_trophies(user9, 7), 201)
        self.assertResponse(set_trophies(user10, 6), 201)
        self.assertResponse(set_trophies(user11, 5), 201)
        self.assertResponse(set_trophies(user12, 4), 201)
        self.assertResponse(set_trophies(user13, 3), 201)
        self.assertResponse(set_trophies(user14, 2), 201)
        self.assertResponse(set_trophies(user15, 1), 201)

        code = self.assertResponse(create_tournament(user1, size=16), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)
        self.assertResponse(join_tournament(user5, code), 201)
        self.assertResponse(join_tournament(user6, code), 201)
        self.assertResponse(join_tournament(user7, code), 201)
        self.assertResponse(join_tournament(user8, code), 201)
        self.assertResponse(join_tournament(user9, code), 201)
        self.assertResponse(join_tournament(user10, code), 201)
        self.assertResponse(join_tournament(user11, code), 201)
        self.assertResponse(join_tournament(user12, code), 201)
        self.assertResponse(join_tournament(user13, code), 201)
        self.assertResponse(join_tournament(user14, code), 201)
        self.assertResponse(join_tournament(user15, code), 201)
        self.assertResponse(join_tournament(user16, code), 201)

        time.sleep(5)

# -------------------------------------------------- HUITIEME -------------------------------------------------- #

        # -------- Match 1: 1 vs 16 ------------------------------------- #
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        # -------- Match 2: 2 vs 15 ------------------------------------- #
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)

        # -------- Match 3: 3 vs 14 ------------------------------------- #
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user3['id']), 200)

        # -------- Match 4: 4 vs 13 ------------------------------------- #
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user4['id']), 200)

        # -------- Match 5: 5 vs 12 ------------------------------------- #
        self.assertResponse(score(user12['id']), 200)
        self.assertResponse(score(user5['id']), 200)
        self.assertResponse(score(user12['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user5['id']), 200)

        # -------- Match 6: 6 vs 11 ------------------------------------- #
        self.assertResponse(score(user11['id']), 200)
        self.assertResponse(score(user6['id']), 200)
        self.assertResponse(score(user11['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user6['id']), 200)

        # -------- Match 7: 7 vs 10 ------------------------------------- #
        self.assertResponse(score(user10['id']), 200)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user7['id']), 200)

        # -------- Match 8: 8 vs 9 ------------------------------------- #
        self.assertResponse(score(user8['id']), 200)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user9['id']), 200)

# -------------------------------------------------- QUART --------------------------------------------------- #
        self.assertResponse(join_tournament(user8, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user10, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user11, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user12, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user13, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user14, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user15, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user16, code, method='DELETE'), 204)
        time.sleep(5)

        # -------- Match 9: 1 vs 9 ------------------------------------- #
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        # -------- Match 10: 4 vs 5 ------------------------------------- #
        self.assertResponse(score(user4['id']), 200)
        self.assertResponse(score(user4['id']), 200)
        self.assertResponse(score(user5['id']), 200)
        for _ in range(MAX_SCORE - 2):
            self.assertResponse(score(user4['id']), 200)

        # -------- Match 11: 2 vs 7 ------------------------------------- #
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)

        # -------- Match 12: 3 vs 6 ------------------------------------- #
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user6['id']), 200)
        for _ in range(MAX_SCORE - 2):
            self.assertResponse(score(user3['id']), 200)

# -------------------------------------------------- SEMI --------------------------------------------------- #
        self.assertResponse(join_tournament(user5, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user6, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user7, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user9, code, method='DELETE'), 204)
        time.sleep(5)

        # -------- Match 13: 1 vs 4 ------------------------------------- #
        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user4['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user1['id']), 200)

        # -------- Match 14: 2 vs 3 ------------------------------------- #
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user2['id']), 200)
        self.assertResponse(score(user2['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        for _ in range(MAX_SCORE - 2):
            self.assertResponse(score(user2['id']), 200)

# -------------------------------------------------- FINAL --------------------------------------------------- #
        self.assertResponse(join_tournament(user3, code, method='DELETE'), 204)
        self.assertResponse(join_tournament(user4, code, method='DELETE'), 204)
        time.sleep(5)

        # -------- Match 15: 1 vs 2 ------------------------------------- #
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        time.sleep(5)
        self.assertThread(user1, user2, user3, user4, user5, user6, user7, user8, user9, user10, user11, user12, user13, user14, user15, user16)

    def test_003_finish_7_seeding(self):
        user1 = self.user([tj, tj, tj, tj, tj, tj, tsa, ts, tmf, tmf, tmf, tmf, gs, tmf, tmf, gs, tmf, tf])
        user2 = self.user([tj, tj, tj, tj, tj, tsa, ts, tmf, gs, tmf, tmf, tmf, gs, tmf, tmf, tmf, tf])
        user3 = self.user([tj, tj, tj, tj, tsa, ts, tmf, gs, tmf, tmf, tmf, gs, tmf, tmf, gs, tmf, tf, ppu])
        user4 = self.user([tj, tj, tj, tsa, ts, tmf, gs, tmf, tmf, tmf, tmf, tmf, tmf, tf])
        user5 = self.user([tj, tj, tsa, ts, tmf, gs, tmf, tmf, tmf, gs, tmf, tmf, tmf, tf])
        user6 = self.user([tj, tsa, ts, tmf, gs, tmf, tmf, tmf, tmf, tmf, tmf, tf])
        user7 = self.user([tsa, ts, tmf, gs, tmf, tmf, tmf, tmf, tmf, tmf, tf])

        self.assertResponse(set_trophies(user1, 7), 201)
        self.assertResponse(set_trophies(user2, 6), 201)
        self.assertResponse(set_trophies(user3, 5), 201)
        self.assertResponse(set_trophies(user4, 4), 201)
        self.assertResponse(set_trophies(user5, 3), 201)
        self.assertResponse(set_trophies(user6, 2), 201)
        self.assertResponse(set_trophies(user7, 1), 201)

        code = self.assertResponse(create_tournament(user1, size=8), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)
        self.assertResponse(join_tournament(user5, code), 201)
        self.assertResponse(join_tournament(user6, code), 201)
        self.assertResponse(join_tournament(user7, code), 201)

        time.sleep(30)

        self.assertResponse(score(user7['id']), 200)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)

        self.assertResponse(score(user6['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user6['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user3['id']), 200)

        self.assertResponse(score(user4['id']), 200)
        self.assertResponse(score(user5['id']), 200)
        self.assertResponse(score(user4['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user5['id']), 200)

        time.sleep(5)

        self.assertResponse(score(user5['id']), 200)
        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user5['id']), 200)
        for _ in range(MAX_SCORE - 2):
            self.assertResponse(score(user1['id']), 200)

        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user2['id']), 200)
        for _ in range(MAX_SCORE - 2):
            self.assertResponse(score(user3['id']), 200)

        time.sleep(5)

        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        self.assertResponse(score(user1['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user3['id']), 200)

        time.sleep(5)
        tournament_id = self.assertResponse(get_games(user3), 200)['results'][0]['tournament_id']
        response = self.assertResponse(get_tournament(tournament_id, user3), 200)
        self.assertEqual(4, len(response['matches']['quarter-final']))
        self.assertThread(user1, user2, user3, user4, user5, user6, user7)


class Test11_Message(UnitTest):

    def test_001_messages(self):
        user1 = self.user([tj, tj, tm, tl])
        user2 = self.user([tj, tm, tl, tm])
        user3 = self.user([])

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(post_message(user3, code, '    coucou    '), 201)
        self.assertResponse(join_tournament(user3, code, method='DELETE'), 204)
        self.assertResponse(post_message(user3, code, 'coucou failed'), 403)
        self.assertResponse(post_message(user1, code, 'blip blop'), 201)
        self.assertThread(user1, user2, user3)

    def test_002_not_in_tournament(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(post_message(user2, code, 'blip blop'), 403)
        self.assertThread(user1, user2)

    def test_003_tournament_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(post_message(user1, '1234', 'blip blop'), 403)
        self.assertThread(user1)

    def test_004_validation_error(self):
        user1 = self.user()

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(post_message(user1, code), 400)
        self.assertResponse(post_message(user1, code, data={'content': ['caca', 'pipi']}), 400)
        self.assertResponse(post_message(user1, code, data={'content': {'prout': 48}}), 400)
        self.assertThread(user1)

    def test_005_messages_after_start(self):
        user1 = self.user([tj, tj, tj, ts, gs, tmf, tmf, tm, gs, tmf, tf, ppu])
        user2 = self.user([tj, tj, ts, gs, tmf, tmf, tm, tm, gs, tmf, tf])
        user3 = self.user([tj, ts, gs, tmf, tmf, tm, tmf, tf])
        user4 = self.user([ts, gs, tmf, tmf, tm, tmf, tf])

        self.assertResponse(set_trophies(user1, 3), 201)
        self.assertResponse(set_trophies(user2, 2), 201)
        self.assertResponse(set_trophies(user3, 1), 201)

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)

        time.sleep(5)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)

        self.assertResponse(post_message(user1, code, data={'content': 'sadf'}), 201) # todo fix empty message
        self.assertResponse(join_tournament(user4, code, method='DELETE'), 204)
        self.assertResponse(post_message(user3, code, data={'content': 'ewfewf'}), 201)
        self.assertResponse(post_message(user4, code, data={'content': 'asfd8'}), 403)

        time.sleep(5)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        time.sleep(5)
        self.assertThread(user1, user2, user3, user4)


class Test12_BlockedTournament(UnitTest):

    def test_001_block_reconnect(self):
        user1 = self.user([ppu, ppu, ppu, tj, tj, tj, ts, gs, tmf, tmf, gs, tmf, tf, ppu])
        user2 = self.user([ppu, ppu, tj, tj, ts, gs, tmf, tmf, gs, tmf, tf])
        user3 = self.user([ppu, tj, ts, gs, tmf, tmf, tmf, tf])
        user4 = self.user([ts, gs, tmf, lj])
        user5 = self.user()
        user6 = self.user()

        self.assertResponse(blocked_user(user4, user5['id']), 201)

        self.assertResponse(set_trophies(user1, 1000), 201)
        self.assertResponse(set_trophies(user2, 500), 201)
        self.assertResponse(set_trophies(user3, 200), 201)

        code = self.assertResponse(create_tournament(user1), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        self.assertResponse(join_tournament(user3, code), 201)
        self.assertResponse(join_tournament(user4, code), 201)

        time.sleep(5)

        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        time.sleep(1)
        block_id = self.assertResponse(blocked_user(user4, user6['id']), 201, get_field=True)
        self.assertResponse(join_tournament(user4, code, method='DELETE'), 204)

        for _ in range(MAX_SCORE):
            self.assertResponse(score(user2['id']), 200)

        time.sleep(5)

        code = self.assertResponse(create_lobby(user4), 201, get_field='code')
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        self.assertResponse(join_lobby(user5, code), 404)
        self.assertResponse(join_lobby(user6, code), 404)
        self.assertResponse(unblocked_user(user4, block_id), 204)
        self.assertResponse(join_lobby(user6, code), 201)
        self.assertThread(user1, user2, user3, user4, user5, user6)


if __name__ == '__main__':
    unittest.main()
