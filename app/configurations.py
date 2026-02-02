import pydantic_settings


class EnvConfigs(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-2024-08-06"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379


settings = EnvConfigs()
