from app.extensions import db
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.staff import Staff
from app.models.student import Student
from app.models.university import University
from app.utils.constants import ADMIN, COURSE_ADVISOR, HOD, LECTURER


def _get_or_create(model, defaults=None, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = dict(defaults or {})
    params.update(kwargs)
    instance = model(**params)
    db.session.add(instance)
    db.session.flush()
    return instance, True


def bootstrap_demo_data():
    created_any = False

    uni, created = _get_or_create(
        University,
        name="Future State University",
        location="Lagos",
        established_year=1992,
    )
    created_any = created_any or created

    faculty, created = _get_or_create(Faculty, name="Faculty of Science", university_id=uni.university_id)
    created_any = created_any or created

    department, created = _get_or_create(Department, name="Computer Science", faculty_id=faculty.faculty_id)
    created_any = created_any or created

    def ensure_staff(email, full_name, role, password, department_id=None):
        nonlocal created_any
        staff = Staff.query.filter_by(email=email).first()
        if staff:
            return staff
        staff = Staff(
            full_name=full_name,
            email=email,
            role=role,
            department_id=department_id,
        )
        staff.set_password(password)
        db.session.add(staff)
        db.session.flush()
        created_any = True
        return staff

    ensure_staff("admin@university.edu", "System Administrator", ADMIN, "admin123", None)
    ensure_staff(
        "hod@university.edu",
        "Head of Department",
        HOD,
        "hod12345",
        department.department_id,
    )
    lecturer = ensure_staff(
        "lecturer@university.edu",
        "Course Lecturer",
        LECTURER,
        "lecturer123",
        department.department_id,
    )
    advisor = ensure_staff(
        "advisor@university.edu",
        "Course Advisor",
        COURSE_ADVISOR,
        "advisor123",
        department.department_id,
    )

    course, created = _get_or_create(
        Course,
        course_code="CSC401",
        defaults={
            "course_title": "Advanced Data Analytics",
            "credit_units": 3,
            "semester": "FIRST",
            "department_id": department.department_id,
            "lecturer_id": lecturer.staff_id,
        },
    )
    if not course.lecturer_id:
        course.lecturer_id = lecturer.staff_id
    created_any = created_any or created

    students = []
    for idx in range(1, 6):
        matric = f"CSC/2022/10{idx}"
        student = Student.query.filter_by(matric_no=matric).first()
        if not student:
            student = Student(
                matric_no=matric,
                full_name=f"Student {idx}",
                gender="M" if idx % 2 else "F",
                level=400,
                department_id=department.department_id,
                advisor_id=advisor.staff_id,
            )
            student.set_password("student123")
            db.session.add(student)
            db.session.flush()
            created_any = True
        students.append(student)

    for student in students:
        _, created = _get_or_create(
            Enrollment,
            student_id=student.student_id,
            course_id=course.course_id,
            session="2025/2026",
            semester="FIRST",
        )
        created_any = created_any or created

    db.session.commit()
    return {"bootstrapped": created_any, "message": "Demo data ready"}

