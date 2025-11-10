import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root_redirect():
    response = client.get("/")
    assert response.status_code == 200  # FastAPI's RedirectResponse with status_code not specified defaults to 200
    assert response.url.path == "/static/index.html"  # Check that we were redirected to the correct page

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) > 0
    
    # Test structure of an activity
    activity = list(activities.values())[0]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)

def test_signup_flow():
    # Test signup for a new activity
    activity_name = "Chess Club"
    email = "test@mergington.edu"
    
    # First, get current participants
    response = client.get("/activities")
    initial_participants = response.json()[activity_name]["participants"]
    
    # Try to sign up
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    assert "message" in response.json()
    assert email in response.json()["message"]
    
    # Verify participant was added
    response = client.get("/activities")
    updated_participants = response.json()[activity_name]["participants"]
    assert len(updated_participants) == len(initial_participants) + 1
    assert email in updated_participants

    # Clean up - unregister the test participant
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200

def test_duplicate_signup():
    # Test that a student cannot sign up twice
    activity_name = "Chess Club"
    email = "duplicate@mergington.edu"
    
    # First signup should succeed
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    
    # Second signup should fail
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

    # Clean up - unregister the test participant
    client.post(f"/activities/{activity_name}/unregister?email={email}")

def test_unregister_flow():
    # Test unregistering from an activity
    activity_name = "Chess Club"
    email = "unregister@mergington.edu"
    
    # First sign up
    client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Then unregister
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    assert "message" in response.json()
    assert email in response.json()["message"]
    
    # Verify participant was removed
    response = client.get("/activities")
    current_participants = response.json()[activity_name]["participants"]
    assert email not in current_participants

def test_unregister_not_signed_up():
    # Test unregistering when not signed up
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"
    
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]

def test_invalid_activity():
    # Test signing up for non-existent activity
    activity_name = "Invalid Activity"
    email = "test@mergington.edu"
    
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]