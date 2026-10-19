from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def isolated_activities(monkeypatch):
    activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client, isolated_activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == isolated_activities


def test_new_signup_succeeds(client, isolated_activities):
    email = "new@mergington.edu"
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert isolated_activities["Chess Club"]["participants"].count(email) == 1


def test_repeated_signup_is_rejected(client, isolated_activities):
    email = "new@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert isolated_activities["Chess Club"]["participants"].count(email) == 1


def test_student_can_signup_for_another_activity(client, isolated_activities):
    email = isolated_activities["Chess Club"]["participants"][0]
    response = client.post(
        "/activities/Programming Class/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert email in isolated_activities["Programming Class"]["participants"]


def test_unknown_activity_still_returns_not_found(client):
    response = client.post(
        "/activities/Unknown/signup", params={"email": "new@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_only_selected_participant(client, isolated_activities):
    participants = isolated_activities["Chess Club"]["participants"]
    original = participants.copy()
    email = original[0]
    response = client.delete(
        "/activities/Chess Club/unregister", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert participants == original[1:]
    signup = client.post("/activities/Chess Club/signup", params={"email": email})
    assert signup.status_code == 200


def test_unregister_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/unregister", params={"email": "new@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_missing_participant_leaves_activity_unchanged(
    client, isolated_activities
):
    original = deepcopy(isolated_activities)
    response = client.delete(
        "/activities/Chess Club/unregister", params={"email": "new@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert isolated_activities == original


def test_unregister_requires_email(client):
    response = client.delete("/activities/Chess Club/unregister")

    assert response.status_code == 422


@pytest.mark.parametrize("asset", ("index.html", "app.js", "styles.css"))
def test_static_assets_require_revalidation(client, asset):
    response = client.get(f"/static/{asset}")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"

    cached_response = client.get(
        f"/static/{asset}",
        headers={"If-None-Match": response.headers["etag"]},
    )

    assert cached_response.status_code == 304
    assert cached_response.headers["cache-control"] == "no-cache"
