from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from urllib.parse import quote

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


def test_get_activities_returns_available_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_student_to_activity():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new.student@mergington.edu for Chess Club"
    }
    assert "new.student@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_invalid_email_domain():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new.student@example.com"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid email domain"}


def test_signup_rejects_duplicate_student():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}


def test_signup_rejects_full_activity_without_changing_participants():
    activity = activities["Chess Club"]
    activity["participants"] = [
        f"student{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    original_participants = activity["participants"].copy()

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "waiting.student@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
    assert activity["participants"] == original_participants


def test_signup_fills_last_place_then_rejects_next_student():
    activity = activities["Chess Club"]
    activity["participants"] = [
        f"student{index}@mergington.edu"
        for index in range(activity["max_participants"] - 1)
    ]

    final_place_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "final.student@mergington.edu"},
    )
    full_activity_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "waiting.student@mergington.edu"},
    )

    assert final_place_response.status_code == 200
    assert full_activity_response.status_code == 400
    assert full_activity_response.json() == {"detail": "Activity is full"}
    assert len(activity["participants"]) == activity["max_participants"]
    assert "final.student@mergington.edu" in activity["participants"]
    assert "waiting.student@mergington.edu" not in activity["participants"]


def test_signup_requires_email_parameter():
    original_participants = activities["Chess Club"]["participants"].copy()

    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422
    assert activities["Chess Club"]["participants"] == original_participants


@pytest.mark.parametrize(
    "email",
    [
        "@mergington.edu",
        "student@@mergington.edu",
        "student@evil.com@mergington.edu",
        " student@mergington.edu",
        "student @mergington.edu",
        "student@sub.mergington.edu",
    ],
)
def test_signup_rejects_malformed_school_email(email):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid email domain"}


def test_failed_signup_does_not_change_participants():
    original_participants = activities["Chess Club"]["participants"].copy()

    client.post(
        "/activities/Chess Club/signup",
        params={"email": "invalid@example.com"},
    )

    assert activities["Chess Club"]["participants"] == original_participants


def test_root_redirects_to_static_frontend():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_frontend_is_available():
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_activities_have_expected_structure_and_valid_capacity():
    required_fields = {
        "category",
        "description",
        "schedule",
        "max_participants",
        "participants",
    }

    response = client.get("/activities")

    assert response.status_code == 200
    for activity in response.json().values():
        assert set(activity) == required_fields
        assert len(activity["participants"]) <= activity["max_participants"]


def test_signup_accepts_url_encoded_activity_name():
    activity_name = "Chess Club"

    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": "encoded.student@mergington.edu"},
    )

    assert response.status_code == 200
    assert "encoded.student@mergington.edu" in activities[activity_name]["participants"]


def test_signup_is_visible_in_subsequent_activity_request():
    email = "visible.student@mergington.edu"

    signup_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    assert signup_response.status_code == 200
    assert email in activities_response.json()["Chess Club"]["participants"]


def test_concurrent_signups_cannot_exceed_capacity():
    activity = activities["Chess Club"]
    activity["participants"] = [
        f"student{index}@mergington.edu"
        for index in range(activity["max_participants"] - 1)
    ]
    start_barrier = Barrier(2)

    def signup(email):
        start_barrier.wait()
        with TestClient(app) as concurrent_client:
            return concurrent_client.post(
                "/activities/Chess Club/signup",
                params={"email": email},
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                signup,
                [
                    "first.concurrent@mergington.edu",
                    "second.concurrent@mergington.edu",
                ],
            )
        )

    assert sorted(response.status_code for response in responses) == [200, 400]
    assert len(activity["participants"]) == activity["max_participants"]
