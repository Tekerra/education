from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.staff import Staff
from app.models.student import Student
from app.models.university import University
from app.schemas.student_schema import StudentRegisterSchema, StudentSchema
from app.utils.constants import STUDENT
from app.utils.helpers import error_response, success_response

auth_bp = Blueprint("auth", __name__)

student_register_schema = StudentRegisterSchema()
student_schema = StudentSchema()


def _department_university_id(department_id: int | None) -> int | None:
    if not department_id:
        return None
    department = Department.query.get(department_id)
    if not department:
        return None
    faculty = Faculty.query.get(department.faculty_id)
    return faculty.university_id if faculty else None


def _staff_university_id(staff: Staff) -> int | None:
    return _department_university_id(staff.department_id)


def _student_university_id(student: Student) -> int | None:
    return _department_university_id(student.department_id)


@auth_bp.get("/universities")
def auth_universities():
    universities = University.query.order_by(University.name.asc()).all()
    data, status = success_response(
        "Universities fetched",
        [
            {
                "university_id": uni.university_id,
                "name": uni.name,
                "location": uni.location,
            }
            for uni in universities
        ],
    )
    return jsonify(data), status


@auth_bp.post("/register")
def register():
    try:
        payload = student_register_schema.load(request.get_json() or {})
    except ValidationError as err:
        data, status = error_response("Validation error", 400, str(err.messages))
        return jsonify(data), status

    existing = Student.query.filter_by(matric_no=payload["matric_no"]).first()
    if existing:
        data, status = error_response("Student with this matric number already exists", 409)
        return jsonify(data), status

    student = Student(
        matric_no=payload["matric_no"].strip().upper(),
        full_name=payload["full_name"],
        gender=payload["gender"],
        level=payload["level"],
        department_id=payload["department_id"],
        advisor_id=payload.get("advisor_id"),
    )
    student.set_password(payload["password"])
    db.session.add(student)
    db.session.commit()

    data, status = success_response("Student registered successfully", student_schema.dump(student), 201)
    return jsonify(data), status


@auth_bp.post("/login")
def login():
    payload = request.get_json() or {}
    identifier = str(payload.get("identifier", "")).strip()
    password = str(payload.get("password", "")).strip()
    university_id = payload.get("university_id")

    if not identifier or not password or not university_id:
        data, status = error_response("identifier, password and university_id are required", 400)
        return jsonify(data), status
    try:
        university_id = int(university_id)
    except (TypeError, ValueError):
        data, status = error_response("university_id must be a valid integer", 400)
        return jsonify(data), status

    university = University.query.get(university_id)
    if not university:
        data, status = error_response("University not found", 404)
        return jsonify(data), status

    staff = Staff.query.filter_by(email=identifier.lower()).first()
    if staff and staff.check_password(password):
        staff_uni_id = _staff_university_id(staff)
        if staff_uni_id and staff_uni_id != university_id:
            data, status = error_response("This staff account does not belong to the selected university", 403)
            return jsonify(data), status

        claims = {
            "role": staff.role,
            "user_type": "staff",
            "department_id": staff.department_id,
            "university_id": university_id,
        }
        token = create_access_token(identity=f"staff:{staff.staff_id}", additional_claims=claims)
        data, status = success_response(
            "Login successful",
            {
                "access_token": token,
                "user": {
                    "id": staff.staff_id,
                    "name": staff.full_name,
                    "role": staff.role,
                    "university_id": university_id,
                    "university_name": university.name,
                },
            },
        )
        return jsonify(data), status

    student = Student.query.filter_by(matric_no=identifier.upper()).first()
    if student and student.check_password(password):
        student_uni_id = _student_university_id(student)
        if student_uni_id != university_id:
            data, status = error_response("This student account does not belong to the selected university", 403)
            return jsonify(data), status

        claims = {
            "role": STUDENT,
            "user_type": "student",
            "department_id": student.department_id,
            "university_id": university_id,
        }
        token = create_access_token(identity=f"student:{student.student_id}", additional_claims=claims)
        data, status = success_response(
            "Login successful",
            {
                "access_token": token,
                "user": {
                    "id": student.student_id,
                    "name": student.full_name,
                    "role": STUDENT,
                    "university_id": university_id,
                    "university_name": university.name,
                },
            },
        )
        return jsonify(data), status

    data, status = error_response("Invalid credentials", 401)
    return jsonify(data), status


@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    claims = get_jwt()
    user_type, user_id = identity.split(":")

    if user_type == "staff":
        staff = Staff.query.get(int(user_id))
        if not staff:
            data, status = error_response("User not found", 404)
            return jsonify(data), status
        payload = {
            "id": staff.staff_id,
            "full_name": staff.full_name,
            "email": staff.email,
            "role": staff.role,
            "department_id": staff.department_id,
            "university_id": claims.get("university_id"),
        }
    else:
        student = Student.query.get(int(user_id))
        if not student:
            data, status = error_response("User not found", 404)
            return jsonify(data), status
        payload = {
            "id": student.student_id,
            "full_name": student.full_name,
            "matric_no": student.matric_no,
            "role": STUDENT,
            "department_id": student.department_id,
            "university_id": claims.get("university_id"),
        }

    payload["claims"] = {
        "role": claims.get("role"),
        "user_type": claims.get("user_type"),
        "university_id": claims.get("university_id"),
    }
    data, status = success_response("User profile fetched", payload)
    return jsonify(data), status
