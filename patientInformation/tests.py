from django.test import TestCase, Client

from account.models import Account, Group


# Create your tests here.


class TestClass(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        Group.objects.create(name='Admin')
        user = Account.objects.create(
            email='testuser@gmail.com',
            username='test_user',
            first_name='Test',
            last_name='Test'
        )
        user.set_password('1234')
        user.is_accepted = True
        user.save()

    def test_can_login(self):
        c = Client()
        self.assertTrue(c.login(email='testuser@gmail.com', password='1234'))
