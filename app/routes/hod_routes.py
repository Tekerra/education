from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import func

from app.extensions import db
from app.models.analytics_result import AnalyticsResult
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.staff import Staff
from app.services.aggregation_service import department_analytics_snapshot
from app.utils.constants import HOD, LECTURER
from app.utils.helpers import error_response, success_response
from app.utils.role_required import role_required

hod_bp = Blueprint("hod", __name__)


@hod_bp.get("/department-analytics")
@role_required(HOD)
def department_analytics():
    claims = get_jwt()
    department_id = claims.get("department_id")
    if not department_id:
        data, status = error_response("HOD has no department assigned", 400)
        return jsonify(data), status
    snapshot = department_analytics_snapshot(department_id)
    data, status = success_response("Department analytics fetched", snapshot)
    return jsonify(data), status


@hod_bp.get("/lecturers")
@role_required(HOD)
def lecturers():
    claims = get_jwt()
    department_id = claims.get("department_id")
    lecturers_q = Staff.query.filter_by(department_id=department_id, role=LECTURER).all()
    payload = [
        {"staff_id": x.staff_id, "full_name": x.full_name, "email": x.email, "role": x.role}
        for x in lecturers_q
    ]
    data, status = success_response("Department lecturers fetched", payload)
    return jsonify(data), status


@hod_bp.get("/high-risk-courses")
@role_required(HOD)
def high_risk_courses():
    claims = get_jwt()
    department_id = claims.get("department_id")
    rows = (
        db.session.query(Course.course_id, Course.course_code, func.avg(Assessment.total_score).label("avg_score"))
        .join(Enrollment, Enrollment.course_id == Course.course_id)
        .join(Assessment, Assessment.enrollment_id == Enrollment.enrollment_id)
        .filter(Course.department_id == department_id)
        .group_by(Course.course_id, Course.course_code)
        .having(func.avg(Assessment.total_score) < 50)
        .all()
    )
    payload = [{"course_id": cid, "course_code": code, "average_score": round(float(avg), 2)} for cid, code, avg in rows]
    data, status = success_response("High-risk courses fetched", payload)
    return jsonify(data), status

