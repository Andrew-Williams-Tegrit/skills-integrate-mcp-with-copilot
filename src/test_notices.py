import copy
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parent))
import app as app_module


class NoticeBoardTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app_module.app)
        self.original_notices = copy.deepcopy(app_module.notices)
        self.original_next_notice_id = app_module.next_notice_id
        today = date.today()
        app_module.notices.clear()
        app_module.notices.update(
            {
                1: {
                    "title": "Active",
                    "body": "Active notice",
                    "start_date": today - timedelta(days=1),
                    "end_date": today + timedelta(days=1),
                    "link": None,
                },
                2: {
                    "title": "Expired",
                    "body": "Expired notice",
                    "start_date": today - timedelta(days=4),
                    "end_date": today - timedelta(days=2),
                    "link": None,
                },
            }
        )
        app_module.next_notice_id = 3

    def tearDown(self):
        app_module.notices.clear()
        app_module.notices.update(self.original_notices)
        app_module.next_notice_id = self.original_next_notice_id

    def test_public_notice_listing_only_shows_active_notices(self):
        response = self.client.get("/notices")
        self.assertEqual(response.status_code, 200)
        notices = response.json()

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]["title"], "Active")

    def test_admin_create_notice_requires_permissions(self):
        payload = {
            "title": "Weather closure",
            "body": "School closes early due to weather.",
            "start_date": str(date.today()),
            "end_date": str(date.today()),
            "link": "https://example.com/notice",
        }
        forbidden_response = self.client.post("/admin/notices", json=payload)
        self.assertEqual(forbidden_response.status_code, 403)

        authorized_response = self.client.post(
            "/admin/notices",
            json=payload,
            headers={"x-admin-token": app_module.ADMIN_NOTICE_TOKEN},
        )
        self.assertEqual(authorized_response.status_code, 201)
        created_notice = authorized_response.json()
        self.assertEqual(created_notice["title"], payload["title"])


if __name__ == "__main__":
    unittest.main()
