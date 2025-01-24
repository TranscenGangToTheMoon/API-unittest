import unittest
from random import randint

from services.blocked import are_blocked, blocked_user, unblocked_user
from utils.my_unittest import UnitTest


class Test01_Blocked(UnitTest):

    def test_001_blocked(self):
        user1 = self.user()
        n = randint(1, 10)
        users = [self.user() for _ in range(n)]

        for user_tmp in users:
            self.assertResponse(blocked_user(user1, user_tmp['id']), 201)
        self.assertResponse(blocked_user(user1, method='GET'), 200, count=n)
        self.assertThread(user1, *users)

    def test_002_unblocked(self):
        user1 = self.user()
        user2 = self.user()

        block_id = self.assertResponse(blocked_user(user1, user2['id']), 201, get_field=True)
        self.assertResponse(blocked_user(user1, method='GET'), 200, count=1)
        self.assertResponse(unblocked_user(user1, block_id), 204)
        self.assertResponse(blocked_user(user1, method='GET'), 200, count=0)
        self.assertThread(user1, user2)


class Test02_BlockedError(UnitTest):

    def test_001_already_blocked(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(blocked_user(user1, user2['id']), 201)
        self.assertResponse(blocked_user(user1, user2['id']), 409, {'detail': 'You are already blocked this user.'})
        self.assertThread(user1, user2)

    def test_002_blocked_not_existing_user(self):
        user1 = self.user()

        self.assertResponse(blocked_user(user1, 123456), 404, {'detail': 'User not found.'})
        self.assertThread(user1)

    def test_003_blocked_user_that_block_us(self):
        user1 = self.user()
        user2 = self.user()

        self.assertResponse(blocked_user(user1, user2['id']), 201)
        self.assertResponse(blocked_user(user2, user1['id']), 404, {'detail': 'User not found.'})
        self.assertThread(user1, user2)

    def test_004_blocked_guest(self):
        user1 = self.user()
        user2 = self.user(guest=True)

        self.assertResponse(blocked_user(user1, user2['id']), 404, {'detail': 'User not found.'})
        self.assertThread(user1, user2)

    def test_005_blocked_by_guest(self):
        user1 = self.user(guest=True)
        user2 = self.user()

        self.assertResponse(blocked_user(user1, user2['id']), 403, {'detail': 'Guest users cannot perform this action.'})
        self.assertThread(user1, user2)

    def test_006_unblock_doest_not_exist(self):
        user1 = self.user()

        self.assertResponse(unblocked_user(user1, 123456), 403, {'detail': 'This blocked user entry does not belong to you.'})
        self.assertThread(user1)

    def test_007_unblock_not_self_instance(self):
        user1 = self.user()
        user2 = self.user()
        user3 = self.user()

        block_id = self.assertResponse(blocked_user(user1, user2['id']), 201, get_field=True)
        self.assertResponse(unblocked_user(user3, block_id), 403, {'detail': 'This blocked user entry does not belong to you.'})
        self.assertThread(user1, user2, user3)


if __name__ == '__main__':
    unittest.main()
