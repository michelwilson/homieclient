import pytest
from unittest.mock import Mock, MagicMock

from homieclient.node import Node


def test_properties_exist():
    n = get_node_with_properties('test-node', {
        'prop1': {'name': 'Property 1', 'datatype': 'string'},
        'prop2': {'name': 'Property 2', 'datatype': 'float', 'unit': 'V'},
    })
    assert n.properties == ['prop1', 'prop2']
    assert hasattr(n, 'prop1')
    assert hasattr(n, 'prop2')


@pytest.mark.parametrize(
    "datatype,value,expected",
    [
        ('integer', '1337', 1337),
        ('float', '12.34', 12.34),
        ('float', '-.1', -0.1),
        ('boolean', 'true', True),
        ('boolean', 'false', False),
        ('boolean', 'invalid', None),
        ('string', 'something something', 'something something')
    ]
)
def test_value_conversion(datatype, value, expected):
    n = get_node_with_properties('test-node', {
        'prop1': {'name': 'Property 1', 'datatype': datatype}
    })
    n.on_message('prop1', value)
    assert n.prop1['value'] == expected


def test_callback_on_update():
    n = get_node_with_properties('test-node', {
        'prop1': {'name': 'Property 1', 'datatype': 'integer'}
    })

    n.on_message('prop1', 1234)

    n._homie_client.on_property_updated.assert_called_with(n, 'prop1', {
        'name': 'Property 1',
        'unit': None,
        'value': 1234
    })


def test_no_callback_when_not_ready():
    n = get_node_with_properties('test-node', {
        'prop1': {'name': 'Property 1', 'datatype': 'integer'}
    })
    n.device.is_ready.return_value = False

    n.on_message('prop1', 1234)

    n._homie_client.on_property_updated.assert_not_called()


def test_attribute():
    n = get_node_with_properties('test-node', {})

    n.on_message('$attribute', 'some-value')

    assert n.attribute == 'some-value'


def test_incomplete_property():
    n = get_node_with_properties('test-node', {
        'prop1': {}
    })

    assert len(n.properties) == 0


def test_callback_on_out_of_order_init():
    n = get_node_with_properties('test-node', {
        'prop1': {}
    })

    n.on_message('prop1', '123')
    n.on_message('prop1/$name', 'Property 1')
    n.on_message('prop1/$datatype', 'integer')

    n._homie_client.on_property_updated.assert_called_with(n, 'prop1', {
        'name': 'Property 1',
        'value': 123,
        'unit': None
    })



def get_node_with_properties(id: str, properties: dict) -> Node:
    homie_client = MagicMock()
    device = Mock()
    n = Node(homie_client, device, id)
    n.on_message('$properties', ','.join(properties.keys()))
    for (propname, info) in properties.items():
        if 'name' in info:
            n.on_message(f'{propname}/$name', info['name'])
        if 'datatype' in info:
            n.on_message(f'{propname}/$datatype', info['datatype'])
        if 'unit' in info:
            n.on_message(f'{propname}/$unit', info['unit'])
    return n
