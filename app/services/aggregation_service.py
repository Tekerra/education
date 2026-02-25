from sqlalchemy import func

import numpy as np
import pandas as pd

from app.extensions import db
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.student import Student
from app.utils.constants import GRADE_POINTS


def _assessment_dataframe(query):
    rows = query.all()
    if not rows:
        return pd.DataFrame(columns=["grade", "total_score", "course_code", "department_id", "faculty_id"])
    return pd.DataFrame(
        rows,
        columns=["grade", "total_score", "course_code", "department_id", "faculty_id"],
    )


def student_gpa_estimate(student_id: int) -> float:
    rows = (
        db.session.query(Assessment.grade, Course.credit_units)
        .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
        .join(Course, Course.course_id == Enrollment.course_id)
        .filter(Enrollment.student_id == student_id)
        .all()
    )
    if not rows:
        return 0.0
    total_points = 0.0
    total_units = 0
    for grade, units in rows:
        total_points += GRADE_POINTS.get(grade, 0.0) * units
        total_units += units
    if total_units == 0:
        return 0.0
    return round(total_points / total_units, 2)


def course_pass_rate(course_id: int) -> float:
    total = (
        db.session.query(func.count(Assessment.assessment_id))
        .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
        .filter(Enrollment.course_id == course_id)
        .scalar()
        or 0
    )
    if total == 0:
        return 0.0
    passed = (
        db.session.query(func.count(Assessment.assessment_id))
        .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
        .filter(Enrollment.course_id == course_id, Assessment.total_score >= 50)
        .scalar()
        or 0
    )
    return round((passed / total) * 100, 2)


def department_average(department_id: int) -> float:
    avg_score = (
        db.session.query(func.avg(Assessment.total_score))
        .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
        .join(Course, Course.course_id == Enrollment.course_id)
        .filter(Course.department_id == department_id)
        .scalar()
    )
    return round(float(avg_score), 2) if avg_score is not None else 0.0


def faculty_pass_rate(faculty_id: int) -> float:
    total = (
        db.session.query(func.count(Assessment.assessment_id))
        .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
        .join(Course, Course.course_id == Enrollment.course_id)
        .join(Department, Department.department_id == Course.department_id)
        .filter(Department.faculty_id == faculty_id)
        .scalar()
        or 0
    )
    if total == 0:
        return 0.0
    passed = (
        db.session.query(func.count(Assessment.assessment_id))
        .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
        .join(Course, Course.course_id == Enrollment.course_id)
        .join(Department, Department.department_id == Course.department_id)
        .filter(Department.faculty_id == faculty_id, Assessment.total_score >= 50)
        .scalar()
        or 0
    )
    return round((passed / total) * 100, 2)


def institution_performance_trend():
    rows = (
        db.session.query(Enrollment.session, func.avg(Assessment.total_score))
        .join(Assessment, Assessment.enrollment_id == Enrollment.enrollment_id)
        .group_by(Enrollment.session)
        .order_by(Enrollment.session.asc())
        .all()
    )
    return [{"session": s, "average_score": round(float(avg), 2)} for s, avg in rows]


def grade_distribution(department_id: int | None = None):
    query = (
        db.session.query(
            Assessment.grade,
            Assessment.total_score,
            Course.course_code,
            Course.department_id,
            Department.faculty_id,
        )
        .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
        .join(Course, Course.course_id == Enrollment.course_id)
        .join(Department, Department.department_id == Course.department_id)
    )
    if department_id:
        query = query.filter(Course.department_id == department_id)

    df = _assessment_dataframe(query)
    if df.empty:
        return {}
    counts = df["grade"].value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items()}


def department_analytics_snapshot(department_id: int):
    query = (
        db.session.query(
            Assessment.grade,
            Assessment.total_score,
            Course.course_code,
            Course.department_id,
            Department.faculty_id,
        )
        .join(Enrollment, Enrollment.enrollment_id == Assessment.enrollment_id)
        .join(Course, Course.course_id == Enrollment.course_id)
        .join(Department, Department.department_id == Course.department_id)
        .filter(Course.department_id == department_id)
    )
    df = _assessment_dataframe(query)
    if df.empty:
        return {
            "average_score": 0.0,
            "pass_rate": 0.0,
            "grade_distribution": {},
            "high_risk_courses": [],
        }

    average_score = float(np.round(df["total_score"].mean(), 2))
    pass_rate = float(np.round((df["total_score"] >= 50).mean() * 100, 2))
    grade_dist = {str(k): int(v) for k, v in df["grade"].value_counts().to_dict().items()}
    high_risk = (
        df.groupby("course_code")["total_score"].mean().reset_index().query("total_score < 50")["course_code"].tolist()
    )

    return {
        "average_score": average_score,
        "pass_rate": pass_rate,
        "grade_distribution": grade_dist,
        "high_risk_courses": high_risk,
    }


def system_stats():
    return {
        "students": db.session.query(func.count(Student.student_id)).scalar() or 0,
        "faculties": db.session.query(func.count(Faculty.faculty_id)).scalar() or 0,
        "departments": db.session.query(func.count(Department.department_id)).scalar() or 0,
        "courses": db.session.query(func.count(Course.course_id)).scalar() or 0,
        "institution_trend": institution_performance_trend(),
    }

