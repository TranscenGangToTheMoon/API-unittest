import unittest

from services.auth import register, register_guest, login, create_guest, verify, refresh
from services.play import play
from services.user import me
from utils.generate_random import rnstr
from utils.my_unittest import UnitTest


class Test01_Register(UnitTest):

    def test_001_register(self):
        username = 'register_test' + rnstr()
        password = 'password_test' + rnstr()

        user = self.assertResponse(register(username, password), 201, get_user=True)
        self.assertResponse(me(user), 200)
        self.assertResponse(login(username, password), 200)

    def test_002_register_already_exist(self):
        user1 = self.user()

        self.assertResponse(register(user1['username'], user1['password']), 400)
        self.assertResponse(register(user1['username'].upper(), user1['password']), 400)
        self.assertThread(user1)

    def test_003_register_invalid_username(self):
        usernames = [
            'de',
            'username_too_long_because_its_must_be_short',
            'invalid_char!@#$',
            'admin',
            'adminstrator',
            'admin123',
            'staff',
            'support22',
            'ft_transcendence',
            'transcendence2',
            'anonymous',
            '',
        ]
        password = 'InvalideUser_123' + rnstr()

        for username in usernames:
            self.assertResponse(register(username, password), 400)

    def test_004_register_invalid_password(self):
        username = 'register_inv_password' + rnstr()
        passwords = [
            '!Invalid_char123 😂 🤣 😃 😄 😅 😆 ',
            '!password_tooooooooooooooooooooooooooooooooooooooooo_long',
            'min_len',
            '123456',
            'password',
            'azertyui',
            'qwertyui',
            'aaaaaaaa',
            '123456789',
            'abcdefgh',
            '',
            username + 'password',
            'register_inv_password',
        ]

        for password in passwords:
            self.assertResponse(register(username, password), 400)

    def test_005_register_password_contain_paste_username(self):
        username = 'pass_contain_username' + rnstr()
        password = 'password' + username
        first_password = 'register_' + rnstr(15)
        user = self.assertResponse(register(username, first_password), 201, get_user=True)
        new_username = 'new_username' + rnstr()

        self.assertResponse(me(user, 'PATCH', data={'username': new_username, 'password': password, 'old_password': first_password}), 200)
        self.assertResponse(login(new_username, password), 200)

    def test_006_register_password_contain_new_username(self):
        password = 'first_pass' + rnstr(10)
        user = self.assertResponse(register(password=password), 201, get_user=True)
        new_username = 'new_username' + rnstr()
        new_password = 'password' + new_username

        self.assertResponse(me(user, 'PATCH', data={'username': new_username, 'password': new_password}), 400)
        self.assertResponse(login(new_username, password), 401)


class Test02_Guest(UnitTest):

    def test_001_create_guest(self):
        self.assertResponse(create_guest(), 201)

    def test_002_register_guest(self):
        user1 = self.user(guest=True)
        username = 'guest-register' + rnstr()

        user = self.assertResponse(register_guest(username=username, guest=user1), 200, get_user=True)
        test_username = self.assertResponse(me(user), 200, get_field='username')
        self.assertEqual(username, test_username)
        self.assertThread(user1)

    def test_003_register_guest_without_tokent(self):
        random_name = rnstr()

        self.assertResponse(register_guest(username='username_' + random_name, password='password_,' + random_name), 401)

    def test_004_register_user_since_guest(self):
        user1 = self.user()

        self.assertResponse(register_guest(guest=user1), 403)
        self.assertThread(user1)

    def test_005_login_guest(self):
        user1 = self.user(guest=True)

        self.assertResponse(login(user1['username'], rnstr()), 401, {'detail': 'No active account found with the given credentials'})
        self.assertThread(user1)

    def test_006_register_guest_try_play_ranked(self):
        user1 = self.user(guest=True)

        self.assertResponse(play(user1, 'ranked'), 403, {'detail': 'Guest users cannot perform this action.'})
        user = self.assertResponse(register_guest(guest=user1), 200, get_user=True)
        self.assertResponse(play(user, 'ranked'), 201)
        self.assertThread(user1)

    def test_007_register_guest_already_exist(self):
        user1 = self.user()
        user2 = self.user(guest=True)

        self.assertResponse(register_guest(username=user1['username'], guest=user2), 400)
        self.assertThread(user1, user2)


class Test03_Login(UnitTest):

    def test_001_login_user_doest_not_exist(self):
        user1 = self.user()

        self.assertResponse(login(user1['username'], user1['password']), 200)
        self.assertThread(user1)

    def test_002_login_bad_password(self):
        self.assertResponse(login('caca', 'pipi'), 401, {'detail': 'No active account found with the given credentials'})

    def test_003_invalid_password(self):
        user1 = self.user()

        self.assertResponse(login(user1['username'], 'zizi'), 401, {'detail': 'No active account found with the given credentials'})
        self.assertThread(user1)

    def test_004_missing_field(self):
        self.assertResponse(login(data={}), 400, {'username': ['This field is required.'], 'password': ['This field is required.']})


class Test04_Verify(UnitTest):

    def test_001_verify(self):
        user1 = self.user()

        respone = self.assertResponse(verify(user1['token']), 200)
        self.assertDictEqual({'id': user1['id'], 'username': user1['username'], 'is_guest': user1['is_guest']}, respone)
        self.assertThread(user1)

    def test_002_invalid_token(self):
        user1 = self.user()

        self.assertResponse(verify('12345798'), 401)
        self.assertResponse(verify(user1['token'], ''), 401)
        self.assertResponse(verify(user1['token'], 'Token '), 401)
        self.assertThread(user1)

    def test_003_no_token(self):
        self.assertResponse(verify(None), 401)
        self.assertResponse(verify(''), 401)

    def test_004_delete_user(self):
        user1 = self.user()

        self.assertResponse(me(user1, 'DELETE', password=True), 204)
        self.assertThread(user1)
        self.assertResponse(verify(user1['token']), 401)


class Test05_Refresh(UnitTest):

    def test_001_refresh(self):
        user1 = self.user()

        response = self.assertResponse(refresh(user1['refresh']), 200)
        user1['token'] = response['access']
        self.assertResponse(me(user1), 200)
        self.assertThread(user1)

    def test_002_refresh_invalid_token(self):
        self.assertResponse(refresh('12345798'), 401)


if __name__ == '__main__':
    unittest.main()
