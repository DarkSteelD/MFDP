from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    smt_token: str
    model_config = SettingsConfigDict(
        extra='ignore',
        env_file='.env',
        env_file_encoding='utf-8'
    )