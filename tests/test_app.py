from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_app():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_valid_student_to_activity():
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_non_school_email():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid student email"


def test_signup_rejects_duplicate_student():
    email = "new.student@mergington.edu"
    signup_url = "/activities/Chess Club/signup"

    first_response = client.post(signup_url, params={"email": email})
    second_response = client.post(signup_url, params={"email": email})

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "Student is already registered for this activity"
    )
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_unregister_removes_registered_student():
    email = "registered.student@mergington.edu"
    activities["Soccer Club"]["participants"].append(email)

    response = client.delete(
        f"/activities/Soccer Club/participants/{email}"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Soccer Club"
    }
    assert email not in activities["Soccer Club"]["participants"]


def test_unregister_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/participants/student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_missing_participant():
    response = client.delete(
        "/activities/Soccer Club/participants/missing@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
