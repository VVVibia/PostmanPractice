from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from pydantic import SecretStr

from src.app.api.schemas.auth import Token


class SecurityService:
    _algorithm = 'HS256'
    _pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    def __init__(self, secret_key: SecretStr, token_ttl: int) -> None:
        self.secret_key = secret_key.get_secret_value()
        self.token_ttl = token_ttl

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def create_access_token(
        self,
        subject: str,
    ) -> Token:
        expire = datetime.utcnow() + timedelta(minutes=self.token_ttl)
        to_encode = {'exp': expire, 'sub': subject}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self._algorithm)
        return Token(access_token=encoded_jwt)

    def get_email_from_token(self, token: str):
        payload = jwt.decode(token, self.secret_key, algorithms=[self._algorithm])
        return payload['sub']
