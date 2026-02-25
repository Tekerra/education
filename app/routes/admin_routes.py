from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.course import Course
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.staff import Staff
from app.models.university import University
from app.schemas.course_schema import CourseSchema
from app.schemas.staff_schema import StaffCreateSchema, StaffSchema
from app.schemas.university_schema import DepartmentSchema, FacultySchema, UniversitySchema
from app.services.aggregation_service import system_stats
from app.utils.constants import ADMIN
from app.utils.helpers import error_response, success_response
from app.utils.role_required import role_required

admin_bp = Blueprint("admin", __name__)

DEFAULT_UNIVERSITY_STRUCTURE = {
    "Faculty of Science": [
        "Computer Science",
        "Mathematics",
        "Physics",
        "Chemistry",
        "Biological Sciences",
    ],
    "Faculty of Engineering": [
        "Electrical Engineering",
        "Mechanical Engineering",
        "Civil Engineering",
        "Computer Engineering",
    ],
    "Faculty of Social and Management Sciences": [
        "Economics",
        "Accounting",
        "Business Administration",
        "Political Science",
    ],
    "Faculty of Arts and Humanities": [
        "English",
        "History and International Studies",
        "Philosophy",
        "Linguistics",
    ],
}

university_schema = UniversitySchema()
faculty_schema = FacultySchema()
department_schema = DepartmentSchema()
staff_create_schema = StaffCreateSchema()
staff_schema = StaffSchema()
course_schema = CourseSchema()


def _ensure_university_structure(university_id: int):
    created_faculties = 0
    created_departments = 0
    for faculty_name, departments in DEFAULT_UNIVERSITY_STRUCTURE.items():
        faculty = Faculty.query.filter_by(name=faculty_name, university_id=university_id).first()
        if not faculty:
            faculty = Faculty(name=faculty_name, university_id=university_id)
            db.session.add(faculty)
            db.session.flush()
            created_faculties += 1

        for dept_name in departments:
            exists = Department.query.filter_by(name=dept_name, faculty_id=faculty.faculty_id).first()
            if exists:
                continue
            db.session.add(Department(name=dept_name, faculty_id=faculty.faculty_id))
            created_departments += 1
    return {"created_faculties": created_faculties, "created_departments": created_departments}


@admin_bp.post("/create-university")
@role_required(ADMIN)
def create_university():
    try:
        payload = university_schema.load(request.get_json() or {})
    except ValidationError as err:
        data, status = error_response("Validation error", 400, str(err.messages))
        return jsonify(data), status

    if University.query.filter_by(name=payload["name"]).first():
        data, status = error_response("University already exists", 409)
        return jsonify(data), status

    university = University(**payload)
    db.session.add(university)
    db.session.flush()

    auto_structure = (request.get_json() or {}).get("auto_structure", True)
    structure_result = {"created_faculties": 0, "created_departments": 0}
    if auto_structure:
        structure_result = _ensure_university_structure(university.university_id)

    db.session.commit()
    response_payload = university_schema.dump(university)
    response_payload["auto_structure"] = structure_result
    data, status = success_response("University created", response_payload, 201)
    return jsonify(data), status


@admin_bp.post("/create-faculty")
@role_required(ADMIN)
def create_faculty():
    try:
        payload = faculty_schema.load(request.get_json() or {})
    except ValidationError as err:
        data, status = error_response("Validation error", 400, str(err.messages))
        return jsonify(data), status

    faculty = Faculty(**payload)
    db.session.add(faculty)
    db.session.commit()
    data, status = success_response("Faculty created", faculty_schema.dump(faculty), 201)
    return jsonify(data), status


@admin_bp.post("/create-department")
@role_required(ADMIN)
def create_department():
    try:
        payload = department_schema.load(request.get_json() or {})
    except ValidationError as err:
        data, status = error_response("Validation error", 400, str(err.messages))
        return jsonify(data), status

    department = Department(**payload)
    db.session.add(department)
    db.session.commit()
    data, status = success_response("Department created", department_schema.dump(department), 201)
    return jsonify(data), status


@admin_bp.post("/create-staff")
@role_required(ADMIN)
def create_staff():
    try:
        payload = staff_create_schema.load(request.get_json() or {})
    except ValidationError as err:
        data, status = error_response("Validation error", 400, str(err.messages))
        return jsonify(data), status

    if Staff.query.filter_by(email=payload["email"].lower()).first():
        data, status = error_response("Staff email already exists", 409)
        return jsonify(data), status

    staff = Staff(
        full_name=payload["full_name"],
        email=payload["email"].lower(),
        role=payload["role"],
        department_id=payload.get("department_id"),
    )
    staff.validate_role()
    staff.set_password(payload["password"])

    db.session.add(staff)
    db.session.commit()
    data, status = success_response("Staff created", staff_schema.dump(staff), 201)
    return jsonify(data), status


