import time
import unittest

from services.blocked import blocked_user
from services.friend import create_friendship, friend_request, friend_requests, get_friend_requests_received, \
    get_friends, friend
from services.game import score
from services.lobby import create_lobby, join_lobby
from services.play import play
from services.user import me
from utils.config import MAX_SCORE
from utils.my_unittest import UnitTest
from utils.sse_event import ppu, afr, rfr, df, cfr, du, rejfr, gs, lj, lup


class Test01_Friend(UnitTest):

    def test_001_friend(self):
        user1 = self.user([afr, ppu])
        user2 = self.user([rfr, ppu])

        self.assertFriendResponse(create_friendship(user1, user2))
        response = self.assertResponse(get_friends(user1), 200, count=1)
        self.assertEqual(response['results'][0]['friend']['username'], user2['username'])
        response = self.assertResponse(get_friends(user2), 200, count=1)
        self.assertEqual(response['results'][0]['friend']['username'], user1['username'])
        self.assertThread(user1, user2)

        user1 = self.user([rfr, ppu])
        user2 = self.user([afr, ppu])

        self.assertFriendResponse(create_friendship(user2, user1))
        response = self.assertResponse(get_friends(user1), 200, count=1)
        self.assertEqual(response['results'][0]['friend']['username'], user2['username'])
        response = self.assertResponse(get_friends(user2), 200, count=1)
        self.assertEqual(response['results'][0]['friend']['username'], user1['username'])
        self.assertThread(user1, user2)

    def test_002_friend_without_friend_request(self):
        user1 = self.user()

        self.assertResponse(friend_request('123456', user1), 404, {'detail': 'Friend request not found.'})
        self.assertThread(user1)

    def test_003_get_friends(self):
        user1 = self.user([afr, ppu, afr, afr, afr, afr, afr, afr])
        users = [self.user([rfr, ppu]) for _ in range(7)]

        for user_tmp in users:
            self.assertFriendResponse(create_friendship(user1, user_tmp))

        self.assertResponse(get_friends(user1), 200, count=7)
        self.assertThread(user1, *users)

    def test_004_get_friends_is_online(self):
        user1 = self.user([afr, ppu] + [afr] * 4)
        user2 = self.user([rfr, ppu])
        users_online = [self.user([rfr, ppu]) for _ in range(2)]
        users = [self.user([rfr, ppu]) for _ in range(2)]

        self.assertFriendResponse(create_friendship(user1, user2))
        for user_tmp in users:
            self.assertFriendResponse(create_friendship(user1, user_tmp))
        for user_tmp in users_online:
            self.assertFriendResponse(create_friendship(user1, user_tmp))

        self.assertThread(*users)
        time.sleep(5)
        self.assertResponse(get_friends(user1), 200, count=5)
        self.assertResponse(get_friends(user1, online='caca'), 200, count=5)
        self.assertResponse(get_friends(user1, online='true'), 200, count=3)
        self.assertThread(user2)
        time.sleep(5)
        self.assertResponse(get_friends(user1, online='true'), 200, count=2)
        self.assertResponse(get_friends(user1, online='false'), 200, count=3)
        self.assertThread(user1, *users_online)

    def test_005_friends_then_block(self):
        user1 = self.user([afr, ppu, df])
        user2 = self.user([rfr, ppu, df])

        self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(get_friends(user2), 200, count=1)

        self.assertResponse(blocked_user(user1, user2['id']), 201)

        for u in (user1, user2):
            self.assertResponse(get_friends(u), 200, count=0)
        self.assertThread(user1, user2)

    def test_006_delete_friend_user1(self):
        user1 = self.user([afr, ppu])
        user2 = self.user([rfr, ppu, df])

        friendship_id = self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(friend(user1, friendship_id), 200)
        self.assertResponse(friend(user1, friendship_id, 'DELETE'), 204)

        self.assertResponse(friend(user1, friendship_id), 404, {'detail': 'Friendship not found.'})
        self.assertResponse(get_friends(user2), 200, count=0)
        self.assertThread(user1, user2)

    def test_007_delete_friend_user2(self):
        user1 = self.user([afr, ppu, df])
        user2 = self.user([rfr, ppu])

        friendship_id = self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(friend(user1, friendship_id), 200)
        self.assertResponse(friend(user2, friendship_id, 'DELETE'), 204)

        self.assertResponse(friend(user2, friendship_id), 404, {'detail': 'Friendship not found.'})
        self.assertResponse(get_friends(user1), 200, count=0)
        self.assertThread(user1, user2)

    def test_008_delete_friend_not_belong_user(self):
        user1 = self.user([afr, ppu])
        user2 = self.user([rfr, ppu])
        user3 = self.user()

        friendship_id = self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(friend(user1, friendship_id), 200)

        self.assertResponse(friend(user3, friendship_id, 'DELETE'), 404, {'detail': 'Friendship not found.'})
        self.assertResponse(friend(user1, friendship_id), 200)
        self.assertThread(user1, user2, user3)

    def test_009_delete_friend_sse(self):
        user1 = self.user([afr, ppu, df, afr, df, afr, df])
        user2 = self.user([rfr, ppu])
        user3 = self.user([rfr, ppu, df])
        user4 = self.user([rfr, ppu, du])

        friendship_id = self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(friend(user2, friendship_id, 'DELETE'), 204)
        self.assertResponse(friend(user1, friendship_id), 404, {'detail': 'Friendship not found.'})

        friendship_id = self.assertFriendResponse(create_friendship(user1, user3))
        self.assertResponse(blocked_user(user3, user1['id']), 201)
        self.assertResponse(friend(user1, friendship_id), 404, {'detail': 'Friendship not found.'})

        friendship_id = self.assertFriendResponse(create_friendship(user1, user4))
        self.assertResponse(me(user4, 'DELETE', password=True), 204)
        self.assertResponse(friend(user1, friendship_id), 404, {'detail': 'Friendship not found.'})
        self.assertThread(user1, user2, user3, user4)


