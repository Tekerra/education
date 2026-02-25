from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

from app.models.analytics_result import AnalyticsResult
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.utils.constants import COURSE_ADVISOR
from app.utils.helpers import success_response
from app.utils.role_required import role_required

advisor_bp = Blueprint("advisor", __name__)


def _current_staff_id() -> int:
    identity = get_jwt_identity()
    _, user_id = identity.split(":")
    return int(user_id)


@advisor_bp.get("/students")
@role_required(COURSE_ADVISOR)
def advisor_students():
    staff_id = _current_staff_id()
    students = Student.query.filter_by(advisor_id=staff_id).all()
    payload = [
        {
            "student_id": s.student_id,
            "matric_no": s.matric_no,
            "full_name": s.full_name,
            "level": s.level,
            "department_id": s.department_id,
        }
        for s in students
    ]
    data, status = success_response("Assigned students fetched", payload)
    return jsonify(data), status


@advisor_bp.get("/at-risk")
@role_required(COURSE_ADVISOR)
def advisor_at_risk():
    staff_id = _current_staff_id()
    rows = (
        Student.query.join(Enrollment, Enrollment.student_id == Student.student_id)
        .join(AnalyticsResult, AnalyticsResult.enrollment_id == Enrollment.enrollment_id)
        .filter(Student.advisor_id == staff_id, AnalyticsResult.risk_level.in_(["HIGH", "MEDIUM"]))
        .all()
    )
    payload = [
        {
            "student_id": s.student_id,
            "matric_no": s.matric_no,
            "full_name": s.full_name,
        }
        for s in rows
    ]
    data, status = success_response("At-risk advisees fetched", payload)
    return jsonify(data), status

