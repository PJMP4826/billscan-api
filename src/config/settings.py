import urllib.parse
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )  # type: ignore

    # LLM Configuracion
    google_api_key: str = Field(..., description="Google API Key")
    llm_gemini_model: str = Field(..., description="Gemini Model")

    # Database configuration
    db_user: str = Field(..., description="Database username")
    db_password: str = Field(..., description="Database password")
    db_name: str = Field(..., description="Database name")
    db_port: str = Field(default="5432", description="Database port")
    db_host: str = Field(..., description="Database host")

    # Cloudflare R2 (S3-compatible) File Storage
    r2_account_id: str = Field(..., description="Cloudflare R2 account ID")
    r2_access_key_id: str = Field(..., description="Cloudflare R2 access key ID")
    r2_secret_access_key: str = Field(
        ..., description="Cloudflare R2 secret access key"
    )
    r2_bucket_name: str = Field(..., description="Cloudflare R2 bucket name")
    r2_public_base_url: str | None = Field(
        default=None,
        description="Optional public base URL for the R2 bucket",
    )

    # Billing Providers

    # FacturaGPT Provider Credentials
    facturagpt_base_url: str = Field(..., description="Base FacturaGPT API EndPoint")
    facturagpt_api_key: str = Field(..., description="FacturaGPT API KEY")
    facturagpt_test_mode: bool = Field(
        default=False, description="FacturaGPT Test Mode"
    )
    # Webhook signing secret (whsec_...) del Partner Dashboard de FacturaGPT.
    # Opcional en settings para no romper el arranque; se exige al construir
    # el handler (cuando llega el primer webhook o se arma el worker).
    facturagpt_webhook_secret: str = Field(
        description="FacturaGPT Webhook signing secret (whsec_...)",
    )

    # Security Configuration
    # Data Encryptors

    encryption_key: str = Field(..., description="Data Encryption Key")

    @property
    def database_url(self) -> str:
        user = urllib.parse.quote_plus(self.db_user)
        password = urllib.parse.quote_plus(self.db_password)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()  # type: ignore
