from .node import Node


class Device:
    def __init__(self, homie_client, id):
        self._homie_client = homie_client
        self.id = id
        self.attributes = {}
        self._complete_nodes = {}
        self._incomplete_nodes = {}
        self._initializing = True


    def __getattr__(self, name):
        if name in self._complete_nodes:
            return self._complete_nodes[name]
        elif '$' + name in self.attributes:
            return self.attributes['$' + name]
        else:
            raise AttributeError('No such attribute: ' + name)


    @property
    def nodes(self):
        return list(self._complete_nodes.values())


    def is_ready(self):
        return not self._initializing and (self.state == 'ready' or self.state == 'alert')

    
    def on_message(self, topic, payload):
        if topic == '$nodes':
            nodes = payload.split(',')
            for n in nodes:
                if n not in self._complete_nodes and n not in self._incomplete_nodes:
                    self._incomplete_nodes[n] = {}

        elif topic[0] == '$':
            self.attributes[topic] = payload

            with self._homie_client._callback_mutex:
                if not self._initializing and self._homie_client.on_device_updated:
                    self._homie_client.on_device_updated(self, topic, payload)

        else:
            (node, node_topic) = topic.split('/', 1)

            if node in self._complete_nodes:
                self._complete_nodes[node].on_message(node_topic, payload)

            else:
                self._incomplete_nodes[node][node_topic] = payload
                self.check_incomplete_nodes(node)


    def check_incomplete_nodes(self, node_name):
        data = self._incomplete_nodes[node_name]

        if '$name' in data and '$type' in data and '$properties' in data:
            node = Node(self._homie_client, self, node_name)
            self._complete_nodes[node_name] = node

            for topic in ['$name', '$type', '$properties']:
                node.on_message(topic, data[topic])
                del data[topic]

            node._initializing = False

            for topic, payload in data:
                node.on_message(topic, payload)

            with self._homie_client._callback_mutex:
                if self._homie_client.on_node_discovered:
                    self._homie_client.on_node_discovered(node)

            del self._incomplete_nodes[node_name]