from marshmallow import fields

from app.extensions import ma


class UniversitySchema(ma.Schema):
    university_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    location = fields.Str(required=True)
    established_year = fields.Int(required=True)


class FacultySchema(ma.Schema):
    faculty_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    university_id = fields.Int(required=True)


class DepartmentSchema(ma.Schema):
    department_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    faculty_id = fields.Int(required=True)

