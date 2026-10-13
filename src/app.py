"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

# FastAPI provides the application and structured HTTP error classes.
from fastapi import FastAPI, HTTPException, Query
# StaticFiles serves the browser-based frontend from the local static folder.
from fastapi.staticfiles import StaticFiles
# RedirectResponse sends visitors from the API root to the frontend page.
from fastapi.responses import RedirectResponse
import os  # Builds a platform-independent path to the static directory.
from pathlib import Path  # Locates files relative to this Python module.
from threading import Lock

# Create the API application and expose descriptive metadata in its generated docs.
app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Resolve the directory containing this file so startup works from any working directory.
current_dir = Path(__file__).parent
# Make frontend assets available under /static (for example, /static/index.html).
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database. Each activity stores display information, its enrollment
# limit, and the email addresses of currently registered students. Data resets whenever
# the application process restarts because it is not persisted to an external database.
activities = {
    "Chess Club": {
        "category": "Academic & Enrichment",
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "category": "Academic & Enrichment",
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "category": "Athletics",
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Debate Club": {
        "category": "Academic & Enrichment",
        "description": "Develop critical thinking and public speaking skills",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["liam@mergington.edu", "ava@mergington.edu"]
    },
    "Soccer Team": {
        "category": "Athletics",
        "description": "Practice soccer skills and compete in school matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["noah@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Team": {
        "category": "Athletics",
        "description": "Build basketball skills and participate in team competitions",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["ethan@mergington.edu", "isabella@mergington.edu"]
    },
    "Art Club": {
        "category": "Arts & Culture",
        "description": "Explore drawing, painting, and mixed-media art",
        "schedule": "Mondays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "amelia@mergington.edu"]
    },
    "Drama Club": {
        "category": "Arts & Culture",
        "description": "Learn acting, stagecraft, and theatrical performance",
        "schedule": "Tuesdays, 3:30 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["james@mergington.edu", "harper@mergington.edu"]
    },
    "Music Ensemble": {
        "category": "Arts & Culture",
        "description": "Practice and perform music as a student ensemble",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 24,
        "participants": ["benjamin@mergington.edu", "evelyn@mergington.edu"]
    }
}
activities_lock = Lock()


# Route requests for the site root to the static frontend rather than returning API data.
@app.get("/")
def root():
    # Use an HTTP redirect so the browser loads the actual HTML resource and its assets.
    return RedirectResponse(url="/static/index.html")


# Return all activities as JSON; FastAPI serializes the nested dictionary automatically.
@app.get("/activities")
def get_activities():
    return activities


# Register a student using the activity name in the URL and email as a query parameter.
@app.post(
    "/activities/{activity_name}/signup",
    summary="Register a student for an activity",
    responses={
        400: {
            "description": "The email is invalid, already registered, or the activity is full"
        },
        404: {"description": "The activity does not exist"},
    },
)
def signup_for_activity(
    activity_name: str,
    email: str = Query(
        ...,
        description="The student's @mergington.edu email address",
        examples=["student@mergington.edu"],
    ),
):
    """Validate and add a student's email to an activity's participant list."""
    # Reject unknown names before attempting to access the activity dictionary.
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Keep a reference to the selected record so its participant list can be updated.
    activity = activities[activity_name]

    # Require one non-empty, whitespace-free username and the exact school domain.
    username, separator, domain = email.partition("@")
    if (
        not separator
        or not username
        or domain != "mergington.edu"
        or any(character.isspace() for character in email)
    ):
        raise HTTPException(status_code=400, detail="Invalid email domain")

    with activities_lock:
        # Prevent duplicate registrations for the same student and activity.
        if email in activity["participants"]:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        if len(activity["participants"]) >= activity["max_participants"]:
            raise HTTPException(status_code=400, detail="Activity is full")

        # Mutate the in-memory list, making the registration visible to later API requests.
        activity["participants"].append(email)
    # Confirm the successful registration with a human-readable response.
    return {"message": f"Signed up {email} for {activity_name}"}
