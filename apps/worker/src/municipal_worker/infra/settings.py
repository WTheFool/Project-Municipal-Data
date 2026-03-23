from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    rq_queue_name: str = "municipal_default"

    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "municipal-data"
    s3_region: str = "us-east-1"
    s3_secure: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()
