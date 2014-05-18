import re
import datetime

def to_bool(s, reverse=False):
    if not reverse:
        if isinstance(s, basestring):
            return s.lower() in ('true', 'yes', 't', 'y', '1')
        return bool(s)
    return str(s).lower()

def to_int(v, reverse=False):
    if not reverse:
        return int(v)
    return str(v)

def to_float(v, reverse=False):
    if not reverse:
        return float(v)
    return str(v)

