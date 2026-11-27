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

    # Billing quota
    billing_max_invoices_per_rfc: int = Field(
        default=3,
        description="Máximo de facturas permitidas por RFC",
    )
    billing_storage_max_retries: int = Field(
        default=3,
        description=(
            "Reintentos del job de timbrado ante fallos transitorios de "
            "almacenamiento (R2)"
        ),
    )
    billing_storage_retry_delay_seconds: float = Field(
        default=5.0,
        description="Delay inicial (segundos) antes de reencolar el timbrado",
    )
    rfc_hash_secret: str = Field(
        default="",
        description=(
            "Secreto para el fingerprint HMAC-SHA256 del RFC. "
            "Si está vacío se usa encryption_key."
        ),
    )

    # Push Notifications (Expo)
    expo_push_base_url: str = Field(
        default="https://exp.host",
        description="Base URL de la Expo Push API",
    )
    expo_push_access_token: str = Field(
        default="",
        description=(
            "Access token de Expo. Solo se requiere si push security está "
            "habilitado en el dashboard."
        ),
    )
    expo_push_timeout_seconds: float = Field(
        default=10.0,
        description="Timeout por petición a Expo (segundos)",
    )
    expo_push_max_retries: int = Field(
        default=2,
        description="Reintentos para respuestas 429/5xx de Expo",
    )
    expo_push_retry_min_delay_seconds: float = Field(
        default=1.0,
        description="Delay base (segundos) del backoff exponencial ante 429/5xx",
    )
    expo_push_max_messages_per_request: int = Field(
        default=100,
        description="Máximo de mensajes por petición de envío a Expo",
    )
    expo_push_max_receipts_per_request: int = Field(
        default=1000,
        description="Máximo de ids por petición de recibos a Expo",
    )

    # Security Configuration
    # Data Encryptors

    encryption_key: str = Field(..., description="Data Encryption Key")

    # Clerk Auth. El secret key se valida al construir el verificador (primer
    # request autenticado), no al arrancar, para no romper el boot en entornos
    # que todavía no lo configuran.
    clerk_secret_key: str = Field(default="", description="Clerk Secret Key")
    clerk_authorized_parties: str = Field(
        default="",
        description="Orígenes permitidos para el token, separados por coma",
    )
    clerk_audience: str | None = Field(
        default=None, description="Audience opcional del JWT de Clerk"
    )

    @property
    def clerk_authorized_parties_list(self) -> list[str] | None:
        parties = [
            party.strip()
            for party in self.clerk_authorized_parties.split(",")
            if party.strip()
        ]
        return parties or None

    @property
    def database_url(self) -> str:
        user = urllib.parse.quote_plus(self.db_user)
        password = urllib.parse.quote_plus(self.db_password)

        url = (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

        # Si se conecta a una base de datos remota (como Supabase), exige SSL
        if self.db_host != "postgres" and "localhost" not in self.db_host:
            url += "?ssl=require"

        return url


settings = Settings()  # type: ignore
