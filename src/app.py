"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from datetime import date as date_type
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
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


# ---------------------------------------------------------------------------
# Attendance tracking
# ---------------------------------------------------------------------------
# Structure: { "YYYY-MM-DD": { "Activity Name": { "email": True/False, ... } } }
attendance_records: dict = {}


class AttendanceInput(BaseModel):
    present: list[str]  # list of emails that attended the session


@app.post("/activities/{activity_name}/attendance")
def mark_attendance(
    activity_name: str,
    body: AttendanceInput,
    date: Optional[str] = Query(default=None, description="ISO date YYYY-MM-DD, defaults to today"),
):
    """Mark attendance for an activity session on a given date.

    Only participants already signed up for the activity can be marked present.
    Everyone else in the activity is recorded as absent.
    """
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    session_date = date or str(date_type.today())

    # Validate that all emails in 'present' are registered participants
    participants = set(activities[activity_name]["participants"])
    unknown = [e for e in body.present if e not in participants]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"The following emails are not registered for this activity: {unknown}",
        )

    # Build attendance record: True = present, False = absent
    record = {email: (email in body.present) for email in participants}

    attendance_records.setdefault(session_date, {})[activity_name] = record
    return {
        "message": f"Attendance recorded for {activity_name} on {session_date}",
        "date": session_date,
        "present": body.present,
        "absent": [e for e in participants if e not in body.present],
    }


@app.get("/activities/{activity_name}/attendance")
def get_attendance(
    activity_name: str,
    start_date: Optional[str] = Query(default=None, description="Filter from date (YYYY-MM-DD, inclusive)"),
    end_date: Optional[str] = Query(default=None, description="Filter to date (YYYY-MM-DD, inclusive)"),
):
    """Get attendance records for an activity, optionally filtered by date range."""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    sessions = []
    for session_date, activities_on_date in sorted(attendance_records.items()):
        if start_date and session_date < start_date:
            continue
        if end_date and session_date > end_date:
            continue
        if activity_name not in activities_on_date:
            continue

        record = activities_on_date[activity_name]
        present = [e for e, attended in record.items() if attended]
        absent = [e for e, attended in record.items() if not attended]
        total = len(record)
        sessions.append({
            "date": session_date,
            "present": present,
            "absent": absent,
            "present_count": len(present),
            "absent_count": len(absent),
            "attendance_rate": round(len(present) / total, 2) if total else 0,
        })

    return {"activity": activity_name, "sessions": sessions, "total_sessions": len(sessions)}


@app.get("/activities/{activity_name}/attendance/summary")
def get_activity_attendance_summary(activity_name: str):
    """Return per-student attendance totals and rates for an activity."""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    totals: dict[str, dict] = {}
    session_count = 0

    for activities_on_date in attendance_records.values():
        if activity_name not in activities_on_date:
            continue
        session_count += 1
        for email, attended in activities_on_date[activity_name].items():
            stats = totals.setdefault(email, {"attended": 0, "missed": 0})
            if attended:
                stats["attended"] += 1
            else:
                stats["missed"] += 1

    per_student = {
        email: {
            **stats,
            "total_sessions": session_count,
            "attendance_rate": round(stats["attended"] / session_count, 2) if session_count else 0,
        }
        for email, stats in totals.items()
    }

    return {
        "activity": activity_name,
        "total_sessions": session_count,
        "per_student": per_student,
    }


@app.get("/students/{email}/attendance")
def get_student_attendance(email: str):
    """Return attendance summary for a specific student across all activities."""
    # Verify the student is registered in at least one activity
    registered = [name for name, act in activities.items() if email in act["participants"]]
    if not registered:
        raise HTTPException(status_code=404, detail="Student not found in any activity")

    summary: dict[str, dict] = {}

    for session_date, activities_on_date in attendance_records.items():
        for activity_name, record in activities_on_date.items():
            if email not in record:
                continue
            stats = summary.setdefault(activity_name, {"attended": 0, "total": 0})
            stats["total"] += 1
            if record[email]:
                stats["attended"] += 1

    activity_summary = {
        activity_name: {
            **stats,
            "attendance_rate": round(stats["attended"] / stats["total"], 2) if stats["total"] else 0,
        }
        for activity_name, stats in summary.items()
    }

    return {"student": email, "activities": activity_summary}
