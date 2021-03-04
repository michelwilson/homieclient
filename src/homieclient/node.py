class Node:
    """Represents a Homie node and contains its properties.

    The properties and attributes on this node can be accessed as
    properties based on their id or name (omitting the initial $).
    The device to which this node belongs is exposed as the device
    property on the class.
    """
    def __init__(self, homie_client, device, id):
        """Create a new node with the given id.

        Arguments:
        homie_client -- the Homie client parent class.
        device -- the Homie device containing this node.
        id -- the id of this node as found on the network
        """
        self._homie_client = homie_client
        self.device = device
        self.id = id
        self.attributes = {}
        self._complete_properties = {}
        self._incomplete_properties = {}
        self._property_values = {}
        self._initializing = True

    def __getattr__(self, name):
        """Get a property or an attribute of this node, based on its id
        or name, omitting the initial $."""
        key = '$' + name
        if name in self._complete_properties:
            return self._get_property(name)
        elif '$' + name in self.attributes:
            return self.attributes['$' + name]
        else:
            raise AttributeError('No such attribute: ' + name)

    @property
    def properties(self):
        """Return a list of all the properties on this node."""
        return list(self._complete_properties.keys())

    def on_message(self, topic, payload):
        """Callback to process MQTT messages and either update the
        relevant property or the attributes of the node."""
        if topic == '$properties':
            properties = payload.split(',')
            for p in properties:
                if p not in self._complete_properties and p not in self._incomplete_properties:
                    self._incomplete_properties[p] = {}

        elif topic[0] == '$':
            self.attributes[topic] = payload

            with self._homie_client._callback_mutex:
                if not self._initializing and self._homie_client.on_node_updated:
                    self._homie_client.on_node_updated(self, topic, payload)

        elif '/' in topic:
            (property, topic) = topic.split('/', 1)

            if property in self._complete_properties:
                self._complete_properties[property][topic] = payload

            else:
                self._incomplete_properties[property][topic] = payload
                self.check_incomplete_properties(property)

        else:
            self._property_values[topic] = payload
            if topic in self._complete_properties:
                self._property_updated(topic)

    def check_incomplete_properties(self, property):
        """Check if the given property is complete.

        After every message, this method is invoked to check if all
        required data is known for a property. If so, the property is
        complete, and it can be added to the list of complete
        properties, and the callback is invoked to inform the user.
        """
        data = self._incomplete_properties[property]

        if '$name' in data and '$datatype' in data:
            self._complete_properties[property] = data
            del self._incomplete_properties[property]

            with self._homie_client._callback_mutex:
                if self._homie_client.on_property_discovered:
                    self._homie_client.on_property_discovered(self, property)

            if property in self._property_values:
                self._property_updated(property)

    def _property_updated(self, property):
        """Called whenever the given property is updated.

        If the device is ready, calls the property update callback. This
        avoids property updates being sent when the device is offline.
        """
        with self._homie_client._callback_mutex:
            if self.device.is_ready() and  \
                    self._homie_client.on_property_updated:
                self._homie_client.on_property_updated(
                    self, property, self._get_property(property))

    def _get_property(self, property):
        """Format the value of the property as a dict.

        Returns a dict containing the name, value and unit of the
        property.  The value is converted based on the datatype for the
        property.
        """
        datatype = self._complete_properties[property]['$datatype']
        unit = self._complete_properties[property].get('$unit')
        name = self._complete_properties[property]['$name']
        raw_value = self._property_values.get(property)

        if raw_value is not None:
            if datatype == 'integer':
                value = int(raw_value)
            elif datatype == 'float':
                value = float(raw_value)
            elif datatype == 'boolean':
                if raw_value == 'true':
                    value = True
                elif raw_value == 'false':
                    value = False
                else:
                    value = None
            else:
                value = raw_value
        else:
            value = None

        return {
            "name": name,
            "value": value,
            "unit": unit
        }
