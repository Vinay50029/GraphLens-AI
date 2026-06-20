from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api.models import UserFile
from api.utils.storage import write_user_file, read_user_file, list_user_files
import os
import shutil
from django.conf import settings

class GraphLensSecurityTests(TestCase):
    def setUp(self):
        # Create API Client
        self.client = APIClient()

        # Create two separate test users
        self.user_a = User.objects.create_user(username="usera", password="password123")
        self.user_b = User.objects.create_user(username="userb", password="password123")

        # Set up a test file for User A
        self.filename_a = "user_a_file.txt"
        self.content_a = "Hello from User A!"
        write_user_file(self.user_a.id, self.filename_a, self.content_a)
        self.file_record_a = UserFile.objects.create(user=self.user_a, filename=self.filename_a, file_size=len(self.content_a))

    def tearDown(self):
        # Cleanup created files inside media test directory
        test_media_dir = os.path.join(settings.MEDIA_ROOT, "users")
        if os.path.exists(test_media_dir):
            shutil.rmtree(test_media_dir)

    def test_file_isolation_user_b_cannot_access_user_a_file(self):
        """Verify that User B cannot delete or access User A's file via API endpoints."""
        # Authenticate as User B
        self.client.force_authenticate(user=self.user_b)

        # Attempt to delete User A's file (passing User A's file record ID)
        delete_url = reverse("delete_file", kwargs={"file_id": self.file_record_a.id})
        response = self.client.post(delete_url)

        # Assert status is 404 Not Found (or permission denied)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

        # Assert User A's file record still exists in the database
        self.assertTrue(UserFile.objects.filter(id=self.file_record_a.id).exists())

    def test_list_files_isolation(self):
        """Verify that User B's file listing is empty, even though User A has a file."""
        self.client.force_authenticate(user=self.user_b)

        list_url = reverse("list_files")
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify that User B does not see User A's file
        self.assertEqual(len(response.data["files"]), 0)

    def test_path_traversal_prevention(self):
        """Verify that attempting to fetch or delete files using directory traversal '..' fails."""
        self.client.force_authenticate(user=self.user_a)

        # Try to delete using a negative or non-existent file ID
        delete_url = reverse("delete_file", kwargs={"file_id": 9999})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify that read_user_file behaves properly inside user folder limits
        with self.assertRaises(FileNotFoundError):
            # Attempt to read a non-existent traversal path
            read_user_file(self.user_a.id, "../../../etc/passwd")
