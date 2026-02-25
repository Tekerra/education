from app import create_app
from app.services.bootstrap_service import bootstrap_demo_data

app = create_app()


with app.app_context():
    result = bootstrap_demo_data()
    print(result.get("message", "Seed completed"))
    print("Admin login: admin@university.edu / admin123")
    print("HOD login: hod@university.edu / hod12345")
    print("Lecturer login: lecturer@university.edu / lecturer123")
    print("Advisor login: advisor@university.edu / advisor123")
    print("Student login identifier example: CSC/2022/101 / student123")

