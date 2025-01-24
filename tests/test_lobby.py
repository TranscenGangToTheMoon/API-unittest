import time
import unittest

from services.blocked import blocked_user, unblocked_user
from services.friend import create_friendship
from services.game import score
from services.lobby import create_lobby, join_lobby, ban_user, invite_user, post_message
from utils.my_unittest import UnitTest


class Test01_JoinLobby(UnitTest):

    def test_001_create_lobby(self):
        user1 = self.user()

        self.assertResponse(create_lobby(user1), 201)
        self.assertThread(user1)

    def test_002_join_lobby(self):
        user1 = self.user(['lobby-join', 'lobby-join'])
        user2 = self.user(['lobby-join'])
        user3 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertThread(user1, user2, user3)

    def test_003_join_two_lobby(self):
        user1 = self.user(['lobby-join', 'lobby-leave'])
        user2 = self.user()
        user3 = self.user(['lobby-join'])

        code1 = self.assertResponse(create_lobby(user1), 201, get_field='code')
        code2 = self.assertResponse(create_lobby(user3), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code1), 201)
        self.assertResponse(join_lobby(user2, code1, method='DELETE'), 204)
        self.assertResponse(join_lobby(user2, code2), 201)
        self.assertThread(user1, user2, user3)


class Test02_ErrorJoinLobby(UnitTest):

    def test_001_lobby_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(join_lobby(user1, '123456'), 404, {'detail': 'Lobby not found.'})
        self.assertThread(user1)

    def test_002_already_join(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user1, code), 409, {'detail': 'You already joined this lobby.'})
        self.assertResponse(join_lobby(user2, code), 409, {'detail': 'You already joined this lobby.'})
        self.assertThread(user1, user2)

    def test_003_lobby_is_full(self):
        user1 = self.user(['lobby-join', 'lobby-join'])
        user2 = self.user(['lobby-join'])
        user3 = self.user()
        user4 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(join_lobby(user4, code), 403, {'detail': 'Lobby is full.'})
        self.assertThread(user1, user2, user3, user4)

    def test_004_guest_create_lobby(self):
        user1 = self.user(guest=True)

        self.assertResponse(create_lobby(user1), 403, {'detail': 'Guest users cannot perform this action.'})
        self.assertThread(user1)

    def test_005_invalid_game_mode(self):
        user1 = self.user()

        self.assertResponse(create_lobby(user1, game_mode='sdfsdf'), 400, {'game_mode': ["Game mode must be 'clash' or 'custom_game'."]})
        self.assertThread(user1)

    def test_006_no_game_mode(self):
        user1 = self.user()

        self.assertResponse(create_lobby(user1, data={}), 400, {'game_mode': ['This field is required.']})
        self.assertThread(user1)

    def test_007_blocked_user_cannot_join(self):
        user1 = self.user()
        users = [self.user() for _ in range(30)]

        for u in users:
            self.assertResponse(blocked_user(user1, u['id']), 201)

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        for u in users:
            self.assertResponse(join_lobby(u, code), 404, {'detail': 'Lobby not found.'})
        self.assertThread(user1, *users)

    def test_008_blocked_user(self):
        user1 = self.user(['lobby-join', 'lobby-leave'])
        user2 = self.user(['lobby-banned'])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(blocked_user(user1, user2['id']), 201)

        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        self.assertEqual(1, len(response))

        self.assertResponse(create_lobby(user2, method='GET'), 404, {'detail': 'You do not belong to any lobby.'})
        self.assertResponse(join_lobby(user2, code), 404, {'detail': 'Lobby not found.'})
        self.assertThread(user1, user2)

    def test_009_blocked_user_not_creator(self):
        user1 = self.user(['lobby-join', 'lobby-join'])
        user2 = self.user(['lobby-join'])
        user3 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(blocked_user(user2, user3['id']), 201)

        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        self.assertEqual(3, len(response))
        self.assertThread(user1, user2, user3)

    def test_010_blocked_then_unblock(self):
        user1 = self.user(['lobby-join', 'lobby-leave', 'lobby-join'])
        user2 = self.user(['lobby-banned'])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        blocked_id = self.assertResponse(blocked_user(user1, user2['id']), 201, get_field=True)

        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        self.assertEqual(1, len(response))

        self.assertResponse(join_lobby(user2, code), 404, {'detail': 'Lobby not found.'})
        self.assertResponse(unblocked_user(user1, blocked_id), 204)
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertThread(user1, user2)

    def test_011_join_lobby_without_sse(self):
        user1 = self.user(sse=False)
        user2 = self.user()

        self.assertResponse(create_lobby(user1), 401, {'code': 'sse_connection_required', 'detail': 'You need to be connected to SSE to access this resource.'})
        code = self.assertResponse(create_lobby(user2), 201, get_field='code')
        self.assertResponse(join_lobby(user1, code), 401, {'code': 'sse_connection_required', 'detail': 'You need to be connected to SSE to access this resource.'})
        self.assertThread(user2)

    def test_012_user_blocked_creator(self):
        user1 = self.user(['lobby-join', 'lobby-join', 'lobby-leave'])
        user2 = self.user(['lobby-join', 'lobby-leave'])
        user3 = self.user(['lobby-banned'])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(blocked_user(user3, user1['id']), 201)
        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        self.assertEqual(2, len(response))
        self.assertThread(user1, user2, user3)


