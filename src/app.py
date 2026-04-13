"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from datetime import date
from typing import Annotated
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, model_validator
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

ADMIN_NOTICE_TOKEN = os.getenv("ADMIN_NOTICE_TOKEN", "teacher-admin-token")


class NoticePayload(BaseModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    start_date: date
    end_date: date
    link: str | None = None

    @model_validator(mode="after")
    def validate_date_window(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


notices = {
    1: {
        "title": "Spring break office hours",
        "body": "Guidance office hours are reduced this week.",
        "start_date": date(2026, 4, 1),
        "end_date": date(2026, 4, 30),
        "link": None,
    }
}
next_notice_id = 2


def require_notice_admin(
    x_admin_token: Annotated[str | None, Header()] = None,
):
    if x_admin_token != ADMIN_NOTICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required",
        )


def is_notice_active(notice: dict, current_date: date | None = None) -> bool:
    check_date = current_date or date.today()
    return notice["start_date"] <= check_date <= notice["end_date"]


def format_notice(notice_id: int, notice: dict) -> dict:
    return {"id": notice_id, **notice}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.get("/notices")
def get_active_notices():
    active_notices = [
        format_notice(notice_id, notice)
        for notice_id, notice in notices.items()
        if is_notice_active(notice)
    ]
    return sorted(active_notices, key=lambda notice: (notice["start_date"], notice["id"]))


@app.get("/admin/notices", dependencies=[Depends(require_notice_admin)])
def get_all_notices():
    all_notices = [
        format_notice(notice_id, notice)
        for notice_id, notice in notices.items()
    ]
    return sorted(all_notices, key=lambda notice: (notice["start_date"], notice["id"]))


@app.post(
    "/admin/notices",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_notice_admin)],
)
def create_notice(notice: NoticePayload):
    global next_notice_id
    notices[next_notice_id] = notice.model_dump()
    created_notice = format_notice(next_notice_id, notices[next_notice_id])
    next_notice_id += 1
    return created_notice


@app.put("/admin/notices/{notice_id}", dependencies=[Depends(require_notice_admin)])
def update_notice(notice_id: int, notice: NoticePayload):
    if notice_id not in notices:
        raise HTTPException(status_code=404, detail="Notice not found")

    notices[notice_id] = notice.model_dump()
    return format_notice(notice_id, notices[notice_id])


@app.delete("/admin/notices/{notice_id}", dependencies=[Depends(require_notice_admin)])
def delete_notice(notice_id: int):
    if notice_id not in notices:
        raise HTTPException(status_code=404, detail="Notice not found")

    notices.pop(notice_id)
    return {"message": "Notice deleted"}
