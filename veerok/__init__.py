from lxml import objectify, etree
import types
import datetime
import re

from .meta import Attribute

EMPTY_MARKER = object()

def remove_ns(elm):
    t = elm.tag
    idx = t.find('}')
    return t if idx == -1 else t[idx+1:]

def is_prop_tag(name):
    v = globals().get(name)
    return v and isinstance(v, PropertyTag)

def mk_prop_name(name):
    """ creates a camel-cases name
        override in subclasses when needed
    """
    return name[0].lower() + name[1:]

class VeerokBase(object):

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __repr__(self):
        data = []
        for k, v in self.__dict__.items():
            data.append('{0}={1}'.format(k, v))
        return '<{0.__class__.__name__} {1}>'.format(self, ', '.join(data))

    def pretty_format(self, indent_lvl=1, ident_str='    '):
        ret = ['{0.__class__.__name__}'.format(self)]
        for k, v in self.__dict__.iteritems():
            if isinstance(v, VeerokBase):
                ret.append('{0}{1}={2}'.format(ident_str * indent_lvl, k, v.pretty_format(indent_lvl+1)))
            else:
                ret.append('{0}{1}={2}'.format(ident_str * indent_lvl, k, v))
        return "\n".join(ret)

    def to_element(self, root_tag, nsmap=None):
        """ create an etree element from XML tag """
        def_ns = None
        if nsmap and nsmap.has_key(None):
            def_ns = nsmap[None]
        root_elm = etree.Element(root_tag.full_name, nsmap=nsmap)
        for attr in root_tag.attributes:
            if hasattr(self, attr.name):
                an = attr.full_name
                if attr.xmlns == def_ns:
                    an = attr.name
                val = getattr(self, attr.name)
                if val is not None:
                    if attr.value_converter:
                        val = attr.value_converter(val, reverse=True)
                    root_elm.set(an, val)

        for child_tag in root_tag.child_tags:
            ctn = mk_prop_name(child_tag.name)

            if child_tag.prop_name:
                ctn = child_tag.prop_name

            if not child_tag.is_prop_tag:
                if hasattr(self, ctn):
                    val = getattr(self, ctn)
                    if isinstance(val, types.ListType) or child_tag.list_in_parent:
                        for i in val:
                            root_elm.append(i.to_element(child_tag, nsmap))
                    else:
                        root_elm.append(val.to_element(child_tag, nsmap))
            else:
                if hasattr(self, child_tag.prop_name):
                    fn = child_tag.full_name
                    if child_tag.xmlns == def_ns:
                        fn = child_tag.name
                    child = etree.SubElement(root_elm, fn)
                    val = getattr(self, child_tag.prop_name)
                    if child_tag.content_converter:
                        val = child_tag.content_converter(val, reverse=True)
                    else:
                        val = str(val)
                    child.text = val

        return root_elm

    def to_xml(self, nsmap=None):
        root_tag = self._tag_def_
        elm = self.to_element(root_tag, nsmap)
        return etree.tostring(elm, pretty_print=True)

class VeerokParser(object):

    __class_cache__ = dict()

    def __init__(self, known_tags, base_class=VeerokBase):
        self.base_class = base_class
        self._tags_map = dict()
        for tag in known_tags:
            self._tags_map[tag.name] = tag

    def parse_xml(self, xml, strict=False):
        root = objectify.fromstring(xml)
        return self._parse_etree(root, None, strict)

    def _parse_etree(self, root, tag=None, strict=False):
        if not tag:
            tag = self._tags_map.get(remove_ns(root))
            if tag is None:
                if strict:
                    raise Exception("Unknown tag: {0}".format(remove_ns(root)))
                return None

        if tag.xmlns and root.tag != tag.full_name:
            raise Exception("Result type mismatch, expected {0}, got {1}".format(tag_with_ns, root.tag))

        # iterate through all child names and build a set of unique names
        child_names = set()
        for child in root.iterchildren():
            child_name = remove_ns(child)
            allowed = tag.get_child_tag(child)
            if allowed:
                child_names.add(child_name)

        cls_attribs = {
            '_tag_def_': tag
        }
        tag_attributes = list(tag.attributes)

        for attrib in tag_attributes:
            cls_attribs[attrib.name] = attrib

        klass = self.__class_cache__.get(tag.full_name)
        if not klass:
            klass = type(tag.name, (self.base_class,), cls_attribs)
            self.__class_cache__[tag.full_name] = klass

        for child_name in child_names:
            tag_attributes.append(Attribute(child_name, types.ListType))

        vals = dict()
        for attrib in tag.attributes: # don't add child types yet
            attr_name = attrib.name
            if not root.attrib.has_key(attrib.name) and not root.attrib.has_key(attrib.full_name):
                if not attrib.mandatory:
                    vals[attrib.name] = None
                    continue
                if hasattr(attrib, 'default_value'):
                    vals[attrib.name] = attrib.default_value
                    continue
                raise ValueError("Missing mandatory attribute: {0.name} for {1.name}".format(attrib, tag))
            # try full name first:
            val = root.attrib.get(attrib.full_name, EMPTY_MARKER)
            if val is EMPTY_MARKER:
                val = root.attrib[attr_name]
            vals[attrib.name] = val

        instance = klass(**vals)

        for child in root.iterchildren():
            child_tag_name = remove_ns(child)
            child_tag = tag.get_child_tag(child)
            if not child_tag:
                continue
            child_prop_name = mk_prop_name(child_tag_name)
            if not child_tag.is_prop_tag:
                child_instance = self._parse_etree(child, child_tag, strict=strict)
                if child_instance:
                    if child_tag.list_in_parent:
                        child_prop_name = child_tag.prop_name or child_prop_name
                        if not getattr(instance, child_prop_name, None):
                            setattr(instance, child_prop_name, [])
                        getattr(instance, child_prop_name).append(child_instance)
                    else:
                        child_prop_name = child_tag.prop_name or child_prop_name
                        setattr(instance, child_prop_name, child_instance)
            else:
                val = child_tag.convert(child.text)
                for attrib in child_tag.attributes:
                    attr_name = attrib.name
                    if not child.attrib.has_key(attrib.name) and not child.attrib.has_key(attrib.full_name):
                        if not attrib.mandatory:
                            setattr(val, attrib.name, None)
                            continue
                        raise ValueError("Missing mandatory attribute: {0.name} for {1.name}".format(attrib, tag))
                    # try full name first:
                    attr_val = child.attrib.get(attrib.full_name, EMPTY_MARKER)
                    if attr_val is EMPTY_MARKER:
                        attr_val = child.attrib[attr_name]
                    setattr(val, attrib.name, attr_val)
                if child_tag.list_in_parent:
                    if not getattr(instance, child_tag.prop_name, None):
                        setattr(instance, child_tag.prop_name, [])
                    getattr(instance, child_tag.prop_name).append(val)
                else:
                    setattr(instance, child_tag.prop_name, val)

        return instance