class Test03_BanLobby(UnitTest):

    def test_001_ban_lobby(self):
        user1 = self.user(['lobby-join', 'lobby-leave'])
        user2 = self.user(['lobby-banned'])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(ban_user(user1, user2, code), 204)

        self.assertResponse(join_lobby(user2, code), 404, {'detail': 'Lobby not found.'})
        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        self.assertEqual(1, len(response))
        self.assertThread(user1, user2)

    def test_002_user_ban_not_join_lobby(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(ban_user(user1, user2, code), 404, {'detail': 'This user does not belong to this lobby.'})
        self.assertThread(user1, user2)

    def test_003_user_banned_not_join_lobby(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(ban_user(user1, user2, code), 404, {'detail': 'This user does not belong to this lobby.'})
        self.assertThread(user1, user2)

    def test_004_invalid_lobby(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(ban_user(user1, user2, '123456'), 403, {'detail': 'You do not belong to this lobby.'})
        self.assertThread(user1, user2)

    def test_005_not_creator(self):
        user1 = self.user(['lobby-join', 'lobby-join'])
        user2 = self.user(['lobby-join'])
        user3 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(ban_user(user2, user3, code), 403, {'detail': 'Only creator can update this lobby.'})
        self.assertThread(user1, user2, user3)

    def test_006_users_does_exist(self):
        user1 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(ban_user(user1, {'id': 123456789}, code), 404, {'detail': 'This user does not belong to this lobby.'})
        self.assertThread(user1)


class Test04_UpdateLobby(UnitTest):

    def test_001_update_lobby(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user(['lobby-update'])

        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertEqual('3v3', self.assertResponse(create_lobby(user1, {'match_type': '3v3'}, 'PATCH'), 200, get_field='match_type'))
        self.assertThread(user1, user2)

    def test_002_invalid_match_type(self):
        user1 = self.user()

        self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201)
        self.assertResponse(create_lobby(user1, data={'match_type': 42}, method='PATCH'), 400, {'match_type': ["Match type must be '1v1' or '3v3'."]})
        self.assertResponse(create_lobby(user1, data={'match_type': 'cac'}, method='PATCH'), 400, {'match_type': ["Match type must be '1v1' or '3v3'."]})
        self.assertThread(user1)

    def test_003_update_not_creator(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(create_lobby(user2, data={'match_type': '3v3'}, method='PATCH'), 403, {'detail': 'Only creator can update this lobby.'})
        self.assertThread(user1, user2)

    def test_004_update_clash(self):
        user1 = self.user()

        self.assertResponse(create_lobby(user1), 201)
        self.assertResponse(create_lobby(user1, data={'match_type': '3v3'}, method='PATCH'), 403, {'detail': 'You cannot update clash lobby.'})
        self.assertThread(user1)

    def test_005_update_game_mode(self):
        user1 = self.user()

        self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201)
        self.assertResponse(create_lobby(user1, method='PATCH'), 403, {'detail': 'You cannot update game mode.'})
        self.assertThread(user1)

    def test_006_update_match_type_when_full(self):
        users = {}
        teams = ['Team A', 'Team A', 'Team A', 'Team B', 'Team B', 'Team B']
        after_teams = ['Team A', 'Spectator', 'Spectator', 'Team B', 'Spectator', 'Spectator']
        for i in range(6):
            response = self.user((['lobby-join'] * (5 - i)) + (['lobby-update-participant'] * 4) + (['lobby-update'] * int(bool(i))))
            response['team'] = teams[i]
            response['after_team'] = after_teams[i]
            users[response['id']] = response
        user1 = list(users.values())[0]

        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')
        response = self.assertResponse(create_lobby(user1, data={'match_type': '3v3'}, method='PATCH'), 200)
        self.assertEqual('3v3', response['match_type'])

        for u in list(users.values())[1:]:
            self.assertResponse(join_lobby(u, code), 201)

        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        for user in response:
            self.assertEqual(user['team'], users[user['id']]['team'])

        response = self.assertResponse(create_lobby(user1, data={'match_type': '1v1'}, method='PATCH'), 200)
        self.assertEqual('1v1', response['match_type'])

        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        for user in response:
            self.assertEqual(user['team'], users[user['id']]['after_team'])
        self.assertThread(*users.values())


class Test05_UpdateParticipantLobby(UnitTest):

    def test_001_set_ready_to_true(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user(['lobby-update-participant'])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertTrue(self.assertResponse(join_lobby(user1, code, data={'is_ready': True}), 200, get_field='is_ready'))
        self.assertThread(user1, user2)

    def test_002_change_team(self):
        user1 = self.user()

        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')

        response = self.assertResponse(join_lobby(user1, code, data={'team': 'Team B'}), 200)
        self.assertEqual('Team B', response['team'])

        response = self.assertResponse(join_lobby(user1, code, data={'team': 'Spectator'}), 200)
        self.assertEqual('Spectator', response['team'])
        self.assertThread(user1)

    def test_003_change_invalid_team(self):
        user1 = self.user()

        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')
        self.assertResponse(join_lobby(user1, code, data={'team': 'Team caca'}), 400, {'team': ["Match type must be 'Team A', 'Team B' or 'Spectator'."]})
        self.assertThread(user1)

    def test_004_change_team_already_in(self):
        user1 = self.user()

        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')
        self.assertResponse(join_lobby(user1, code, data={'team': 'Team A'}), 409, {'detail': 'You are already in this team.'})
        self.assertThread(user1)

    def test_005_change_team_full(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user2, code, method='PATCH', data={'team': 'Team A'}), 403, {'detail': 'Team is full.'})
        self.assertThread(user1, user2)


class Test06_LeaveLobby(UnitTest):

    def test_001_leave_lobby(self):
        user1 = self.user(['lobby-join', 'lobby-join', 'lobby-leave', 'lobby-leave'])
        user2 = self.user(['lobby-join', 'lobby-leave'])
        user3 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)

        self.assertResponse(join_lobby(user3, code, 'DELETE'), 204)
        self.assertResponse(join_lobby(user2, code, 'DELETE'), 204)
        self.assertResponse(join_lobby(user1, code, 'DELETE'), 204)
        self.assertResponse(join_lobby(user1, code, 'GET'), 403, {'detail': 'You do not belong to this lobby.'})
        self.assertResponse(create_lobby(user1, method='GET'), 404, {'detail': 'You do not belong to any lobby.'})
        self.assertThread(user1, user2, user3)

    def test_002_leave_lobby_then_other_member_became_creator(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user(['lobby-leave', 'lobby-update-participant'])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user1, code, 'DELETE'), 204)

        response = self.assertResponse(join_lobby(user2, code, 'GET'), 200)
        self.assertEqual(1, len(response))
        self.assertTrue(response[0]['creator'])
        self.assertThread(user1, user2)

    def test_003_guest_join_leave_lobby_then_destroy_lobby(self):
        user1 = self.user(['lobby-join', 'lobby-join'])
        user2 = self.user(['lobby-join', 'lobby-leave', 'lobby-destroy'], guest=True)
        user3 = self.user(['lobby-leave', 'lobby-destroy'], guest=True)

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(join_lobby(user1, code, 'DELETE'), 204)
        self.assertResponse(join_lobby(user2, code, 'GET'), 403, {'detail': 'You do not belong to this lobby.'})
        self.assertResponse(join_lobby(user3, code, 'GET'), 403, {'detail': 'You do not belong to this lobby.'})
        self.assertResponse(create_lobby(user2, method='GET'), 404, {'detail': 'You do not belong to any lobby.'})
        self.assertResponse(create_lobby(user3, method='GET'), 404, {'detail': 'You do not belong to any lobby.'})
        self.assertThread(user1, user2, user3)

    def test_004_leave_lobby_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(join_lobby(user1, '123456', method='DELETE'), 403, {'detail': 'You do not belong to this lobby.'})
        self.assertThread(user1)

    def test_005_leave_lobby_does_not_join(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code, 'DELETE'), 403, {'detail': 'You do not belong to this lobby.'})
        self.assertThread(user1, user2)

    def test_006_leave_lobby_not_creator(self):
        user1 = self.user(['lobby-join', 'lobby-leave'])
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user2, code, 'DELETE'), 204)

        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        self.assertEqual(1, len(response))
        self.assertThread(user1, user2)


