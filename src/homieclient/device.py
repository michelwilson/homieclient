from .node import Node


class Device:
    """Represents a Homie device and contains its nodes.

    The nodes and attributes on this device can be accessed as
    properties based on their id or name (omitting the initial $).
    """
    def __init__(self, homie_client, id):
        """Create a new device with the given id.

        Arguments:
        homie_client -- the Homie client parent class
        id -- the id of this device as found on the network
        """
        self._homie_client = homie_client
        self.id = id
        self.attributes = {}
        self._complete_nodes = {}
        self._incomplete_nodes = {}

    def __getattr__(self, name):
        """Get a node or an attribute of this device, based on its id or
        name, omitting the initial $."""
        if name in self._complete_nodes:
            return self._complete_nodes[name]
        elif '$' + name in self.attributes:
            return self.attributes['$' + name]
        else:
            raise AttributeError('No such attribute: ' + name)

    @property
    def nodes(self):
        """Return a list of all the nodes in this device."""
        return list(self._complete_nodes.values())

    def is_ready(self):
        """True if all nodes have been discovered and the device is
        either ready or in alert (i.e., not sleeping or lost)."""
        return not len(self._incomplete_nodes) and (self.state == 'ready' or self.state == 'alert')

    def on_message(self, topic, payload):
        """Callback to process MQTT messages and either update the
        relevant node or the attributes of the device."""
        if topic == '$nodes':
            if len(payload.strip()):
                nodes = payload.split(',')
                for n in nodes:
                    if n not in self._complete_nodes and n not in self._incomplete_nodes:
                        self._incomplete_nodes[n] = {}
            else:
                self._incomplete_nodes = {}

        elif topic[0] == '$':
            self.attributes[topic] = payload

            with self._homie_client._callback_mutex:
                if not len(self._incomplete_nodes) and self._homie_client.on_device_updated:
                    self._homie_client.on_device_updated(self, topic, payload)

        else:
            (node, node_topic) = topic.split('/', 1)

            if node in self._complete_nodes:
                self._complete_nodes[node].on_message(node_topic, payload)

            else:
                self._incomplete_nodes[node][node_topic] = payload
                self.check_incomplete_nodes(node)

    def check_incomplete_nodes(self, node_name):
        """Check if the given node is complete.

        After every message, this method is invoked to check if all
        required data is known for a node. If so, the node is complete,
        and it can be added to the list of complete nodes, and the
        callback is invoked to inform the user.
        """
        data = self._incomplete_nodes[node_name]

        if '$name' in data and '$type' in data and '$properties' in data:
            node = Node(self._homie_client, self, node_name)
            self._complete_nodes[node_name] = node

            for topic in ['$name', '$type', '$properties']:
                node.on_message(topic, data[topic])
                del data[topic]

            node._initializing = False

            for topic, payload in data.items():
                node.on_message(topic, payload)

            with self._homie_client._callback_mutex:
                if self._homie_client.on_node_discovered:
                    self._homie_client.on_node_discovered(node)

            del self._incomplete_nodes[node_name]
