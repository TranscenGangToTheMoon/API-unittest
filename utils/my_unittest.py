import json
import re
import time
import unittest
from threading import Thread

import httpx

from services.auth import register, create_guest
from services.game import is_in_game
from services.user import me
from utils.generate_random import rnstr


class UnitTest(unittest.TestCase):

    def user(self, tests_sse: list[str] = None, username=None, password=None, guest=False, sse=True, connect_game=True):
        _new_user = {}

        if guest:
            response = create_guest()
        else:
            if username is None:
                username = 'user-' + rnstr(10)
            if password is None:
                password = 'password-' + rnstr(15)
            _new_user['username'] = username
            _new_user['password'] = password
            response = register(_new_user['username'], password)

        token = self.assertResponse(response, 201)
        _new_user['token'] = token['access']
        _new_user['refresh'] = token['refresh']
        response = self.assertResponse(me(_new_user), 200)
        _new_user['id'] = response['id']
        _new_user['username'] = response['username']
        _new_user['is_guest'] = response['is_guest']
        if sse:
            self.connect_to_sse(_new_user, tests_sse, connect_game=connect_game)
        return _new_user

    def assertResponse(self, response, status_code, json_assertion=None, count=None, get_field=None, get_user=False):
        self.assertEqual(status_code, response.status_code)
        if json_assertion is not None:
            self.assertEqual(json_assertion, response.json)
        if count is not None:
            self.assertEqual(count, response.json['count'])
        if get_user:
            return {'token': response.json['access']}
        if get_field is not None:
            if get_field is True:
                get_field = 'id'
            return response.json[get_field]
        return response.json

    def assertFriendResponse(self, responses, status_code=201, json_assertion=None):
        self.assertEqual(201, responses[0].status_code)
        self.assertEqual(status_code, responses[1].status_code)
        if json_assertion is not None:
            self.assertEqual(json_assertion, responses[1].json)
        self.assertEqual(responses[0].json['id'], responses[1].json['id'])
        return responses[1].json['id']

    def connect_to_sse(self, user, tests: list[str] = None, status_code=200, connect_game=True):
        user['thread'] = Thread(target=self._thread_connect_to_sse, args=(user, tests, status_code, connect_game))
        user['thread'].start()
        time.sleep(0.5)
        return user['thread']

    def _thread_connect_to_sse(self, user, tests, status_code, connect_game):
        user['thread_tests'] = tests
        user['thread_assertion'] = []
        user['thread_finish'] = False
        if 'username' not in user:
            user['username'] = 'unknown'
        print(f"SSE CONNECTING {user['username']}...\n", flush=True)
        with httpx.Client(verify=False) as client:
            headers = {
                'Authorization': f'Bearer {user["token"]}',
                'Content-Type': 'text/event-stream',
            }
            with client.stream('GET', 'https://localhost:4443/sse/users/', headers=headers) as response:
                self.assertEqual(status_code, response.status_code)
                if status_code == 200:
                    buff = None
                    for line in response.iter_text():
                        if user['thread_finish']:
                            break
                        if buff is not None:
                            line = buff + line
                            buff = None
                        if '\n\n' not in line:
                            buff = line
                            continue
                        for event, data in re.findall(r'event: ([a-z0-9\-]+)\ndata: (.+)\n\n', line):
                            if event == 'ping':
                                continue
                            data = json.loads(data)
                            print(f"SSE RECEIVED {user['username']}: {data}", flush=True)
                            if data['event_code'] == 'game-start' and connect_game:
                                self.assertResponse(is_in_game(user, data['data']['id']), 200)
                            user['thread_assertion'].append(data['event_code'])
                            if event == 'delete-user':
                                break
        print(f"SSE DISCONNECTING {user['username']}...\n", flush=True)

    def assertThread(self, *users):
        time.sleep(0.1)
        for user in users:
            user['thread_finish'] = True
        for user in users:
            user['thread'].join()
            if user['thread_tests'] is None:
                user['thread_tests'] = []
            print('TEST', user['id'], user['username'], flush=True)
            print('expected', user['thread_tests'], flush=True)
            print('got     ', user['thread_assertion'], flush=True)
            self.assertListEqual(user['thread_tests'], user['thread_assertion'])
