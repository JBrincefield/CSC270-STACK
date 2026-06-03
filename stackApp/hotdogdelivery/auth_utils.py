"""Firebase auth helpers for the Hotdog Delivery app.

This module bridges Firebase Authentication and Django's session system.
Users sign in with Firebase on the frontend, the backend verifies the ID
token, and then stores a small session payload so the rest of the app can
use normal Django request/session checks.
"""

from __future__ import annotations

import json
from typing import Any

from django.conf import settings

from . import dal


dal.init_app()


def _firebase_auth():
    from firebase_admin import auth as firebase_auth

    return firebase_auth


def web_config_ready() -> bool:
    return bool(getattr(settings, 'FIREBASE_WEB_CONFIG_READY', False))


def get_web_config() -> dict[str, str]:
    return dict(getattr(settings, 'FIREBASE_WEB_CONFIG', {}))


def get_web_config_json() -> str:
    return json.dumps(get_web_config())


def firebase_context_processor(request):
    user = get_session_user(request)
    config_ready = web_config_ready()
    return {
        'firebase_web_config': get_web_config() if config_ready else None,
        'firebase_web_config_json': get_web_config_json() if config_ready else '',
        'auth_user': user,
        'auth_is_authenticated': bool(user),
        'auth_is_admin': bool(user and user.get('isAdmin')),
    }


def is_admin_claim(claims: dict[str, Any] | None) -> bool:
    if not claims:
        return False
    return bool(claims.get('admin') or claims.get('role') == 'admin')


def user_payload_from_claims(claims: dict[str, Any]) -> dict[str, Any]:
    return {
        'uid': claims.get('uid', ''),
        'email': claims.get('email', ''),
        'displayName': claims.get('name') or claims.get('display_name') or claims.get('email', ''),
        'photoURL': claims.get('picture', ''),
        'isAdmin': is_admin_claim(claims),
    }


def get_session_user(request) -> dict[str, Any] | None:
    return request.session.get('firebase_user')


def set_session_user(request, claims: dict[str, Any]) -> dict[str, Any]:
    user = user_payload_from_claims(claims)
    request.session['firebase_user'] = user
    request.session.set_expiry(60 * 60 * 24 * 7)
    return user


def clear_session_user(request) -> None:
    request.session.flush()


def verify_id_token(id_token: str) -> dict[str, Any]:
    firebase_auth = _firebase_auth()
    return firebase_auth.verify_id_token(id_token, check_revoked=False)


def grant_admin_role(uid: str, enabled: bool = True) -> None:
    firebase_auth = _firebase_auth()
    claims = {'admin': True} if enabled else {}
    firebase_auth.set_custom_user_claims(uid, claims)


def get_user_record(uid: str):
    firebase_auth = _firebase_auth()
    return firebase_auth.get_user(uid)


def user_label(user: dict[str, Any] | None) -> str:
    if not user:
        return 'Guest'
    return user.get('displayName') or user.get('email') or 'Guest'
