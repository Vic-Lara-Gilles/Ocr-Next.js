from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self._repository = UserRepository(db)

    def register(self, name: str, email: str, password: str) -> User:
        existing = self._repository.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        hashed = self._hash_password(password)
        return self._repository.create(name, email, hashed)

    def authenticate(self, email: str, password: str) -> User:
        user = self._repository.get_by_email(email)
        if not user or not self._verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        return user

    def create_access_token(self, user_id: UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXPIRATION_MINUTES
        )
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    def decode_token(self, token: str) -> UUID:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return UUID(payload["sub"])

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
