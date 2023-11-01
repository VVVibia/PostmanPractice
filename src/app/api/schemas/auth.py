from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(
        description='Токен доступа. Используется в дальнейшем для авторизации.',
        example='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTA4MjE4NjMsInN1YiI6ImEudHVsYWtpbkBjZnQucnUifQ.wLs9AFe2rIc2BiFW3z7jDgnyWHj8eyTKAZHSQ2jxnBk',  # noqa
    )
    token_type: str = Field('bearer', description='Тип токена')
