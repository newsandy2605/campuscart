import os
from functools import lru_cache


class Settings:
    app_name = os.getenv("APP_NAME", "CampusCart API")
    app_env = os.getenv("APP_ENV", "development")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://campuscart:campuscart@db:5432/campuscart",
    )
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    saleor_api_url = os.getenv(
        "SALEOR_API_URL", "http://host.docker.internal:8000/graphql/"
    )
    saleor_token = os.getenv("SALEOR_TOKEN", "")
    saleor_webhook_secret = os.getenv("SALEOR_WEBHOOK_SECRET", "")
    saleor_channel = os.getenv("SALEOR_CHANNEL", "default-channel")

    media_dir = os.getenv("MEDIA_DIR", "/app/uploads")
    storage_provider = os.getenv("STORAGE_PROVIDER", "local")
    s3_bucket = os.getenv("S3_BUCKET", "")
    s3_region = os.getenv("S3_REGION", "")
    s3_endpoint_url = os.getenv("S3_ENDPOINT_URL", "")
    s3_public_base_url = os.getenv("S3_PUBLIC_BASE_URL", "")
    s3_access_key_id = os.getenv("S3_ACCESS_KEY_ID", "")
    s3_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY", "")

    campus_verification_mode = os.getenv("CAMPUS_VERIFICATION_MODE", "domain_or_admin")
    sentry_dsn = os.getenv("SENTRY_DSN", "")

    jwt_secret = os.getenv(
        "JWT_SECRET",
        "local-development-secret-change-before-prod-1234567890",
    )
    jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
    password_reset_ttl_seconds = int(os.getenv("PASSWORD_RESET_TTL_SECONDS", "900"))
    handoff_secret = os.getenv("HANDOFF_SECRET", jwt_secret)

    cors_origins = [
        x.strip()
        for x in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if x.strip()
    ]

    otp_ttl_seconds = int(os.getenv("OTP_TTL_SECONDS", "600"))
    otp_max_attempts = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    dev_otp_echo = os.getenv("DEV_OTP_ECHO", "true").lower() == "true"

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", "noreply@campuscart.local")
    smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"

    sms_provider = os.getenv("SMS_PROVIDER", "")
    sms_webhook_url = os.getenv("SMS_WEBHOOK_URL", "")
    twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_verify_service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID", "")

    payment_provider = os.getenv("PAYMENT_PROVIDER", "local")
    razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    razorpay_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    platform_fee_percent = float(os.getenv("PLATFORM_FEE_PERCENT", "0"))

    def validate(self):
        if self.app_env.lower() == "production":
            if len(self.jwt_secret) < 32 or self.jwt_secret.startswith("local-") or "change-before-prod" in self.jwt_secret:
                raise RuntimeError("JWT_SECRET must be a strong production secret")
            if len(self.handoff_secret) < 32 or self.handoff_secret == self.jwt_secret:
                raise RuntimeError("HANDOFF_SECRET must be a separate production secret")
            if not self.cors_origins or any("localhost" in origin for origin in self.cors_origins):
                raise RuntimeError("Production CORS_ORIGINS must not contain localhost")
            if self.dev_otp_echo:
                raise RuntimeError("DEV_OTP_ECHO must be false in production")
            if not self.smtp_host or not self.smtp_from:
                raise RuntimeError("SMTP_HOST and SMTP_FROM are required for email OTP delivery in production")
            if self.sms_provider.lower() == "twilio" and (not self.twilio_account_sid or not self.twilio_auth_token or not self.twilio_verify_service_sid):
                raise RuntimeError("Twilio credentials are required when SMS_PROVIDER=twilio")
            if self.sms_webhook_url and not self.sms_webhook_url.startswith("https://"):
                raise RuntimeError("SMS_WEBHOOK_URL must use HTTPS in production")
            if self.payment_provider == "razorpay" and (not self.razorpay_key_id or not self.razorpay_key_secret or not self.razorpay_webhook_secret):
                raise RuntimeError("Razorpay key, secret and webhook secret are required when PAYMENT_PROVIDER=razorpay")
            if self.storage_provider.lower() == "s3" and (not self.s3_bucket or not self.s3_region or not self.s3_access_key_id or not self.s3_secret_access_key):
                raise RuntimeError("S3_BUCKET, S3_REGION, S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY are required when STORAGE_PROVIDER=s3")
            if self.campus_verification_mode not in {"domain_or_admin", "admin_only", "development_allow_contact"}:
                raise RuntimeError("Invalid CAMPUS_VERIFICATION_MODE")


@lru_cache(maxsize=1)
def get_settings():
    return Settings()


settings = get_settings()
