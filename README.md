# Python Homie client

This is a very basic implementation of a client for IoT devices following the
[Homie](https://homieiot.github.io/) MQTT convention. Currently, it only
really supports sensor-like devices, i.e., those devices that publish retained
non-settable properties, as this is at this point in time the only use-case
I personally have for it.

### Usage

Create an instance of the client, and connect it to your MQTT server:

```
from homieclient import HomieClient

c = HomieClient(server='10.42.0.1')
```

Various callbacks can be registered, that will be called when a device, a node
or a property is discovered or updated:

```
# Called when a new device is found. Note that at this point not all the nodes
# of the devices might be discovered yet.
def device_discovered(device):
    print("Found device %s, state is %s" % (device.name, device.state))
c.on_device_discovered = device_discovered

# Called when an attribute on the device changes, such as $state
def device_updated(device, attribute, value):
    print('Device %s updated: %s = %s' % (device.name, attribute, value))
c.on_device_updated = device_updated

# Called when a node on a device is found. The device for this node can be
# accessed via node.device.
def node_discovered(node):
    print('Found node %s on device %s' % (node.name, node.device.name))
    print('Node properties: %s' % node.properties)
c.on_node_discovered = node_discovered

# Called when an attribute on a node changes.
def node_updated(node, attribute, value):
    print('%s, node %s: %s = %s' % (node.device.name, node.name, attribute, value))
c.on_node_updated = node_updated

# Called when a new property on a node is found.
def property_discovered(node, property):
    print('Found property %s on node %s, device %s' % (property, node.name, node.device.name))
c.on_property_discovered = property_discovered

# Called when a property on a node is updated. The value is a dict
# containing the name, value and unit of the property
def property_updated(node, property, value):
    print('%s: %s = %s' % (node.name, property, repr(value)))
c.on_property_updated = property_updated
```

After registering the callbacks you need to connect the client to the broker:
```
c.connect()
```

It is also possible to access all the devices, nodes and properties via the
client, without using any of the callbacks. Every device is exposed as a property
on the client, the nodes are exposed as properties on the device, and the properties
as properties on the node. So if you have a device with id `outdoor_sensor` with
node `sensor` and property `temperature`, you can do
```
temperature = c.outdoor_sensor.sensor.temperature
print('%s: %.1f %s' % (temperature.name, temperature.value, temperature.unit))
```
This will print something like
```
Temperature: 21.4 °C
```
assuming the name of the property is `Temperature`, and it reports a `float` value,
and the weather is quite nice.
