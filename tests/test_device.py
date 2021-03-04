import pytest
from unittest.mock import MagicMock

from homieclient import Device


def test_ready_no_nodes():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': '',
        '$state': 'ready'
    })
    assert d.is_ready()


def test_nodelist_no_nodes():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': '',
        '$state': 'ready'
    })
    assert len(d.nodes) == 0


def test_basic_attributes():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': '',
        '$state': 'ready'
    })
    assert d.name == 'Test Device'
    assert d.state == 'ready'


def test_not_ready_when_lost():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': '',
        '$state': 'lost'
    })
    assert not d.is_ready()


def test_not_ready_when_nodes_unknown():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': 'sensor',
        '$state': 'ready'
    })
    assert not d.is_ready()


def test_node_init():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': 'sensor',
        '$state': 'ready',
        'sensor/$name': 'Sensor',
        'sensor/$type': 'unit-test-sensor',
        'sensor/$properties': ''
    })
    assert d.is_ready()
    assert len(d.nodes) == 1
    assert d.sensor is not None
    assert d.sensor.name == 'Sensor'
    assert d.sensor._initializing == False


def test_partial_node():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': 'sensor',
        '$state': 'ready',
        'sensor/$name': 'Sensor',
        'sensor/$type': 'unit-test-sensor'
    })
    assert not d.is_ready()
    assert len(d.nodes) == 0
    with pytest.raises(AttributeError):
        d.sensor


def test_node_init_out_of_order():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': 'sensor',
        '$state': 'ready',
        'sensor/$name': 'Sensor',
        'sensor/$someattr': 'this is extra',
        'sensor/$type': 'unit-test-sensor',
        'sensor/$properties': ''
    })
    assert d.is_ready()
    assert len(d.nodes) == 1
    assert d.sensor is not None
    assert d.sensor.name == 'Sensor'
    assert d.sensor._initializing == False
    assert d.sensor.someattr == 'this is extra'


def test_send_msg_to_complete_node():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': 'sensor',
        '$state': 'ready',
        'sensor/$name': 'Sensor',
        'sensor/$type': 'unit-test-sensor',
        'sensor/$properties': ''
    })

    with pytest.raises(AttributeError):
        d.sensor.someattr
    
    d.on_message('sensor/$someattr', 'new-value')

    assert d.sensor.someattr == 'new-value'


def test_node_discovery_callback():
    d = get_device_after_msgs('test-device', {
        '$name': 'Test Device',
        '$nodes': 'sensor',
        '$state': 'ready',
        'sensor/$name': 'Sensor',
        'sensor/$type': 'unit-test-sensor',
        'sensor/$properties': ''
    })

    d._homie_client.on_node_discovered.assert_called_with(d.sensor)


def get_device_after_msgs(id: str, msgs: dict) -> Device:
    d = Device(MagicMock(), id)
    for topic, msg in msgs.items():
        d.on_message(topic, msg)
    return d