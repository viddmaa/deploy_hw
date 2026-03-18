import re

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserCreate(BaseModel):
    username: str = Field(
        min_length=4,
        max_length=20,
        pattern=r"^[A-Za-z0-9]+$",
        description="Username must contain only letters and digits",
    )
    email: EmailStr
    password: str
    confirm_password: str
    age: int = Field(ge=18, le=100)

    @model_validator(mode="after")
    def validate_user_data(self) -> "UserCreate":
        password = self.password

        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*]", password):
            raise ValueError("Password must contain at least one special character: !@#$%^&*")

        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self