@admin_bp.post("/create-course")
@role_required(ADMIN)
def create_course():
    try:
        payload = course_schema.load(request.get_json() or {})
    except ValidationError as err:
        data, status = error_response("Validation error", 400, str(err.messages))
        return jsonify(data), status

    if Course.query.filter_by(course_code=payload["course_code"].upper()).first():
        data, status = error_response("Course code already exists", 409)
        return jsonify(data), status

    lecturer_id = payload.get("lecturer_id")
    if lecturer_id:
        lecturer = Staff.query.get(lecturer_id)
        if not lecturer:
            data, status = error_response("Assigned lecturer does not exist", 404)
            return jsonify(data), status

    course = Course(
        course_code=payload["course_code"].upper(),
        course_title=payload["course_title"],
        credit_units=payload["credit_units"],
        semester=payload["semester"],
        department_id=payload["department_id"],
        lecturer_id=lecturer_id,
    )
    db.session.add(course)
    db.session.commit()
    data, status = success_response("Course created", course_schema.dump(course), 201)
    return jsonify(data), status


@admin_bp.get("/system-stats")
@role_required(ADMIN)
def get_system_stats():
    data, status = success_response("System statistics fetched", system_stats())
    return jsonify(data), status


@admin_bp.post("/bootstrap-structure")
@role_required(ADMIN)
def bootstrap_structure():
    payload = request.get_json() or {}
    uni_name = (payload.get("university_name") or "Future State University").strip()
    uni_location = (payload.get("location") or "Lagos").strip()
    established_year = int(payload.get("established_year") or 1992)
    faculty_name = (payload.get("faculty_name") or "Faculty of Science").strip()
    department_name = (payload.get("department_name") or "Computer Science").strip()

    university = University.query.filter_by(name=uni_name).first()
    if not university:
        university = University(name=uni_name, location=uni_location, established_year=established_year)
        db.session.add(university)
        db.session.flush()

    faculty = Faculty.query.filter_by(name=faculty_name, university_id=university.university_id).first()
    if not faculty:
        faculty = Faculty(name=faculty_name, university_id=university.university_id)
        db.session.add(faculty)
        db.session.flush()

    department = Department.query.filter_by(name=department_name, faculty_id=faculty.faculty_id).first()
    if not department:
        department = Department(name=department_name, faculty_id=faculty.faculty_id)
        db.session.add(department)
        db.session.flush()

    db.session.commit()
    data, status = success_response(
        "Institution structure ready",
        {
            "university": {
                "university_id": university.university_id,
                "name": university.name,
                "location": university.location,
                "established_year": university.established_year,
            },
            "faculty": {"faculty_id": faculty.faculty_id, "name": faculty.name},
            "department": {"department_id": department.department_id, "name": department.name},
        },
        201,
    )
    return jsonify(data), status


@admin_bp.get("/reference-data")
@role_required(ADMIN)
def reference_data():
    universities = University.query.order_by(University.name.asc()).all()
    payload = []
    for uni in universities:
        faculties = Faculty.query.filter_by(university_id=uni.university_id).order_by(Faculty.name.asc()).all()
        faculty_data = []
        for fac in faculties:
            departments = Department.query.filter_by(faculty_id=fac.faculty_id).order_by(Department.name.asc()).all()
            faculty_data.append(
                {
                    "faculty_id": fac.faculty_id,
                    "name": fac.name,
                    "departments": [{"department_id": d.department_id, "name": d.name} for d in departments],
                }
            )
        payload.append(
            {
                "university_id": uni.university_id,
                "name": uni.name,
                "location": uni.location,
                "established_year": uni.established_year,
                "faculties": faculty_data,
            }
        )
    data, status = success_response("Reference data fetched", payload)
    return jsonify(data), status


@admin_bp.get("/university-structure/<int:university_id>")
@role_required(ADMIN)
def university_structure(university_id: int):
    uni = University.query.get(university_id)
    if not uni:
        data, status = error_response("University not found", 404)
        return jsonify(data), status

    faculties = Faculty.query.filter_by(university_id=uni.university_id).order_by(Faculty.name.asc()).all()
    payload = {
        "university_id": uni.university_id,
        "name": uni.name,
        "location": uni.location,
        "established_year": uni.established_year,
        "faculties": [],
    }
    for fac in faculties:
        departments = Department.query.filter_by(faculty_id=fac.faculty_id).order_by(Department.name.asc()).all()
        payload["faculties"].append(
            {
                "faculty_id": fac.faculty_id,
                "name": fac.name,
                "departments": [{"department_id": d.department_id, "name": d.name} for d in departments],
            }
        )

    data, status = success_response("University structure fetched", payload)
    return jsonify(data), status
