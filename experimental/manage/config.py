import ConfigParser
import re

InterpolationError = ConfigParser.InterpolationError
InterpolationSyntaxError = ConfigParser.InterpolationSyntaxError
NoOptionError = ConfigParser.NoOptionError
NoSectionError = ConfigParser.NoSectionError


class Converter(object):
    """Converts config values to several types.

    Supported types are boolean, float, int, list and unicode.
    """

    _boolean_states = {
        '1':     True,
        'yes':   True,
        'true':  True,
        'on':    True,
        '0':     False,
        'no':    False,
        'false': False,
        'off':   False,
    }

    def to_boolean(self, value):
        key = value.lower()
        if key not in self._boolean_states:
            raise ValueError(
                'Not a boolean: %r. Booleans must be one of %s.' %
                (value, ', '.join(self._boolean_states.keys())))

        return self._boolean_states[key]

    def to_float(self, value):
        return float(value)

    def to_int(self, value):
        return int(value)

    def to_list(self, value):
        value = [line.strip() for line in value.splitlines()]
        return [v for v in value if v]

    def to_unicode(self, value):
        return unicode(value)


class Config(ConfigParser.RawConfigParser):
    """Extended RawConfigParser with the following extra features:

    - All `get*()` functions allow a default to be returned. Instead
      of throwing errors when no section or option is found, it returns the
      default value or None.

    - The `get*()` functions can receive a list of sections to be searched in
      order.

    - A `getlist()` method splits multi-line values into a list.

    - It also implements the magical interpolation behavior similar to the one
      from `SafeConfigParser`, but also supports references to sections.
      This means that values can contain format strings which refer to other
      values in the config file. These variables are replaced on the fly.

    An example of variable substituition is::

        [my_section]
        app_name = my_app
        path = path/to/%(app_name)s

    Here, calling `get('my_section', 'path')` will automatically replace
    variables, resulting in `path/to/my_app`. To get the raw value without
    substitutions, use `get('my_section', 'path', raw=True)`.

    To reference a different section, separate the section and option
    names using a pipe::

        [my_section]
        app_name = my_app

        [my_other_section]
        path = path/to/%(my_section|app_name)s

    If any variables aren't found, a `InterpolationError`is
    raised.

    Variables are case sensitive, differently from the interpolation behavior
    in `SafeConfigParser`.
    """

    converter = Converter()

    _interpolate_re = re.compile(r"%\(([^)]*)\)s")

    def get(self, sections, option, default=None, raw=False):
        """Returns a config value from a given section, converted to unicode.

        :param sections:
            The config section name, or a list of config section names to be
            searched in order.
        :param option:
            The config option name.
        :param default:
            A default value to return in case the section or option are not
            found. Default is None.
        :param raw:
            If True, doesn't perform variable substitution if the value
            has placeholders. Default is False.
        :returns:
            A config value.
        """
        converter = self.converter.to_unicode
        return self._get_many(sections, option, converter, default, raw)

    def getboolean(self, sections, option, default=None, raw=False):
        """Returns a config value from a given section, converted to boolean.

        See :methd:`get` for a description of the parameters.
        """
        converter = self.converter.to_boolean
        return self._get_many(sections, option, converter, default, raw)

    def getfloat(self, sections, option, default=None, raw=False):
        """Returns a config value from a given section, converted to float.

        See :methd:`get` for a description of the parameters.
        """
        converter = self.converter.to_float
        return self._get_many(sections, option, converter, default, raw)

    def getint(self, sections, option, default=None, raw=False):
        """Returns a config value from a given section, converted to int.

        See :methd:`get` for a description of the parameters.
        """
        converter = self.converter.to_int
        return self._get_many(sections, option, converter, default, raw)

    def getlist(self, sections, option, default=None, raw=False):
        """Returns a config value from a given section, converted to boolean.

        See :methd:`get` for a description of the parameters.
        """
        converter = self.converter.to_list
        return self._get_many(sections, option, converter, default, raw)

    def _get(self, section, option):
        """Wrapper for `RawConfigParser.get`."""
        return ConfigParser.RawConfigParser.get(self, section, option)

    def _get_many(self, sections, option, converter, default, raw):
        """Wraps get functions allowing default values and a list of sections
        looked up in order until a value is found.
        """
        if isinstance(sections, basestring):
            sections = [sections]

        for section in sections:
            try:
                value = self._get(section, option)
                if not raw:
                    value = self._interpolate(section, option, value)

                return converter(value)
            except (NoSectionError, NoOptionError):
                pass

        return default

    def _interpolate(self, section, option, raw_value, tried=None):
        """Performs variable substituition in a config value."""
        variables = self._get_variable_names(section, option, raw_value)
        if not variables:
            return raw_value

        if tried is None:
            tried = [(section, option)]

        values = {}
        for var in variables:
            parts = var.split('|', 1)
            if len(parts) == 1:
                new_section, new_option = section, var
            else:
                new_section, new_option = parts

            if parts in tried:
                continue

            try:
                found = self._get(new_section, new_option)
            except (NoSectionError, NoOptionError):
                raise InterpolationError(section, option,
                    'Could not find section %r and option %r.' %
                    (new_section, new_option))

            tried.append((new_section, new_option))
            if not self.has_option(new_section, new_option):
                tried.append(('DEFAULT', new_option))

            values[var] = self._interpolate(new_section, new_option,
                                            found, tried)

        try:
            return raw_value % values
        except KeyError, e:
            raise InterpolationError(section, option,
                'Cound not replace %r: variable %r is missing.' %
                (raw_value, e.args[0]))

    def _get_variable_names(self, section, option, raw_value):
        """Returns a list of placeholder names in a config value, if any.

        Adapted from SafeConfigParser._interpolate_some().
        """
        rv = set()
        while raw_value:
            pos = raw_value.find('%')
            if pos < 0:
                return rv
            if pos > 0:
                raw_value = raw_value[pos:]

            char = raw_value[1:2]
            if char == '%':
                raw_value = raw_value[2:]
            elif char == '(':
                match = self._interpolate_re.match(raw_value)
                if match is None:
                    raise InterpolationSyntaxError(option, section,
                        'Bad interpolation variable reference: %r.' %
                        raw_value)

                rv.add(match.group(1))
                raw_value = raw_value[match.end():]
            else:
                raise InterpolationSyntaxError(option, section,
                    "'%%' must be followed by '%%' or '(', "
                    "found: %r." % raw_value)

        return rv
