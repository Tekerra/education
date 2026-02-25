from app import create_app
from app.extensions import db
from app.models import (
    AnalyticsResult,
    Assessment,
    Course,
    Department,
    Enrollment,
    Faculty,
    Staff,
    Student,
    University,
)

app = create_app()


@app.shell_context_processor
def shell_context():
    return {
        "db": db,
        "University": University,
        "Faculty": Faculty,
        "Department": Department,
        "Staff": Staff,
        "Student": Student,
        "Course": Course,
        "Enrollment": Enrollment,
        "Assessment": Assessment,
        "AnalyticsResult": AnalyticsResult,
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

