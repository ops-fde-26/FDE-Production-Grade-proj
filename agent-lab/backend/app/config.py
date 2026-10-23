from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "agent lab"
    debug: bool = True


settings = Settings()
