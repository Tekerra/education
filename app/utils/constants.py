ADMIN = "ADMIN"
DEAN = "DEAN"
HOD = "HOD"
COURSE_ADVISOR = "COURSE_ADVISOR"
LECTURER = "LECTURER"
STUDENT = "STUDENT"

STAFF_ROLES = {ADMIN, DEAN, HOD, COURSE_ADVISOR, LECTURER}
ALL_ROLES = STAFF_ROLES | {STUDENT}

GRADE_SCALE = [
    (70, "A"),
    (60, "B"),
    (50, "C"),
    (45, "D"),
    (40, "E"),
    (0, "F"),
]

GRADE_POINTS = {
    "A": 5.0,
    "B": 4.0,
    "C": 3.0,
    "D": 2.0,
    "E": 1.0,
    "F": 0.0,
}

RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"

