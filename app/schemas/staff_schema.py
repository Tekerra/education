from marshmallow import fields, validate

from app.extensions import ma
from app.utils.constants import STAFF_ROLES


class StaffCreateSchema(ma.Schema):
    full_name = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(required=True, validate=validate.OneOf(sorted(STAFF_ROLES)))
    department_id = fields.Int(load_default=None)


class StaffSchema(ma.Schema):
    staff_id = fields.Int(dump_only=True)
    full_name = fields.Str(required=True)
    email = fields.Email(required=True)
    role = fields.Str(required=True)
    department_id = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)

