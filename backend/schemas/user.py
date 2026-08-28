from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: int | None = None
    gender: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserProfileUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None