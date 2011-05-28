from __future__ import absolute_import
from pygments.style import Style
from pygments.token import *


COLOR_1 = '#e6dccc'
COLOR_2 = '#1e214f'
COLOR_3 = '#b5242e'
COLOR_4 = '#1e4f34'
COLOR_5 = '#537b99'


class pygapp2(Style):
    default_style = ""
    styles = {
        Comment: 'italic ' + COLOR_5,
        Keyword: 'bold ' + COLOR_2,
        Operator: 'bold ' + COLOR_4,
        Punctuation: '#777',
        Number: COLOR_4,
        Name: '#000',
        Name.Decorator: 'bold ' + COLOR_2,
        Name.Builtin: COLOR_2,
        Name.Exception: 'bold ' + COLOR_3,
        Generic.Error: 'bold ' + COLOR_3,
        String: COLOR_3
    }
