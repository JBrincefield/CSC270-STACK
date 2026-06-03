from django.conf import settings


def firebase_context(request):
    """Inject Firebase web config and current authenticated user into every template."""
    uid = request.session.get('user_uid')
    current_user = None
    if uid:
        current_user = {
            'uid': uid,
            'email': request.session.get('user_email', ''),
            'name': request.session.get('user_name', ''),
            'is_admin': request.session.get('is_admin', False),
        }
    return {
        'current_user': current_user,
        'firebase_config': settings.FIREBASE_WEB_CONFIG,
    }
