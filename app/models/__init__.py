from app.models.analytics_result import AnalyticsResult
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.staff import Staff
from app.models.student import Student
from app.models.university import University

__all__ = [
    "University",
    "Faculty",
    "Department",
    "Staff",
    "Student",
    "Course",
    "Enrollment",
    "Assessment",
    "AnalyticsResult",
]
