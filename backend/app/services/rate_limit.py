from app.services.cache import increment_with_ttl, safe_get, safe_setex


def allow_request(key: str, limit: int, window_seconds: int) -> bool:
    count = increment_with_ttl(key, window_seconds)
    # If Redis is unavailable, fail open for local development instead of taking auth offline.
    return count == 0 or count <= limit


def allow_cooldown(key: str, cooldown_seconds: int) -> bool:
    if safe_get(key):
        return False
    safe_setex(key, cooldown_seconds, "1")
    return True


def check_otp_rate(destination: str) -> None:
    key = f"cc:otp:{destination}"
    if not allow_cooldown(f"{key}:cooldown", 45):
        raise ValueError("Please wait 45 seconds before requesting another OTP")
    if not allow_request(f"{key}:window", 5, 900):
        raise ValueError("Too many OTP requests. Try again later")


def check_message_rate(user_id: int) -> None:
    if not allow_request(f"cc:msg:{user_id}", 40, 300):
        raise ValueError("Too many messages. Please slow down")


def check_offer_rate(user_id: int) -> None:
    if not allow_request(f"cc:offer:{user_id}", 25, 3600):
        raise ValueError("Too many offers. Please try again later")
