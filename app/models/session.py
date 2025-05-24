from tortoise import fields, models


class Session(models.Model):
    id = fields.IntField(pk=True)
    # user: fields.ForeignKeyRelation["models.User"] = fields.ForeignKeyField( # Corrected type hint
    user: fields.ForeignKeyRelation["app.models.users.User"] = (
        fields.ForeignKeyField(  # More explicit for Tortoise
            "models.User", related_name="sessions", on_delete=fields.CASCADE
        )
    )  # "models.User" refers to the User model in the 'models' app (as defined in TORTOISE_ORM_CONFIG)
    # related_name="sessions" allows access from User object like user.sessions
    refresh_token = fields.CharField(
        max_length=512, unique=True, index=True
    )  # Increased length for safety
    expires_at = fields.DatetimeField(index=True)
    created_at = fields.DatetimeField(auto_now_add=True)  # Tortoise uses auto_now_add
    is_active = fields.BooleanField(default=True, index=True)

    def __str__(self):
        return f"Session for user {self.user_id} - Token: {self.refresh_token[:20]}..."
