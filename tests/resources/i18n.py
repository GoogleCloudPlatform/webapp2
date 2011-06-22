from webapp2_extras import config
from webapp2_extras import i18n

default_config = {
    'locale': 'en_US',
    'timezone': 'America/Chicago',
    'required': config.REQUIRED_VALUE,
}

def locale_selector(request, store):
    return i18n.get_store().default_locale

def timezone_selector(request, store):
    return i18n.get_store().default_timezone
