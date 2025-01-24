import unittest

from services.blocked import blocked_user, unblocked_user
from services.chat import accept_chat, create_chat, create_message, request_chat_id
from services.friend import create_friendship, friend_requests
from services.user import me
from utils.generate_random import rnstr
from utils.my_unittest import UnitTest


class Test01_CreateChat(UnitTest):

    def test_001_accept_chat_from_anyone(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(accept_chat(user2), 200)
        self.assertResponse(create_chat(user1, user2['username']), 201)
        self.assertThread(user1, user2)

    def test_002_accept_chat_from_friend_only(self):
        user1 = self.user(['accept-friend-request'])
        user2 = self.user(['receive-friend-request'])

        self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(create_chat(user1, user2['username']), 201)
        self.assertThread(user1, user2)


class Test02_CreateChatError(UnitTest):

    def test_001_user_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(create_chat(user1, 'caca_pipi_proute'), 404, {'detail': 'User not found.'})
        self.assertThread(user1)

    def test_002_does_not_accept_chat(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(create_chat(user1, user2['username']), 403, {'detail': 'This user does not accept new chat.'})
        self.assertThread(user1, user2)

    def test_003_blocked_by_user(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(blocked_user(user1, user2['id']), 201)
        self.assertResponse(create_chat(user2, user1['username']), 404, {'detail': 'User not found.'})
        self.assertThread(user1, user2)

    def test_004_chat_with_myself(self):
        user1 = self.user()

        self.assertResponse(create_chat(user1, user1['username']), 403, {'detail': 'You cannot chat with yourself.'})
        self.assertThread(user1)

    def test_005_accept_chat_from_none(self):
        user1 = self.user(['accept-friend-request'])
        user2 = self.user(['receive-friend-request'])

        self.assertResponse(accept_chat(user2, 'none'), 200)
        self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(create_chat(user1, user2['username']), 403, {'detail': 'This user does not accept new chat.'})
        self.assertThread(user1, user2)

    def test_006_already_chat_with(self):
        user1 = self.user(['accept-friend-request'])
        user2 = self.user(['receive-friend-request'])

        self.assertFriendResponse(create_friendship(user1, user2))
        self.assertResponse(create_chat(user1, user2['username']), 201)
        self.assertResponse(create_chat(user1, user2['username']), 409, {'detail': 'You are already chat with this user.'})
        self.assertThread(user1, user2)

    def test_007_blocked_user_trying_request(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(blocked_user(user1, user2['id']), 201)
        self.assertResponse(friend_requests(user1, user2), 403, {'detail': 'You blocked this user.'})
        self.assertThread(user1, user2)

    def test_008_chat_with_guest(self):
        user1 = self.user()
        user2 = self.user(guest=True)

        self.assertResponse(create_chat(user1, user2['username']), 404, {'detail': 'User not found.'})
        self.assertThread(user1, user2)

    def test_009_guest_create_chat(self):
        user1 = self.user()
        user2 = self.user(guest=True)

        self.assertResponse(accept_chat(user1, 'none'), 200)
        self.assertResponse(create_chat(user2, user1['username']), 403, {'detail': 'Guest users cannot perform this action.'})
        self.assertThread(user1, user2)


class Test03_GetChat(UnitTest):

    def test_001_get_chats(self):
        user1 = self.user()
        ct = 5
        users = [self.user() for _ in range(ct)]

        self.assertResponse(create_chat(user1, method='GET'), 200, count=0)

        for tmp_user in users:
            self.assertResponse(accept_chat(tmp_user), 200)
            self.assertResponse(create_chat(user1, tmp_user['username']), 201)

        self.assertResponse(create_chat(user1, method='GET'), 200, count=ct)
        self.assertThread(user1, *users)

    def test_002_search_chats(self):
        user1 = self.user()
        user2 = self.user(username='caca' + rnstr())

        name = 'chat-user'
        users = [self.user(username=name + rnstr()) for _ in range(5)]

        for tmp_user in users:
            self.assertResponse(accept_chat(tmp_user), 200)
            self.assertResponse(create_chat(user1, tmp_user['username']), 201)

        self.assertResponse(accept_chat(user2), 200)
        self.assertResponse(create_chat(user1, user2['username']), 201)

        self.assertResponse(create_chat(user1, method='GET', query='caca'), 200, count=1)

        self.assertResponse(create_chat(user1, method='GET', query=name), 200, count=5)
        self.assertThread(user1, user2, *users)

    def test_003_search_chats_none(self):
        user1 = self.user()

        self.assertResponse(create_chat(user1, method='GET', data={'q': 'chat'}), 200, count=0)
        self.assertThread(user1)

    def test_004_blocked_chat(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(accept_chat(user2), 200)
        chat_id = self.assertResponse(create_chat(user1, user2['username']), 201, get_field=True)

        self.assertResponse(blocked_user(user1, user2['id']), 201)

        self.assertResponse(request_chat_id(user1, chat_id), 403, {'detail': 'You do not belong to this chat.'})
        self.assertResponse(request_chat_id(user2, chat_id), 403, {'detail': 'You do not belong to this chat.'})
        self.assertThread(user1, user2)

    def test_005_get_chat_not_belong(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()

        self.assertResponse(accept_chat(user2), 200)
        chat_id = self.assertResponse(create_chat(user1, user2['username']), 201, get_field=True)

        self.assertResponse(request_chat_id(user3, chat_id), 403, {'detail': 'You do not belong to this chat.'})
        self.assertThread(user1, user2, user3)

    def test_006_do_not_view_chat(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(accept_chat(user2), 200)
        chat_id = self.assertResponse(create_chat(user1, user2['username']), 201, get_field=True)

        self.assertResponse(request_chat_id(user1, chat_id, 'DELETE'), 204)
        self.assertResponse(create_chat(user1, method='GET'), 200, count=0)
        self.assertResponse(create_chat(user2, method='GET'), 200, count=1)
        self.assertResponse(request_chat_id(user1, chat_id), 200)
        self.assertResponse(create_chat(user1, method='GET'), 200, count=1)
        self.assertThread(user1, user2)

    def test_007_delete_chat(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(accept_chat(user2), 200)
        chat_id = self.assertResponse(create_chat(user1, user2['username']), 201, get_field=True)

        self.assertResponse(request_chat_id(user1, chat_id, method='DELETE'), 204)
        self.assertResponse(request_chat_id(user2, chat_id), 200)
        self.assertThread(user1, user2)


class Test04_Messages(UnitTest):

    def send_message(self, user1, user2):
        self.assertResponse(accept_chat(user2), 200)

        chat_id = self.assertResponse(create_chat(user1, user2['username']), 201, get_field=True)
        self.assertResponse(create_message(user1, chat_id, 'Hey'), 201)
        self.assertResponse(create_message(user2, chat_id, 'Hi'), 201)
        self.assertResponse(create_message(user1, chat_id, 'How are you ?'), 201)
        self.assertResponse(create_message(user2, chat_id, 'goood !'), 201)
        self.assertResponse(create_message(user2, chat_id, 'and u ?'), 201)

        return chat_id

    def test_001_send_messages(self):
        user1 = self.user()
        user2 = self.user()

        chat_id = self.send_message(user1, user2)
        response = self.assertResponse(request_chat_id(user1, chat_id), 200)
        self.assertEqual('and u ?', response['last_message']['content'])
        self.assertThread(user1, user2)

    def test_002_get_messages(self):
        user1 = self.user()
        user2 = self.user()

        chat_id = self.send_message(user1, user2)

        self.assertResponse(create_message(user1, chat_id, method='GET'), 200, count=5)
        self.assertThread(user1, user2)

    def test_003_send_chat_does_not_exist(self):
        user1 = self.user()

        self.assertResponse(create_message(user1, '123456', 'test'), 403, {'detail': 'You do not belong to this chat.'})
        self.assertThread(user1)

    def test_004_send_chat_does_not_belong(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()

        self.assertResponse(accept_chat(user1), 200)

        chat_id = self.assertResponse(create_chat(user2, user1['username']), 201, get_field=True)

        self.assertResponse(create_message(user3, chat_id, 'test'), 403, {'detail': 'You do not belong to this chat.'})
        self.assertThread(user1, user2, user3)

    def test_005_chat_blocked(self):
        user1 = self.user()
        user2 = self.user()

        chat_id = self.send_message(user1, user2)

        block_id = self.assertResponse(blocked_user(user1, user2['id']), 201, get_field=True)

        self.assertResponse(request_chat_id(user1, chat_id), 403, {'detail': 'You do not belong to this chat.'})
        self.assertResponse(create_message(user1, chat_id, method='GET'), 403, {'detail': 'You do not belong to this chat.'})
        self.assertResponse(create_message(user1, chat_id, 'block'), 403, {'detail': 'You do not belong to this chat.'})

        self.assertResponse(unblocked_user(user1, block_id), 204)
        self.assertResponse(create_message(user1, chat_id, 'thank for unblocking me ;))'), 201)
        self.assertResponse(request_chat_id(user1, chat_id), 200)
        self.assertThread(user1, user2)

    def test_006_do_not_view_chat(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(accept_chat(user2), 200)
        chat_id = self.assertResponse(create_chat(user1, user2['username']), 201, get_field=True)

        self.assertResponse(request_chat_id(user1, chat_id, method='DELETE'), 204)

        self.assertResponse(create_message(user1, chat_id, 'do not view chat'), 403, {'detail': 'You do not belong to this chat.'})

        self.assertResponse(create_chat(user1, method='GET'), 200, count=0)

        self.assertResponse(create_message(user2, chat_id, 'Hey how are you ?'), 201)

        self.assertResponse(create_chat(user1, method='GET'), 200, count=1)
        self.assertResponse(create_message(user1, chat_id, 'Fine and u?'), 201)
        self.assertThread(user1, user2)

    def test_007_get_chat_sort_by_last_update(self):
        user1 = self.user()
        users = [self.user() for _ in range(5)]
        chat_id = None
        tmp_chat_id = None

        for tmp_user in users:
            tmp_chat_id = self.send_message(user1, tmp_user)
            if chat_id is None:
                chat_id = tmp_chat_id

        response = self.assertResponse(create_chat(user1, method='GET'), 200, count=5)
        self.assertEqual(tmp_chat_id, response['results'][0]['id'])
        self.assertResponse(create_message(user1, chat_id, 'Hey !'), 201)
        response = self.assertResponse(create_chat(user1, method='GET'), 200)
        self.assertEqual(chat_id, response['results'][0]['id'])
        self.assertThread(user1, *users)

    def test_008_message_notifications(self):
        user1 = self.user()
        user2 = self.user()

        chat_id = self.send_message(user1, user2)
        self.assertEqual(3, self.assertResponse(request_chat_id(user1, chat_id), 200, get_field='unread_messages'))
        self.assertEqual(2, self.assertResponse(request_chat_id(user2, chat_id), 200, get_field='unread_messages'))
        self.assertResponse(create_message(user1, chat_id, method='GET'), 200)
        self.assertEqual(0, self.assertResponse(request_chat_id(user1, chat_id), 200, get_field='unread_messages'))
        self.assertEqual(2, self.assertResponse(request_chat_id(user2, chat_id), 200, get_field='unread_messages'))
        self.assertResponse(create_message(user2, chat_id, 'did you receive new notification ?'), 201)
        self.assertEqual(1, self.assertResponse(request_chat_id(user1, chat_id), 200, get_field='unread_messages'))
        self.assertThread(user1, user2)

    def test_009_chat_notifications(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()

        self.send_message(user1, user2)
        chat_id = self.send_message(user1, user3)
        self.assertEqual(2, self.assertResponse(me(user1), 200, get_field='notifications')['chats'])
        self.assertResponse(create_message(user1, chat_id, method='GET'), 200)
        self.assertEqual(1, self.assertResponse(me(user1), 200, get_field='notifications')['chats'])
        self.assertThread(user1, user2, user3)

    def test_010_last_message_is_read(self):
        user1 = self.user()
        user2 = self.user()

        chat_id = self.send_message(user1, user2)
        self.assertFalse(self.assertResponse(create_chat(user1, method='GET'), 200)['results'][0]['last_message']['is_read'])
        self.assertFalse(self.assertResponse(create_chat(user2, method='GET'), 200)['results'][0]['last_message']['is_read'])

        self.assertResponse(create_message(user1, chat_id, method='GET'), 200)
        self.assertTrue(self.assertResponse(create_chat(user1, method='GET'), 200)['results'][0]['last_message']['is_read'])

        self.assertResponse(create_message(user1, chat_id, data={'content': 'test message', 'is_read': True}), 201)
        self.assertTrue(self.assertResponse(create_chat(user1, method='GET'), 200)['results'][0]['last_message']['is_read'])
        self.assertThread(user1, user2)

    def test_011_message_is_read(self):
        user1 = self.user()
        user2 = self.user()

        chat_id = self.send_message(user1, user2)

        messages = self.assertResponse(create_message(user1, chat_id, method='GET'), 200, get_field='results')
        for message in messages:
            if message['author'] == user2['id']:
                self.assertFalse(message['is_read'])

        messages = self.assertResponse(create_message(user1, chat_id, method='GET'), 200, get_field='results')
        for message in messages:
            if message['author'] == user2['id']:
                self.assertTrue(message['is_read'])

        messages = self.assertResponse(create_message(user2, chat_id, method='GET'), 200, get_field='results')
        for message in messages:
            if message['author'] == user1['id']:
                self.assertFalse(message['is_read'])

        messages = self.assertResponse(create_message(user2, chat_id, method='GET'), 200, get_field='results')
        for message in messages:
            if message['author'] == user1['id']:
                self.assertTrue(message['is_read'])

        self.assertThread(user1, user2)


if __name__ == '__main__':
    unittest.main()
