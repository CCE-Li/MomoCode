from fastapi import Response

from app.core.config import get_settings

_settings = get_settings()


def set_auth_cookies(
    response: Response,
    session_token: str,
    csrf_token: str,
) -> None:
    max_age = _settings.session_ttl_days * 24 * 60 * 60
    response.set_cookie(
        key=_settings.session_cookie_name,
        value=session_token,
        max_age=max_age,
        httponly=True,
        secure=_settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=_settings.csrf_cookie_name,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=_settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=_settings.session_cookie_name, path="/")
    response.delete_cookie(key=_settings.csrf_cookie_name, path="/")
