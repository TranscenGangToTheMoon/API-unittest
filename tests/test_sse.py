import time
import unittest

from services.auth import register_guest
from services.chat import create_chat, accept_chat
from services.friend import friend_requests
from services.lobby import create_lobby, join_lobby
from services.sse import events
from services.user import me
from utils.generate_random import rnstr
from utils.my_unittest import UnitTest
from utils.sse_event import rfr, gs, rm, lj, cfr, du, afr, i1, i3, ic, ll, lm, it, tj, tl, tm, ts, tsa, tmf, tf, lup, \
    ppu


class Test01_SSE(UnitTest):

    def test_001_connection_success(self):
        user1 = self.user()

        self.assertThread(user1)

    def test_002_guest_connection_success(self):
        user1 = self.user(guest=True)

        self.assertThread(user1)

    def test_003_connect_twice(self):
        user1 = self.user(sse=False)
        user2 = self.user()
        user3 = self.user()

        user1_bis = user1.copy()
        self.connect_to_sse(user1, [rfr])
        time.sleep(1)
        self.connect_to_sse(user1_bis, [rfr, rfr])

        self.assertResponse(friend_requests(user2, user1), 201)
        self.assertThread(user1, user2)
        self.assertResponse(friend_requests(user3, user1), 201)
        self.assertThread(user1_bis, user3)

    def test_004_invalid_token(self):
        thread1 = self.connect_to_sse({'token': 'invalid_token'}, status_code=401)
        thread1.join()

    def test_005_guest_then_register(self):
        user1 = self.user([ppu], guest=True)
        username = 'sse-register-' + rnstr()

        self.assertResponse(register_guest(user1, username=username), 200)
        user1['username'] = username
        self.assertThread(user1)
        response = self.assertResponse(me(user1), 200)
        self.assertFalse(response['is_guest'])
        self.assertEqual(username, response['username'])

    def test_006_delete_user(self):
        user1 = self.user([du])

        self.assertResponse(me(user1, 'DELETE', password=True), 204)
        self.assertThread(user1)


class Test02_EventsEndpoint(UnitTest):

    def test_001_send_event(self):
        user1 = self.user([rm, gs, lj, cfr, du], connect_game=False)

        self.assertResponse(events(user1, data={'content': 'coucou', 'chat_id': 1}, event_code=rm, kwargs={'username': 'didier', 'message': 'coucou'}), 201)
        self.assertResponse(events(user1, event_code=gs), 201)
        self.assertResponse(events(user1, event_code=lj, kwargs={'username': 'robert'}), 201)
        self.assertResponse(events(user1, event_code=cfr), 201)
        self.assertResponse(events(user1, event_code=du), 201)
        self.assertThread(user1)

    def test_002_missing_field(self):
        user1 = self.user()

        errors_request_data = [
            {'users_id': [user1['id']]},
            {'event_code': cfr},
        ]

        for error in errors_request_data:
            self.assertResponse(events(request_data=error), 400)
        self.assertThread(user1)

    def test_003_not_good_type(self):
        user1 = self.user()

        errors_request_data = [
            {'users_id': [user1['id']], 'event_code': None},
            {'users_id': [user1['id']], 'event_code': ['ping']},
            {'users_id': [user1['id']], 'event_code': 'caca'},
            {'users_id': [user1['id']], 'event_code': {'test': 5}},
            {'users_id': [user1['id']], 'event_code': 2},

            {'users_id': None, 'event_code': 'ping'},
            {'users_id': 'caca', 'event_code': 'ping'},
            {'users_id': 6, 'event_code': 'ping'},
            {'users_id': [1, 'coucou'], 'event_code': 'ping'},
            {'users_id': ['coucou'], 'event_code': 'ping'},
            {'users_id': {'cef': 9}, 'event_code': 'ping'},
        ]

        for error in errors_request_data:
            self.assertResponse(events(request_data=error), 400)
        self.assertThread(user1)

    def test_004_user_does_not_exist(self):
        user1 = self.user()

        self.assertThread(user1)
        time.sleep(5)
        self.assertResponse(events({'id': 123456789}, event_code='ping'), 404)
        self.assertResponse(events({'id': user1['id']}, event_code='ping'), 404)

    def test_005_missing_data_kwargs(self):
        events_code = [rm, afr, rfr, i1, i3, ic, it, lj, ll, lm, tj, tl, tm, ts, tsa, tmf, tf]
        user1 = self.user(connect_game=False)

        for e in events_code:
            self.assertResponse(events(user1, event_code=e), 400)
        self.assertThread(user1)

    def test_006_invalid_username_kwargs(self):
        user1 = self.user([rm])

        self.assertResponse(events(user1, data={'content': 'coucou', 'chat_id': 1}, event_code=rm, kwargs={'username': 132456789, 'message': 'coucou'}), 201)
        self.assertThread(user1)


class Test03_SSEConnectionClose(UnitTest):

    def test_001_last_online(self):
        user1 = self.user()
        user2 = self.user()

        last_online = self.assertResponse(me(user1), 200, get_field='last_online')
        self.assertResponse(accept_chat(user2), 200)
        self.assertResponse(create_chat(user1, user2['username']), 201)
        time.sleep(0.5)
        self.assertThread(user1)
        time.sleep(5)
        response = self.assertResponse(create_chat(user1, method='GET'), 200)['results'][0]['chat_with']['status']
        self.assertTrue(response['is_online'])
        self.assertNotEqual(last_online, response['last_online'])
        self.assertThread(user2)

    def test_002_leave_lobby_when_disconnect(self):
        user1 = self.user([lj])
        user2 = self.user([ll, lup])

        code = self.assertResponse(create_lobby(user1), 201, get_field='code')
        self.assertResponse(join_lobby(user2, code), 201)
        self.assertThread(user1)
        time.sleep(5)
        self.assertThread(user2)


if __name__ == '__main__':
    unittest.main()
