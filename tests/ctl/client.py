from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import LiveServerTestCase
from eremaea import models
from eremaea.ctl.client import Client
from eremaea.ctl.file import ContentFile
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.views import APIView

try:
	from unittest.mock import patch
except ImportError:
	from mock import patch

class ClientTest(LiveServerTestCase):
	def setUp(self):
		self.client = Client(self.live_server_url)

	def test_upload1(self):
		content = b"123"
		retention_policy = models.RetentionPolicy.objects.create(name="hourly", duration=timedelta(hours=1))
		collection = models.Collection.objects.create(name="mycol", default_retention_policy=retention_policy)
		self.assertTrue(self.client.upload(ContentFile(content,"file.jpg","image/jpeg"), "mycol"))
		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(snapshot.retention_policy, retention_policy)
		self.assertEqual(snapshot.file.read(), content)
	def test_purge1(self):
		retention_policy = models.RetentionPolicy.objects.create(name="hourly", duration=timedelta(hours=1))
		collection = models.Collection.objects.create(name="mycol", default_retention_policy=retention_policy)
		models.Snapshot.objects.create(collection = collection, date = datetime.now() - timedelta(minutes=90))
		self.assertTrue(self.client.purge("hourly"))
		snapshots = models.Snapshot.objects.all()
		self.assertEqual(len(snapshots), 0)

# Workaround for https://github.com/tomchristie/django-rest-framework/issues/2466
# override_settings should have be used here
@patch.object(APIView, 'authentication_classes', new = [TokenAuthentication])
@patch.object(APIView, 'permission_classes', new = [IsAuthenticatedOrReadOnly])
class TokenAuthClientTest(ClientTest):
	def setUp(self):
		user = User.objects.create(username="test")
		token = Token.objects.create(user=user)
		self.client = Client(self.live_server_url, token = token.key)
