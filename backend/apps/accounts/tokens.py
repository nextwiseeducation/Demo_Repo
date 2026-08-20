from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

_signer = TimestampSigner(salt="email-verification")

VERIFICATION_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 3  # 3 days


def make_verification_token(user_id) -> str:
    return _signer.sign(str(user_id))


def read_verification_token(token: str) -> str | None:
    """Returns the user id encoded in the token, or None if invalid/expired."""
    try:
        return _signer.unsign(token, max_age=VERIFICATION_TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
