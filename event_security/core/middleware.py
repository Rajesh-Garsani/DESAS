
from importlib import import_module
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware

class PerPathSessionMiddleware(SessionMiddleware):

    def _cookie_name_for_request(self, request):
        # adjust this condition if your admin path differs
        if request.path.startswith('/admin/'):
            return getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')
        return getattr(settings, 'USER_SESSION_COOKIE_NAME', settings.SESSION_COOKIE_NAME)

    def process_request(self, request):
        # Load the session using the cookie appropriate for this request
        engine = import_module(settings.SESSION_ENGINE)
        cookie_name = self._cookie_name_for_request(request)
        request.session = engine.SessionStore(request.COOKIES.get(cookie_name))
        # remember which cookie name we used so process_response can re-use it
        request._session_cookie_name = cookie_name

    def process_response(self, request, response):
        # Let the built-in middleware save the session (super handles saving)
        response = super().process_response(request, response)

        # If Django wrote a cookie with the default name, move it to our chosen name
        chosen_name = getattr(request, '_session_cookie_name', None) or self._cookie_name_for_request(request)
        default_name = settings.SESSION_COOKIE_NAME

        if chosen_name != default_name and default_name in response.cookies:
            morsel = response.cookies.pop(default_name)  # remove default cookie
            # build kwargs for set_cookie while preserving attributes
            kwargs = {}
            if morsel.get('max-age'): kwargs['max_age'] = int(morsel['max-age'])
            if morsel.get('expires'): kwargs['expires'] = morsel['expires']
            kwargs['path'] = morsel.get('path', '/')
            if morsel.get('domain'): kwargs['domain'] = morsel['domain']
            kwargs['secure'] = bool(morsel.get('secure'))
            kwargs['httponly'] = bool(morsel.get('httponly'))
            if morsel.get('samesite'): kwargs['samesite'] = morsel['samesite']

            # set the cookie with the new name and the same value/attributes
            response.set_cookie(chosen_name, morsel.value, **{k:v for k,v in kwargs.items() if v is not None})

        return response
