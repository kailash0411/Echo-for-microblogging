import unittest
from app import db, create_app
from app.models import User, Post
from datetime import datetime, timedelta
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):    
        u = User(username='test_name')
        u.set_password('test_password')
        self.assertFalse(u.check_password('wrong_password'))
        self.assertTrue(u.check_password('test_password'))

    def test_followers(self):
        u1 = User(username='test_name1', email='test_name1@gmail.com')
        u2 = User(username='test_name2', email='test_name2@gmail.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u2.followers.all(), [])
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u1.followed.first().username, 'test_name2')
        self.assertEqual(u2.followers.first().username, 'test_name1')

        u1.unfollow(u2)
        db.session.commit()
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)
        self.assertFalse(u1.is_following(u2))

    def test_followed_posts(self):
        u1 = User(username='test_name1', email='test_name1@gmail.com')
        u2 = User(username='test_name2', email='test_name2@gmail.com')
        u3 = User(username='test_name3', email='test_name3@gmail.com')
        u4 = User(username='test_name4', email='test_name4@gmail.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.utcnow()
        p1 = Post(body="post from john", author=u1,
                  timestamp=now + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2,
                  timestamp=now + timedelta(seconds=4))
        p3 = Post(body="post from mary", author=u3,
                  timestamp=now + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4,
                  timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        u1.follow(u2)
        u1.follow(u4)
        u2.follow(u3)
        u3.follow(u4)
        db.session.commit()

        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()

        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])


if __name__ == '__main__':
    unittest.main(verbosity=2)