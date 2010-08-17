"""Adds the Authorization header introduced in WebOb 0.9.7."""
import webob
import webapp2

# see http://lists.w3.org/Archives/Public/ietf-http-wg/2009OctDec/0297.html
known_auth_schemes = ['Basic', 'Digest', 'WSSE', 'HMACDigest', 'GoogleLogin',
    'Cookie', 'OpenID']
known_auth_schemes = dict.fromkeys(known_auth_schemes, None)


def parse_auth(val):
    if val is not None:
        authtype, params = val.split(' ', 1)
        if authtype in known_auth_schemes:
            if authtype == 'Basic' and '"' not in params:
                # this is the "Authentication: Basic XXXXX==" case
                pass
            else:
                params = webob.parse_params(params)
        return authtype, params
    return val


def serialize_auth(val):
    if isinstance(val, (tuple, list)):
        authtype, params = val
        if isinstance(params, dict):
            params = ', '.join(map('%s="%s"'.__mod__, params.items()))
        assert isinstance(params, str)
        return '%s %s' % (authtype, params)
    return val


class Request(webapp2.Request):
    authorization = webob.converter(
        webob.header_getter('Authorization', rfc_section='14.8'),
        parse_auth, serialize_auth,
    )
