def user_role(request):
    if request.user.is_authenticated:
        return {
            'user_role': request.user.role,
            'is_admin': request.user.is_admin(),
            'is_event_registrar': request.user.is_event_registrar(),
            'is_security_guard': request.user.is_security_guard(),
        }
    return {}