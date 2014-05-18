import types
from .utils import to_bool, to_int, to_float


class MetaString(unicode):
    pass

class MetaInt(int):
    pass

class MetaBool(object):
    def __init__(self, value=False):
        self.value = value

    def __nonzero__(self):
        return self.value

    def __repr__(self):
        return repr(self.value)

def to_meta_bool(v, reverse=False):
    if not reverse:
        return MetaBool(to_bool(v))
    return to_bool(v.value, True)

def to_meta_string(v, reverse=False):
    if not reverse:
        return MetaString(v)
    return unicode(v)


marker = object()

class Attribute(object):

    def __init__(self, name, attr_type=types.StringType, xmlns=None,
            value_converter=to_meta_string, mandatory=False,
            default_value=marker):
        self.name = name
        self.attr_type = attr_type
        self.xmlns = xmlns
        self.value_converter = value_converter
        self.mandatory = mandatory
        if default_value is not marker:
            self.default_value = default_value

    def __get__(self, instance, cls):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, self.attr_type) and value is not None:
            if self.value_converter:
                value = self.value_converter(value)
            else:
                raise ValueError("Wrong value type: {0}".format(type(value)))
        instance.__dict__[self.name] = value

    @property
    def full_name(self):
        if self.xmlns:
            return '{{{0.xmlns}}}{0.name}'.format(self)
        return self.name


class IntAttribute(Attribute):

    def __init__(self, name, xmlns=None, mandatory=False):
        super(IntAttribute, self).__init__(name,
            types.IntType,
            value_converter=to_int,
            xmlns=xmlns,
            mandatory=mandatory)


class BoolAttribute(Attribute):

    def __init__(self, name, xmlns=None, mandatory=False):
        super(BoolAttribute, self).__init__(name,
            types.BooleanType,
            value_converter=to_bool,
            xmlns=xmlns,
            mandatory=mandatory)

class Tag(object):

    def __init__(self, name,
            attributes=(),
            child_tags=(),
            xmlns=None,
            list_in_parent=True,
            prop_name=None,
            is_prop_tag=False,
            content_type=MetaString,
            content_converter=to_meta_string,
            aliases=()):
        self.name = name
        self.attributes = attributes
        self.xmlns = xmlns
        self.child_tags = child_tags
        self.list_in_parent = list_in_parent
        self.prop_name = prop_name
        if self.prop_name is None:
            self.prop_name = self.name[0].lower() + self.name[1:]
        self.is_prop_tag = is_prop_tag
        # makes sence only if is_prop_tag == True
        self.content_type = content_type
        self.content_converter = content_converter
        self.aliases = aliases

    @property
    def full_name(self):
        if self.xmlns:
            return "{%s}%s" % (self.xmlns, self.name)
        return self.name

    def get_child_tag(self, elm):
        for ct in self.child_tags:
            if elm.tag == ct.full_name:
                return ct
        return None

    def __repr__(self):
        return '<Tag {0}>'.format(self.name)

    def convert(self, value):
        if not self.is_prop_tag:
            raise ValueError("Cannot convert non-property tag value")
        if not isinstance(value, self.content_type) and value is not None:
            if self.content_converter:
                value = self.content_converter(value)
            else:
                raise ValueError("Wrong value type")
        return value


class PropertyTag(Tag):
    """ a simple tag with content (no attributes) """
    def __init__(self, name, prop_name=None,
            content_type=MetaString,
            list_in_parent=False,
            content_converter=to_meta_string,
            xmlns=None,
            attributes=()):
        super(PropertyTag, self).__init__(name,
            prop_name=prop_name,
            child_tags=(),
            attributes=attributes,
            is_prop_tag=True,
            list_in_parent=list_in_parent,
            xmlns=xmlns,
            content_type=content_type,
            content_converter=content_converter)

    def __repr__(self):
        return '<PropertyTag {0}>'.format(self.name)


class BoolPropertyTag(PropertyTag):

    def __init__(self, name, prop_name=None, xmlns=None):
        super(BoolPropertyTag, self).__init__(name, prop_name,
            types.BooleanType, content_converter=to_bool, xmlns=xmlns)

class ListPropertyTag(PropertyTag):

    def __init__(self, name, prop_name=None, xmlns=None):
        super(ListPropertyTag, self).__init__(name, prop_name,
            types.ListType, xmlns=xmlns)


class IntPropertyTag(PropertyTag):

    def __init__(self, name, prop_name=None, xmlns=None):
        super(IntPropertyTag, self).__init__(name, prop_name,
            types.IntType, content_converter=to_int, xmlns=xmlns)


class FloatPropertyTag(PropertyTag):

    def __init__(self, name, prop_name=None, xmlns=None):
        super(FloatPropertyTag, self).__init__(name, prop_name,
            types.FloatType, content_converter=to_float, xmlns=xmlns)

