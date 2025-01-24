import time
import unittest

from services.auth import login
from services.blocked import blocked_user
from services.chat import create_chat, accept_chat, request_chat_id, create_message
from services.friend import friend_requests, get_friend_requests_received, create_friendship, friend, get_friends, \
    friend_request
from services.game import create_game, is_in_game, score
from services.lobby import create_lobby, join_lobby
from services.play import play
from services.tournament import create_tournament, search_tournament, join_tournament
from services.user import get_user, me, get_chat_data, get_data, get_game_data
from utils.generate_random import rnstr
from utils.my_unittest import UnitTest


# TODO fguirama: test update user
# TODO fguirama: test get friend field
# TODO fguirama: test get status field


class Test01_GetUsers(UnitTest):

    def test_001_get_user(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(get_user(user1, user2['id']), 200)
        self.assertThread(user1, user2)

    def test_002_get_blocked_by_user(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(blocked_user(user2, user1['id']), 201)
        self.assertResponse(get_user(user1, user2['id']), 404, {'detail': 'User not found.'})
        self.assertThread(user1, user2)

    def test_003_get_blocked_user(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(blocked_user(user1, user2['id']), 201)
        self.assertResponse(get_user(user1, user2['id']), 403, {'detail': 'You blocked this user.'})
        self.assertThread(user1, user2)

    def test_004_get_user_doest_not_exist(self):
        user1 = self.user()

        self.assertResponse(get_user(user1, user2_id=123456), 404, {'detail': 'User not found.'})
        self.assertThread(user1)


class Test02_UserMe(UnitTest):

    def test_001_get_me(self):
        user1 = self.user()

        response = self.assertResponse(me(user1), 200)
        last_online = response['last_online']
        self.assertDictEqual(response, {'id': response['id'], 'username': user1['username'], 'is_guest': False, 'created_at': response['created_at'], 'profile_picture': None, 'accept_friend_request': True, 'accept_chat_from': 'friends_only', 'trophies': 0, 'notifications': {'friend_requests': 0, 'chats': 0}, 'is_online': True, 'last_online': response['last_online']})
        self.assertThread(user1)
        time.sleep(5)
        self.assertNotEqual(last_online, self.assertResponse(me(user1), 200)['last_online'])

    def test_002_get_me_guest(self):
        user1 = self.user(guest=True)

        response = self.assertResponse(me(user1), 200)
        self.assertDictEqual(response, {'id': response['id'], 'username': response['username'], 'is_guest': True, 'created_at': response['created_at'], 'profile_picture': None, 'accept_friend_request': True, 'accept_chat_from': 'friends_only', 'trophies': 0, 'notifications': {'friend_requests': 0, 'chats': 0}, 'is_online': True, 'last_online': response['last_online']})
        self.assertThread(user1)


class Test03_DeleteUser(UnitTest):

    def test_001_delete(self):
        user1 = self.user()

        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(me(user1), 401, {'code': 'user_not_found', 'detail': 'User not found.'})
        self.assertThread(user1)

    def test_002_delete_not_get_me(self):
        user1 = self.user()

        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(me(user1), 401, {'code': 'user_not_found', 'detail': 'User not found.'})
        self.assertThread(user1)

    def test_003_already_delete(self):
        user1 = self.user()

        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(me(user1, method='DELETE', password=True), 401, {'code': 'user_not_found', 'detail': 'User not found.'})
        self.assertThread(user1)

    def test_004_request_after_delete(self):
        user1 = self.user()

        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(create_lobby(user1), 401, {'code': 'user_not_found', 'detail': 'User not found.'})
        self.assertThread(user1)

    def test_005_user_in_lobby(self):
        user1 = self.user()
        user2 = self.user()

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(create_lobby(user1, method='GET'), 401, {'code': 'user_not_found', 'detail': 'User not found.'})
        self.assertResponse(join_lobby(user2, code), 404, {'detail': 'Lobby not found.'})
        self.assertThread(user1, user2)

    def test_006_user_in_game(self):
        user1 = self.user(['game-start'])
        user2 = self.user(['game-start'])

        self.assertResponse(create_game(user1, user2), 201)
        time.sleep(1)
        self.assertResponse(me(user1, method='DELETE', password=True), 403)
        self.assertThread(user1, user2)

    def test_007_user_in_tournament(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()
        name = rnstr()

        code = self.assertResponse(create_tournament(user1, {'name': 'Delete User ' + name}), 201, get_field='code')
        self.assertResponse(search_tournament(user2, name), 200, count=1)
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(create_tournament(user1, method='GET'), 401, {'code': 'user_not_found', 'detail': 'User not found.'})
        self.assertResponse(search_tournament(user2, name), 200, count=0)
        self.assertResponse(join_tournament(user3, code), 404)
        self.assertThread(user1, user2, user3)

    def test_008_user_in_start_tournament(self):
        user1 = self.user(['tournament-join'])
        user2 = self.user(['tournament-leave'])
        user3 = self.user()
        name = rnstr()

        code = self.assertResponse(create_tournament(user1, {'name': 'Delete User ' + name}), 201, get_field='code')
        self.assertResponse(join_tournament(user2, code), 201)
        response = self.assertResponse(search_tournament(user3, name), 200, count=1)
        self.assertEqual(2, response['results'][0]['n_participants'])
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        response = self.assertResponse(search_tournament(user3, name), 200, count=1)
        self.assertEqual(1, response['results'][0]['n_participants'])
        # TODO fguirama: make when tournament work
        self.assertThread(user1, user2, user3)

    def test_009_chat_with(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(accept_chat(user2), 200)
        chat_id = self.assertResponse(create_chat(user1, user2['username']), 201, get_field=True)
        self.assertResponse(request_chat_id(user2, chat_id), 200)
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(request_chat_id(user2, chat_id), 403, {'detail': 'You do not belong to this chat.'})
        self.assertThread(user1, user2)

    def test_010_play_duel(self):
        user2 = self.user()

        while True:
            user1 = self.user()

            self.assertResponse(play(user1), 201)
            time.sleep(1)
            response = is_in_game(user1)
            if response.status_code == 404:
                break
            user1['thread_tests'] = ['game-start']
            self.assertThread(user1)
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(play(user2), 201)
        time.sleep(1)
        self.assertResponse(is_in_game(user2), 404, {'detail': 'You do not belong to any game.'})
        self.assertThread(user1, user2)

    def test_012_play_ranked(self):
        user2 = self.user()

        while True:
            user1 = self.user()

            self.assertResponse(play(user1, 'ranked'), 201)
            time.sleep(1)
            response = is_in_game(user1)
            if response.status_code == 404:
                break
            self.assertThread(user1)
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(play(user2, 'ranked'), 201)
        time.sleep(1)
        self.assertResponse(is_in_game(user2), 404, {'detail': 'You do not belong to any game.'})
        self.assertThread(user1, user2)

    def test_013_friend_request(self):
        user1 = self.user()
        user2 = self.user(['receive-friend-request', 'cancel-friend-request'])

        friend_request_id = self.assertResponse(friend_requests(user1, user2), 201, get_field=True)
        self.assertResponse(get_friend_requests_received(user2), 200, count=1)
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(friend_request(friend_request_id, user2, 'GET'), 404)
        self.assertResponse(get_friend_requests_received(user2), 200, count=0)
        self.assertThread(user1, user2)

    def test_014_friend(self):
        user1 = self.user(['accept-friend-request', 'accept-friend-request'])
        user2 = self.user(['receive-friend-request', 'delete-friend'])
        user3 = self.user(['receive-friend-request', 'delete-friend'])

        id = self.assertFriendResponse(create_friendship(user1, user2))
        self.assertFriendResponse(create_friendship(user1, user3))
        self.assertResponse(friend(user2, id), 200)
        self.assertResponse(get_friends(user1), 200, count=2)
        self.assertResponse(get_friends(user2), 200, count=1)
        self.assertResponse(get_friends(user3), 200, count=1)
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(friend(user2, id), 404, {'detail': 'Friendship not found.'})
        self.assertResponse(get_friends(user2), 200, count=0)
        self.assertResponse(get_friends(user3), 200, count=0)
        self.assertThread(user1, user2, user3)

    def test_015_blocked(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(blocked_user(user2, user1['id']), 201)
        self.assertResponse(blocked_user(user2, user1['id'], method='GET'), 200, count=1)
        self.assertResponse(me(user1, method='DELETE', password=True), 204)
        self.assertResponse(blocked_user(user2, user1['id'], method='GET'), 200, count=0)
        self.assertThread(user1, user2)


class Test04_UpdateUserMe(UnitTest):

    def test_001_update_password(self):
        user1 = self.user()
        old_password = user1['password']

        self.assertResponse(me(user1, method='PATCH', data={'password': 'new_password', 'old_password': old_password}), 200)
        self.assertResponse(login(user1['username'], 'new_password'), 200)
        self.assertResponse(login(user1['username'], old_password), 401, {'detail': 'No active account found with the given credentials'})
        self.assertThread(user1)

    def test_002_update_password_same_as_before(self):
        user1 = self.user()

        self.assertResponse(me(user1, method='PATCH', data={'password': user1['password'], 'old_password': user1['password']}), 400, {'password': ['Password is the same as the old one.']})
        self.assertResponse(login(data=user1), 200)
        self.assertThread(user1)

    def test_003_update_password_error_old_password(self):
        user1 = self.user()
        new_password = 'new-' + rnstr(10)

        self.assertResponse(me(user1, method='PATCH', data={'password': new_password}), 400, {'old_password': ['Password confirmation is required.']})
        self.assertResponse(me(user1, method='PATCH', data={'password': new_password, 'old_password': 'caca'}), 400, {'old_password': ['Incorrect password.']})
        self.assertResponse(login(data=user1), 200)
        self.assertThread(user1)


class Test05_RenameUser(UnitTest):

    def test_001_rename_user(self):
        user1 = self.user()
        old_username = user1['username']
        new_username = old_username + '_new'

        self.assertResponse(me(user1, method='PATCH', data={'username': new_username}), 200)
        self.assertResponse(login(new_username, user1['password']), 200)
        self.assertResponse(login(old_username, user1['password']), 401, {'detail': 'No active account found with the given credentials'})
        self.assertThread(user1)

    def test_002_rename_user_friend(self):
        user1 = self.user(['accept-friend-request'])
        user2 = self.user(['receive-friend-request'])
        new_username = user1['username'] + '_new'

        id = self.assertFriendResponse(create_friendship(user1, user2))
        user1['id'] = self.assertResponse(me(user1, method='PATCH', data={'username': new_username}), 200, get_field=True)
        response = self.assertResponse(friend(user2, id), 200)
        self.assertEqual(new_username, response['friend']['username'])
        self.assertThread(user1, user2)

    def test_003_rename_blocked_user(self):
        user1 = self.user()
        user2 = self.user()
        new_username = user1['username'] + '_new'

        self.assertResponse(blocked_user(user2, user1['id']), 201)
        self.assertResponse(me(user1, method='PATCH', data={'username': new_username}), 200)

        response = self.assertResponse(blocked_user(user2, method='GET'), 200, count=1)
        self.assertEqual(response['results'][0]['blocked']['username'], new_username)
        self.assertThread(user1, user2)

    def test_004_rename_chat(self):
        old_username = 'rename-chat-' + rnstr()
        user1 = self.user(username=old_username)
        user2 = self.user()
        new_username = 'new-username-' + rnstr()

        self.assertResponse(accept_chat(user2), 200)
        self.assertResponse(create_chat(user1, user2['username']), 201)
        self.assertResponse(me(user1, method='PATCH', data={'username': new_username}), 200)

        self.assertResponse(create_chat(user2, method='GET', query=old_username), 200, count=0)
        self.assertResponse(create_chat(user2, method='GET', query=new_username), 200, count=1)
        self.assertThread(user1, user2)

    def test_005_rename_sse(self):
        user1 = self.user()
        new_username = 'rename-sse-' + rnstr()

        self.assertResponse(me(user1, method='PATCH', data={'username': new_username}), 200)
        self.assertResponse(me(user1), 200)
        self.assertThread(user1)


class Test06_download_data(UnitTest):

    def test_001_download_data(self):
        user1 = self.user(['accept-friend-request', 'receive-friend-request', 'receive-friend-request', 'receive-friend-request', 'game-start', 'game-start', 'game-start'])
        user2 = self.user(['accept-friend-request'])
        user3 = self.user(['accept-friend-request'])
        user4 = self.user()
        user5 = self.user()
        user6 = self.user(['receive-friend-request'])
        user7 = self.user(['receive-friend-request'])
        user8 = self.user(['receive-friend-request'])
        user9 = self.user()
        user10 = self.user(['game-start'])
        user11 = self.user(['game-start'])
        user12 = self.user(['game-start'])
        user13 = self.user()

        self.assertFriendResponse(create_friendship(user1, user6))
        self.assertResponse(friend_requests(user1, user7), 201)
        self.assertResponse(friend_requests(user1, user8), 201)
        self.assertResponse(friend_requests(user13, user1), 201)
        self.assertResponse(blocked_user(user1, user9['id']), 201)

        def make_conversation(user, messages, _friend=False):
            if _friend:
                self.assertFriendResponse(create_friendship(user, user1))
            else:
                self.assertResponse(accept_chat(user), 200)
            chat_id = self.assertResponse(create_chat(user1, user['username']), 201, get_field=True)
            for msg in messages:
                self.assertResponse(create_message(user1, chat_id, msg), 201)

        make_conversation(user2, ['msg1', 'msg2', 'msg3'], True)
        make_conversation(user3, [], True)
        make_conversation(user4, ['erg', 'dfg', 'dfg', 'erg', 'dfg', 'dfg', 'erg', 'dfg', 'dfg', 'erg', 'dfg', 'dfg', 'erg', 'dfg', 'dfg', 'erg', 'dfg', 'caca'])
        make_conversation(user5, ['hey', 'ah'])

        for u in (user10, user11, user12):
            self.assertResponse(create_game(user1, u), 201)
            self.assertResponse(score(user1['id']), 200)
            self.assertResponse(score(user1['id']), 200)
            self.assertResponse(score(user1['id']), 200)
            time.sleep(1)

        self.assertResponse(get_data(user1), 200)
        self.assertThread(user1, user2, user3, user4, user5, user6, user7, user8, user9, user10, user11, user12, user13)

    def test_002_chat_data(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()
        user4 = self.user()

        def make_conversation(user, messages):
            self.assertResponse(accept_chat(user), 200)
            chat_id = self.assertResponse(create_chat(user1, user['username']), 201, get_field=True)
            for msg in messages:
                self.assertResponse(create_message(user1, chat_id, msg), 201)

        make_conversation(user2, ['msg1', 'msg2', 'msg3'])
        make_conversation(user3, [])
        make_conversation(user4, ['erg', 'dfg', 'dfg', 'erg', 'dfg', 'dfg', 'erg', 'dfg', 'dfg', 'erg', 'dfg', 'dfg', 'erg', 'dfg', 'dfg', 'erg', 'dfg', 'caca'])

        self.assertResponse(get_chat_data(user1), 200)
        self.assertThread(user1, user2, user3, user4)

    def test_003_game_data(self):
        user1 = self.user(['game-start', 'game-start'])
        user2 = self.user(['game-start'])
        user3 = self.user(['game-start'])

        for u in (user2, user3):
            self.assertResponse(create_game(user1, u), 201)
            self.assertResponse(score(user1['id']), 200)
            self.assertResponse(score(user1['id']), 200)
            self.assertResponse(score(user1['id']), 200)
            time.sleep(1)

        self.assertResponse(get_game_data(user1), 200)
        self.assertThread(user1, user2, user3)


if __name__ == '__main__':
    unittest.main()