class Test07_GetLobby(UnitTest):

    def test_001_get_lobby(self):
        user1 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        response = self.assertResponse(create_lobby(user1, method='GET'), 200)
        self.assertEqual(code, response['code'])
        self.assertThread(user1)

    def test_002_get_lobby_does_not_join(self):
        user1 = self.user()

        self.assertResponse(create_lobby(user1, method='GET'), 404, {'detail': 'You do not belong to any lobby.'})
        self.assertThread(user1)

    def test_002_get_lobby_participant(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code), 201)

        response = self.assertResponse(join_lobby(user1, code, 'GET'), 200)
        self.assertEqual(2, len(response))
        self.assertThread(user1, user2)

    def test_003_get_lobby_participant_does_not_join(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')

        self.assertResponse(join_lobby(user2, code, 'GET'), 403, {'detail': 'You do not belong to this lobby.'})
        self.assertThread(user1, user2)


class Test08_InviteLobby(UnitTest):

    def test_001_invite_clash(self):
        user1 = self.user(['accept-friend-request'])
        user2 = self.user(['receive-friend-request', 'invite-clash'])

        self.assertFriendResponse(create_friendship(user1, user2))
        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(invite_user(user1, user2, code), 204)
        self.assertThread(user1, user2)

    def test_002_invite_custom_1v1(self):
        user1 = self.user(['accept-friend-request'])
        user2 = self.user(['receive-friend-request', 'invite-1v1'])

        self.assertFriendResponse(create_friendship(user1, user2))
        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')
        self.assertResponse(invite_user(user1, user2, code), 204)
        self.assertThread(user1, user2)

    def test_003_invite_custom_3v3(self):
        user1 = self.user(['accept-friend-request'])
        user2 = self.user(['receive-friend-request', 'invite-3v3'])

        self.assertFriendResponse(create_friendship(user1, user2))
        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')
        self.assertResponse(create_lobby(user1, {'match_type': '3v3'}, method='PATCH'), 200)
        self.assertResponse(invite_user(user1, user2, code), 204)
        self.assertThread(user1, user2)

    def test_004_invite_yourself(self):
        user1 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(invite_user(user1, user1, code), 403, {'detail': 'You cannot invite yourself.'})
        self.assertThread(user1)

    def test_005_not_friend(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(invite_user(user1, user2, code), 403, {'detail': 'You can only invite friends.'})
        self.assertThread(user1, user2)

    def test_006_not_creator(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user()
        user3 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(invite_user(user2, user3, code), 403, {'detail': 'Only creator can update this lobby.'})
        self.assertThread(user1, user2, user3)

    def test_007_user_already_in_lobby(self):
        user1 = self.user(['lobby-join'])
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(invite_user(user1, user2, code), 409, {'detail': 'This user is already in this lobby.'})
        self.assertThread(user1, user2)

    def test_008_not_in_lobby(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(invite_user(user2, user3, code), 403, {'detail': 'You do not belong to this lobby.'})
        self.assertThread(user1, user2, user3)


class Test09_Message(UnitTest):

    def test_001_test(self):
        user1 = self.user(['lobby-join', 'lobby-join', 'lobby-message', 'lobby-leave'])
        user2 = self.user(['lobby-join', 'lobby-message', 'lobby-leave', 'lobby-message'])
        user3 = self.user([])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertResponse(join_lobby(user3, code), 201)
        self.assertResponse(post_message(user3, code, '    coucou    '), 201)
        self.assertResponse(join_lobby(user3, code, method='DELETE'), 204)
        self.assertResponse(post_message(user3, code, 'coucou failed'), 403)
        self.assertResponse(post_message(user1, code, 'blip blop'), 201)
        self.assertThread(user1, user2, user3)

    def test_002_not_in_lobby(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(post_message(user2, code, 'blip blop'), 403)
        self.assertThread(user1, user2)

    def test_003_lobby_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(post_message(user1, '1234', 'blip blop'), 403)
        self.assertThread(user1)

    def test_004_validation_error(self):
        user1 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(post_message(user1, code), 400)
        self.assertResponse(post_message(user1, code, data={'content': ['caca', 'pipi']}), 400)
        self.assertResponse(post_message(user1, code, data={'content': {'prout': 48}}), 400)
        self.assertThread(user1)


class Test10_FinishMatch(UnitTest):

    def test_001_is_playing(self):
        user1 = self.user(['lobby-join', 'lobby-update-participant', 'game-start'])
        user2 = self.user(['lobby-update-participant', 'game-start'])

        code = self.assertResponse(create_lobby(user1, game_mode='custom_game'), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)

        self.assertResponse(join_lobby(user1, code, data={'is_ready': True}), 200)
        self.assertFalse(self.assertResponse(create_lobby(user1, method='GET'), 200, get_field='is_playing'))
        self.assertResponse(join_lobby(user2, code, data={'is_ready': True}), 200)

        time.sleep(2)

        self.assertResponse(score(user1['id']), 200)
        self.assertTrue(self.assertResponse(create_lobby(user1, method='GET'), 200, get_field='is_playing'))
        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user1['id']), 200)

        self.assertFalse(self.assertResponse(create_lobby(user1, method='GET'), 200, get_field='is_playing'))
        self.assertThread(user1, user2)

    def test_002_is_playing_from_different_lobby(self):
        user1 = self.user(['lobby-join', 'lobby-update-participant', 'game-start'])
        user2 = self.user(['lobby-update-participant', 'game-start'])
        user3 = self.user(['game-start'])
        user4 = self.user(['lobby-join', 'lobby-join', 'lobby-update-participant', 'lobby-update-participant', 'game-start'])
        user5 = self.user(['lobby-join', 'lobby-update-participant', 'lobby-update-participant', 'game-start'])
        user6 = self.user(['lobby-update-participant', 'lobby-update-participant', 'game-start'])

        code1 = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code1), 201)

        code2 = self.assertResponse(create_lobby(user3), 201, get_field='code')

        code3 = self.assertResponse(create_lobby(user4), 201, get_field='code')
        self.assertResponse(join_lobby(user5, code3), 201)
        self.assertResponse(join_lobby(user6, code3), 201)

        self.assertResponse(join_lobby(user1, code1, data={'is_ready': True}), 200)
        self.assertFalse(self.assertResponse(create_lobby(user1, method='GET'), 200, get_field='is_playing'))
        self.assertResponse(join_lobby(user2, code1, data={'is_ready': True}), 200)

        self.assertFalse(self.assertResponse(create_lobby(user3, method='GET'), 200, get_field='is_playing'))
        self.assertResponse(join_lobby(user3, code2, data={'is_ready': True}), 200)

        self.assertResponse(join_lobby(user4, code3, data={'is_ready': True}), 200)
        self.assertResponse(join_lobby(user5, code3, data={'is_ready': True}), 200)
        self.assertFalse(self.assertResponse(create_lobby(user4, method='GET'), 200, get_field='is_playing'))
        self.assertResponse(join_lobby(user6, code3, data={'is_ready': True}), 200)

        time.sleep(2)

        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user1['id']), 200)
        self.assertResponse(score(user1['id']), 200)

        self.assertFalse(self.assertResponse(create_lobby(user1, method='GET'), 200, get_field='is_playing'))
        self.assertFalse(self.assertResponse(create_lobby(user3, method='GET'), 200, get_field='is_playing'))
        self.assertFalse(self.assertResponse(create_lobby(user5, method='GET'), 200, get_field='is_playing'))
        self.assertThread(user1, user2, user3, user4, user5, user6)


if __name__ == '__main__':
    unittest.main()
