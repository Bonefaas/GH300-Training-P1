from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class SignupTests(TestCase):
    def setUp(self):
        self.activities = deepcopy(activities)
        activity_patch = patch("src.app.activities", self.activities)
        activity_patch.start()
        self.addCleanup(activity_patch.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_new_signup_succeeds(self):
        email = "new@mergington.edu"
        response = self.client.post(
            "/activities/Chess Club/signup", params={"email": email}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"message": f"Signed up {email} for Chess Club"}
        )
        self.assertEqual(self.activities["Chess Club"]["participants"].count(email), 1)

    def test_repeated_signup_is_rejected(self):
        email = "new@mergington.edu"
        self.client.post("/activities/Chess Club/signup", params={"email": email})
        response = self.client.post(
            "/activities/Chess Club/signup", params={"email": email}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "Student is already signed up for this activity"},
        )
        self.assertEqual(self.activities["Chess Club"]["participants"].count(email), 1)

    def test_student_can_signup_for_another_activity(self):
        email = self.activities["Chess Club"]["participants"][0]
        response = self.client.post(
            "/activities/Programming Class/signup", params={"email": email}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(email, self.activities["Programming Class"]["participants"])

    def test_unknown_activity_still_returns_not_found(self):
        response = self.client.post(
            "/activities/Unknown/signup", params={"email": "new@mergington.edu"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})

    def test_unregister_removes_only_selected_participant(self):
        participants = self.activities["Chess Club"]["participants"]
        original = participants.copy()
        email = original[0]
        response = self.client.delete(
            "/activities/Chess Club/unregister", params={"email": email}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"message": f"Unregistered {email} from Chess Club"}
        )
        self.assertEqual(participants, original[1:])
        signup = self.client.post(
            "/activities/Chess Club/signup", params={"email": email}
        )
        self.assertEqual(signup.status_code, 200)

    def test_unregister_unknown_activity(self):
        response = self.client.delete(
            "/activities/Unknown/unregister", params={"email": "new@mergington.edu"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})

    def test_unregister_missing_participant_leaves_activity_unchanged(self):
        original = deepcopy(self.activities)
        response = self.client.delete(
            "/activities/Chess Club/unregister", params={"email": "new@mergington.edu"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(), {"detail": "Student is not signed up for this activity"}
        )
        self.assertEqual(self.activities, original)

    def test_unregister_requires_email(self):
        response = self.client.delete("/activities/Chess Club/unregister")

        self.assertEqual(response.status_code, 422)

    def test_static_assets_require_revalidation(self):
        for asset in ("index.html", "app.js", "styles.css"):
            with self.subTest(asset=asset):
                response = self.client.get(f"/static/{asset}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["cache-control"], "no-cache")
                cached_response = self.client.get(
                    f"/static/{asset}",
                    headers={"If-None-Match": response.headers["etag"]},
                )
                self.assertEqual(cached_response.status_code, 304)
                self.assertEqual(cached_response.headers["cache-control"], "no-cache")