class Test02_FriendRequest(UnitTest):

    def test_001_friend_request(self):
        user1 = self.user()
        user2 = self.user([rfr])

        friend_request_id = self.assertResponse(friend_requests(user1, user2), 201, get_field=True)

        self.assertResponse(get_friend_requests_received(user2), 200, count=1)
        self.assertResponse(friend_requests(user1, method='GET'), 200, count=1)
        self.assertResponse(friend_request(friend_request_id, user1, method='GET'), 200)
        self.assertResponse(friend_request(friend_request_id, user2, method='GET'), 200)
        self.assertThread(user1, user2)

    def test_002_user_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(friend_requests(user1, {'username': 'caca'}), 404, {'detail': 'User not found.'})
        self.assertThread(user1)

    def test_003_already_request(self):
        user1 = self.user()
        user2 = self.user([rfr])

        self.assertResponse(friend_requests(user1, user2), 201)
        self.assertResponse(friend_requests(user1, user2), 409, {'detail': 'You have already sent a friend request to this user.'})
        self.assertResponse(friend_requests(user2, user1), 409, {'detail': 'You have already received a friend request from this user.'})
        self.assertThread(user1, user2)

    def test_004_already_friends(self):
        user1 = self.user([afr, ppu])
        user2 = self.user([rfr, ppu])

        self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(friend_requests(user1, user2), 409, {'detail': 'You are already friends with this user.'})
        self.assertThread(user1, user2)

    def test_005_send_friend_request_then_blocked(self):
        user1 = self.user([rejfr])
        user2 = self.user([rfr, cfr])

        self.assertResponse(friend_requests(user1, user2), 201)
        self.assertResponse(blocked_user(user2, user1['id']), 201)
        self.assertResponse(get_friend_requests_received(user2), 200, count=0)
        self.assertResponse(friend_requests(user1, method='GET'), 200, count=0)
        self.assertThread(user1, user2)

    def test_006_blocked_then_send_friend_request(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(blocked_user(user1, user2['id']), 201)
        self.assertResponse(friend_requests(user1, user2), 403, {'detail': 'You blocked this user.'})
        self.assertResponse(friend_requests(user2, user1), 404, {'detail': 'User not found.'})
        self.assertThread(user1, user2)

    def test_007_send_friend_request_to_myself(self):
        user1 = self.user()

        self.assertResponse(friend_requests(user1, user1), 403, {'detail': 'You cannot send a friend request to yourself.'})
        self.assertThread(user1)

    def test_008_forget_username_field(self):
        user1 = self.user()

        self.assertResponse(friend_requests(user1, data={}), 400, {'username': ['This field is required.']})
        self.assertThread(user1)

    def test_009_get_friend_request_not_belong(self):
        user1 = self.user()
        user2 = self.user([rfr])
        user3 = self.user()

        friend_request_id = self.assertResponse(friend_requests(user1, user2), 201, get_field=True)
        self.assertResponse(friend_request(friend_request_id, user3), 404, {'detail': 'Friend request not found.'})
        self.assertThread(user1, user2, user3)

    def test_010_reject_friend_request(self):
        user1 = self.user([rejfr, rejfr, rejfr])
        user2 = self.user([rfr])
        user3 = self.user([rfr, cfr])
        user4 = self.user([rfr, du])

        friend_request_id = self.assertResponse(friend_requests(user1, user2), 201, get_field=True)
        self.assertResponse(friend_request(friend_request_id, user2, 'DELETE'), 204)
        self.assertResponse(friend_request(friend_request_id, user1, 'GET'), 404, {'detail': 'Friend request not found.'})

        friend_request_id = self.assertResponse(friend_requests(user1, user3), 201, get_field=True)
        self.assertResponse(blocked_user(user3, user1['id']), 201)
        self.assertResponse(friend_request(friend_request_id, user1, 'GET'), 404, {'detail': 'Friend request not found.'})

        friend_request_id = self.assertResponse(friend_requests(user1, user4), 201, get_field=True)
        self.assertResponse(me(user4, 'DELETE', password=True), 204)
        self.assertResponse(friend_request(friend_request_id, user1, 'GET'), 404, {'detail': 'Friend request not found.'})

        self.assertThread(user1, user2, user3, user4)

    def test_011_cancel_friend_request(self):
        user1 = self.user([rfr, cfr, rfr, cfr, rfr, cfr])
        user2 = self.user()
        user3 = self.user([rejfr])
        user4 = self.user([du])

        friend_request_id = self.assertResponse(friend_requests(user2, user1), 201, get_field=True)
        self.assertResponse(friend_request(friend_request_id, user2, 'DELETE'), 204)
        self.assertResponse(friend_request(friend_request_id, user1, 'GET'), 404, {'detail': 'Friend request not found.'})
        self.assertResponse(friend_request(friend_request_id, user2, 'GET'), 404, {'detail': 'Friend request not found.'})

        friend_request_id = self.assertResponse(friend_requests(user3, user1), 201, get_field=True)
        self.assertResponse(blocked_user(user3, user1['id']), 201)
        self.assertResponse(friend_request(friend_request_id, user1, 'GET'), 404, {'detail': 'Friend request not found.'})
        self.assertResponse(friend_request(friend_request_id, user2, 'GET'), 404, {'detail': 'Friend request not found.'})

        friend_request_id = self.assertResponse(friend_requests(user4, user1), 201, get_field=True)
        self.assertResponse(me(user4, 'DELETE', password=True), 204)
        self.assertResponse(friend_request(friend_request_id, user1, 'GET'), 404, {'detail': 'Friend request not found.'})

        self.assertThread(user1, user2, user3, user4)

    def test_012_delete_friend_request_after_became_friend(self):
        user1 = self.user([afr, ppu])
        user2 = self.user([rfr, ppu])

        friend_request_id = self.assertResponse(friend_requests(user1, user2), 201, get_field=True)
        self.assertResponse(friend_request(friend_request_id, user2), 201, get_field=True)
        self.assertResponse(friend_request(friend_request_id, user1, 'GET'), 404, {'detail': 'Friend request not found.'})
        self.assertResponse(friend_request(friend_request_id, user2, 'GET'), 404, {'detail': 'Friend request not found.'})
        self.assertThread(user1, user2)

    def test_013_accept_own_send_friend_request(self):
        user1 = self.user()
        user2 = self.user([rfr])

        friend_request_id = self.assertResponse(friend_requests(user1, user2), 201, get_field=True)
        self.assertResponse(friend_request(friend_request_id, user1), 403, {'detail': 'You cannot accept your own friend request.'})
        self.assertThread(user1, user2)

    def test_014_guest_user_make_friend_request(self):
        user1 = self.user(guest=True)
        user2 = self.user()

        self.assertResponse(friend_requests(user1, user2), 403, {'detail': 'Guest users cannot perform this action.'})
        self.assertThread(user1, user2)

    def test_015_guest_user_receive_friend_request(self):
        user1 = self.user()
        user2 = self.user(guest=True)

        self.assertResponse(friend_requests(user1, user2), 404, {'detail': 'User not found.'})
        self.assertThread(user1, user2)

    def test_016_friend_request_receive(self):
        n = 4
        user1 = self.user([rfr] * (n + 1) + [cfr])
        user2 = self.user()
        users = [self.user() for _ in range(n)]

        self.assertEqual(0, self.assertResponse(me(user1), 200, get_field='notifications')['friend_requests'])

        friend_request_id = self.assertResponse(friend_requests(user2, user1), 201, get_field=True)
        for tmp_user in users:
            self.assertResponse(friend_requests(tmp_user, user1), 201)

        self.assertResponse(get_friend_requests_received(user2), 200)
        self.assertEqual(n + 1, self.assertResponse(me(user1), 200, get_field='notifications')['friend_requests'])
        self.assertResponse(friend_request(friend_request_id, user2, 'DELETE'), 204)
        self.assertEqual(n, self.assertResponse(me(user1), 200, get_field='notifications')['friend_requests'])
        self.assertResponse(get_friend_requests_received(user1), 200)
        self.assertEqual(0, self.assertResponse(me(user1), 200, get_field='notifications')['friend_requests'])
        self.assertThread(user1, user2, *users)

    def test_017_new_field(self):
        user1 = self.user([rfr])
        user2 = self.user()

        self.assertResponse(friend_requests(user2, user1), 201)
        response = self.assertResponse(get_friend_requests_received(user1), 200, get_field='results')
        self.assertIn('new', response[0])
        self.assertEqual(response[0]['new'], True)
        response = self.assertResponse(friend_requests(user2, method='GET'), 200, get_field='results')
        self.assertNotIn('new', response[0])
        self.assertThread(user1, user2)

    def test_018_no_friend_request(self):
        user1 = self.user()

        self.assertEqual(0, self.assertResponse(me(user1), 200, get_field='notifications')['friend_requests'])
        self.assertThread(user1)

    def test_019_friend_request_offline_then_connect_when_cancel_friend_request(self):
        user1 = self.user(sse=False)
        user2 = self.user()

        friend_request_id = self.assertResponse(friend_requests(user2, user1), 201, get_field=True)
        self.connect_to_sse(user1, [cfr])
        self.assertEqual(1, self.assertResponse(me(user1), 200, get_field='notifications')['friend_requests'])
        self.assertResponse(friend_request(friend_request_id, user2, method='DELETE'), 204)
        self.assertThread(user1, user2)


class Test03_FriendStat(UnitTest):

    def test_001_play_against_duel(self):
        user1 = self.user([afr, ppu, gs])
        user2 = self.user([rfr, ppu, gs])

        self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(play(user1), 201)
        self.assertResponse(play(user2), 201)

        self.assertResponse(score(user2['id']), 200)
        for _ in range(MAX_SCORE):
            self.assertResponse(score(user1['id']), 200)

        response = self.assertResponse(get_friends(user1), 200, count=1)
        self.assertEqual(response['results'][0]['matches_played_against'], 1)
        self.assertEqual(response['results'][0]['me_wins'], 1)
        response = self.assertResponse(get_friends(user2), 200, count=1)
        self.assertEqual(response['results'][0]['matches_played_against'], 1)
        self.assertEqual(response['results'][0]['me_wins'], 0)
        self.assertThread(user1, user2)

    def test_002_play_against_lobby(self):
        user1 = self.user([afr, ppu, lj, lj, lup, lup, gs])
        user2 = self.user([lj, lup, lup, gs])
        user3 = self.user([lup, lup, gs])
        user4 = self.user([rfr, ppu, gs])
        user5 = self.user([lj, lup, gs])
        user6 = self.user([lup, gs])

        self.assertFriendResponse(create_friendship(user1, user4))

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(join_lobby(user1, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user2, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user3, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user4), 201, get_field='code')
        self.assertResponse(join_lobby(user4, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user5), 201, get_field='code')
        self.assertResponse(join_lobby(user6, code), 201)
        self.assertResponse(join_lobby(user5, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user6, code, data={'is_ready': True}), 200)

        self.assertResponse(score(user4['id']), 200)
        self.assertResponse(score(user6['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user1['id']), 200)

        response = self.assertResponse(get_friends(user1), 200, count=1)
        self.assertEqual(response['results'][0]['matches_played_against'], 1)
        self.assertEqual(response['results'][0]['me_wins'], 1)
        response = self.assertResponse(get_friends(user4), 200, count=1)
        self.assertEqual(response['results'][0]['matches_played_against'], 1)
        self.assertEqual(response['results'][0]['me_wins'], 0)
        self.assertThread(user1, user2, user3, user4, user5, user6)

    def test_003_play_together(self):
        user1 = self.user([afr, ppu, lj, lj, lup, lup, gs])
        user2 = self.user([rfr, ppu, lj, lup, lup, gs])
        user3 = self.user([lup, lup, gs])
        user4 = self.user([gs])
        user5 = self.user([afr, ppu, lj, lup, gs])
        user6 = self.user([rfr, ppu, lup, gs])

        self.assertFriendResponse(create_friendship(user1, user2))
        self.assertFriendResponse(create_friendship(user5, user6))

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(join_lobby(user1, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user2, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user3, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user4), 201, get_field='code')
        self.assertResponse(join_lobby(user4, code, data={'is_ready': True}), 200)

        code = self.assertResponse(create_lobby(user5), 201, get_field='code')
        self.assertResponse(join_lobby(user6, code), 201)
        self.assertResponse(join_lobby(user5, code, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user6, code, data={'is_ready': True}), 200)

        self.assertResponse(score(user4['id']), 200)
        self.assertResponse(score(user6['id']), 200)
        self.assertResponse(score(user3['id']), 200)
        for _ in range(MAX_SCORE - 1):
            self.assertResponse(score(user1['id']), 200)

        response = self.assertResponse(get_friends(user1), 200, count=1)
        self.assertEqual(response['results'][0]['matches_played_together'], 1)
        self.assertEqual(response['results'][0]['matches_won_together'], 1)
        response = self.assertResponse(get_friends(user2), 200, count=1)
        self.assertEqual(response['results'][0]['matches_played_together'], 1)
        self.assertEqual(response['results'][0]['matches_won_together'], 1)

        response = self.assertResponse(get_friends(user5), 200, count=1)
        self.assertEqual(response['results'][0]['matches_played_together'], 1)
        self.assertEqual(response['results'][0]['matches_won_together'], 0)
        response = self.assertResponse(get_friends(user6), 200, count=1)
        self.assertEqual(response['results'][0]['matches_played_together'], 1)
        self.assertEqual(response['results'][0]['matches_won_together'], 0)
        self.assertThread(user1, user2, user3, user4, user5, user6)


if __name__ == '__main__':
    unittest.main()
