import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activity_state():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_list():
    response = client.get("/activities")
    assert response.status_code == 200

    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
    assert "michael@mergington.edu" in data["Chess Club"]["participants"]


def test_signup_adds_participant_and_rejects_duplicates():
    email = "newstudent@mergington.edu"
    signup_response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert signup_response.status_code == 200
    assert signup_response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]

    duplicate_response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_404_for_unknown_activity():
    response = client.post("/activities/Unknown/signup", params={"email": "student@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant_and_rejects_missing():
    email = "michael@mergington.edu"
    response = client.post("/activities/Chess Club/unregister", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]

    missing_response = client.post("/activities/Chess Club/unregister", params={"email": email})
    assert missing_response.status_code == 400
    assert missing_response.json()["detail"] == "Participant not found in this activity"


def test_unregister_returns_404_for_unknown_activity():
    response = client.post("/activities/Unknown/unregister", params={"email": "student@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
