from unittest.mock import call, Mock

from homieclient import HomieClient
from paho.mqtt.client import MQTTMessage

def test_integration():
    device_discovered = Mock()
    node_discovered = Mock()
    property_discovered = Mock()
    device_updated = Mock()
    node_updated = Mock()
    property_updated = Mock()

    c = HomieClient()

    c.on_device_discovered = device_discovered
    c.on_node_discovered = node_discovered
    c.on_property_discovered = property_discovered

    c.on_device_updated = device_updated
    c.on_node_updated = node_updated
    c.on_property_updated = property_updated

    with open('tests/messages.txt') as f:
        for line in f.readlines():
            topic, payload = line.split(' ', 1)
            msg = MQTTMessage()
            msg.topic = topic.encode('utf-8')
            msg.payload = payload.strip().encode('utf-8')
            c.on_message(None, None, msg)

    assert c.sensor1.state == 'ready'
    assert len(c.sensor1.nodes) == 2
    assert len(c.sensor1.dht.properties) == 2
    assert len(c.sensor1.bmp.properties) == 1
    assert c.sensor1.dht.temperature == {'name': 'Temperature', 'unit': '°C', 'value': 19.82}
    assert c.sensor1.dht.humidity == {'name': 'Humidity', 'unit': '%', 'value': 61.9}
    assert c.sensor1.bmp.pressure == {'name': 'Pressure', 'unit': 'mbar', 'value': 1021.69}
    assert c.powermeter.state == 'ready'
    assert len(c.powermeter.nodes) == 1
    assert len(c.powermeter.powermeter.properties) == 2
    assert c.powermeter.powermeter.power_delivered == {'name': 'Power delivered', 'unit': 'W', 'value': 410}
    assert c.powermeter.powermeter.power_returned == {'name': 'Power returned', 'unit': 'W', 'value': 1500}

    device_discovered.assert_has_calls([call(c.powermeter), call(c.sensor1)], any_order=True)
    node_discovered.assert_has_calls([call(node) for node in [c.powermeter.powermeter, c.sensor1.bmp, c.sensor1.dht]], any_order=True)
    property_discovered.assert_has_calls([call(e[0], e[1]) for e in [
        (c.sensor1.dht, 'temperature'),
        (c.sensor1.dht, 'humidity'),
        (c.sensor1.bmp, 'pressure'),
        (c.powermeter.powermeter, 'power_delivered'),
        (c.powermeter.powermeter, 'power_returned')
    ]], any_order=True)

    property_updated.assert_has_calls([call(e[0], e[1], e[2]) for e in [
        (c.sensor1.dht, 'temperature', {'name': 'Temperature', 'unit': '°C', 'value': 20.12}),
        (c.sensor1.dht, 'temperature', {'name': 'Temperature', 'unit': '°C', 'value': 20.08}),
        (c.sensor1.dht, 'temperature', {'name': 'Temperature', 'unit': '°C', 'value': 19.82}),
        (c.sensor1.dht, 'humidity', {'name': 'Humidity', 'unit': '%', 'value': 63.5}),
        (c.sensor1.dht, 'humidity', {'name': 'Humidity', 'unit': '%', 'value': 63.2}),
        (c.sensor1.dht, 'humidity', {'name': 'Humidity', 'unit': '%', 'value': 61.9}),
        (c.sensor1.bmp, 'pressure', {'name': 'Pressure', 'unit': 'mbar', 'value': 1021.7}),
        (c.sensor1.bmp, 'pressure', {'name': 'Pressure', 'unit': 'mbar', 'value': 1021.71}),
        (c.sensor1.bmp, 'pressure', {'name': 'Pressure', 'unit': 'mbar', 'value': 1021.69}),
        (c.powermeter.powermeter, 'power_delivered', {'name': 'Power delivered', 'unit': 'W', 'value': 356}),
        (c.powermeter.powermeter, 'power_delivered', {'name': 'Power delivered', 'unit': 'W', 'value': 390}),
        (c.powermeter.powermeter, 'power_delivered', {'name': 'Power delivered', 'unit': 'W', 'value': 410}),
        (c.powermeter.powermeter, 'power_returned', {'name': 'Power returned', 'unit': 'W', 'value': 1300}),
        (c.powermeter.powermeter, 'power_returned', {'name': 'Power returned', 'unit': 'W', 'value': 1400}),
        (c.powermeter.powermeter, 'power_returned', {'name': 'Power returned', 'unit': 'W', 'value': 1500})
    ]], any_order=True)