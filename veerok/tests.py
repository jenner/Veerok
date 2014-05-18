import unittest

from veerok import VeerokParser
from veerok.meta import (
    Tag,
    PropertyTag,
    IntPropertyTag,
    Attribute,
    IntAttribute,
)

def create_tag_def():
    id_attr = Attribute('id')

    return Tag('Main', attributes=(
        id_attr,
        Attribute('foo'),
        Attribute('kabumm'),
    ), child_tags=(
        Tag('Child', prop_name='children', attributes=(
            id_attr,
            Attribute('name'),
        )),
        PropertyTag('Description'),
        IntPropertyTag('Price'),
    ))

class VeerokParserTest(unittest.TestCase):

    def test_parser_nonstrict(self):
        xml = """
        <Main id="12345" foo="bar">
            <Child id="333" name="child1" />
            <Child id="444" name="child2" />
            <Child id="555" name="child3" />
            <Description>Some tag with children and a description. And there's a price too.</Description>
            <Price>4444</Price>
        </Main>
        """
        tag_def = create_tag_def()
        parser = VeerokParser((tag_def,))
        result = parser.parse_xml(xml, strict=False)
        self.assertEqual(len(result.children), 3)
        self.assertEqual(result.price, 4444)
        self.assertEqual(result.id, '12345')
        self.assertEqual(result.foo, 'bar')
        self.assertEqual(result.description, "Some tag with children and a description. And there's a price too.")
        print result.to_xml()

#tags = (create_tag_def(),)
#parser = VeerokParser(tags)
#result = parser.parse_xml(xml)
#print(result.pretty_format())
#print result.to_xml()

