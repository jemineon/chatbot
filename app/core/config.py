from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastAPI Learning Project"
    app_version: str = "0.1.0"
    debug: bool = True
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_user: str = "fastapi_user"
    mysql_password: str = "fastapi_password"
    mysql_database: str = "fastapi_app"

    # .env file and real environment variables are both read from here.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
