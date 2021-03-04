from unittest.mock import Mock, patch
import pytest

from homieclient import HomieClient
from paho.mqtt.client import MQTTMessage


def test_basic_device():
    c = get_client_with_messages({
        'homie/testdevice/$homie': '3.0.1',
        'homie/testdevice/$name': 'Test device',
        'homie/testdevice/$state': 'ready',
        'homie/testdevice/$nodes': ''
    })
    assert c.testdevice.state == 'ready'
    assert len(c.devices) == 1
    assert c.devices[0] == c.testdevice


def test_incomplete_device():
    c = get_client_with_messages({
        'homie/testdevice/$homie': '3.0.1',
        'homie/testdevice/$name': 'Test device'
    })
    with pytest.raises(AttributeError):
        c.testdevice


def test_out_of_order():
    c = get_client_with_messages({
        'homie/testdevice/testnode/$attr': 'value',
        'homie/testdevice/$homie': '3.0.1',
        'homie/testdevice/$name': 'Test device',
        'homie/testdevice/$state': 'ready',
        'homie/testdevice/$nodes': 'testnode'
    })
    assert c.testdevice.state == 'ready'
    assert c.testdevice._incomplete_nodes['testnode']['$attr'] == 'value'


def test_subscribe_default_prefix():
    c = HomieClient()
    mqtt_client = Mock()
    c.on_connect(mqtt_client, None, None, None)
    mqtt_client.subscribe.assert_called_with('homie/#')


def test_subscribe_custom_prefix():
    c = HomieClient(prefix='unittest')
    mqtt_client = Mock()
    c.on_connect(mqtt_client, None, None, None)
    mqtt_client.subscribe.assert_called_with('unittest/#')


@patch('homieclient.mqtt.Client')
def test_connect_custom_params(mock_client_constructor):
    mock_client = Mock()
    mock_client_constructor.side_effect = [mock_client]
    c = HomieClient(server='unit-test-server', port=1337)
    c.connect()

    mock_client.connect_async.assert_called_with('unit-test-server', 1337)


def get_client_with_messages(msgs: dict) -> HomieClient:
    c = HomieClient()

    for topic, payload in msgs.items():
        msg = MQTTMessage()
        msg.topic = topic.encode('utf-8')
        msg.payload = payload.encode('utf-8')
        c.on_message(None, None, msg)

    return c
