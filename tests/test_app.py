"""Tests for the Mergington High School API endpoints.

All tests follow the AAA (Arrange-Act-Assert) pattern.
"""

from src.app import activities


class TestRoot:
    def test_root_redirects_to_static_index(self, client):
        # Arrange
        url = "/"

        # Act
        response = client.get(url, follow_redirects=False)

        # Assert
        assert response.status_code in (302, 307)
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    def test_returns_all_activities_with_expected_shape(self, client):
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data.keys() == activities.keys()
        for details in data.values():
            assert expected_fields <= details.keys()

    def test_response_is_not_cached(self, client):
        # Arrange
        url = "/activities"

        # Act
        response = client.get(url)

        # Assert
        assert response.headers["cache-control"] == "no-store"

    def test_known_activity_contains_seeded_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        seeded_email = "michael@mergington.edu"

        # Act
        response = client.get("/activities")

        # Assert
        assert seeded_email in response.json()[activity_name]["participants"]


class TestSignup:
    def test_signup_adds_participant(self, client):
        # Arrange
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
        assert email in activities[activity_name]["participants"]

    def test_signup_unknown_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_email_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # already seeded as a participant

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup", params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
        assert activities[activity_name]["participants"].count(email) == 1


class TestUnregister:
    def test_unregister_removes_participant(self, client):
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"  # seeded participant

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants", params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "message": f"Unregistered {email} from {activity_name}"
        }
        assert email not in activities[activity_name]["participants"]

    def test_unregister_unknown_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants", params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up_returns_404(self, client):
        # Arrange
        activity_name = "Art Club"
        email = "ghost@mergington.edu"  # not a participant

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants", params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student is not signed up for this activity"


class TestSignupUnregisterRoundTrip:
    def test_signup_then_unregister_restores_original_state(self, client):
        # Arrange
        activity_name = "Debate Club"
        email = "roundtrip@mergington.edu"
        original_participants = list(activities[activity_name]["participants"])

        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup", params={"email": email}
        )
        unregister_response = client.delete(
            f"/activities/{activity_name}/participants", params={"email": email}
        )

        # Assert
        assert signup_response.status_code == 200
        assert unregister_response.status_code == 200
        assert activities[activity_name]["participants"] == original_participants
