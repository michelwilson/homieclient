class Node:
    def __init__(self, homie_client, device, id):
        self._homie_client = homie_client
        self.device = device
        self.id = id
        self.attributes = {}
        self._complete_properties = {}
        self._incomplete_properties = {}
        self._property_values = {}
        self._initializing = True


    def __getattr__(self, name):
        key = '$' + name
        if name in self._complete_properties:
            return self._get_property(name)
        elif '$' + name in self.attributes:
            return self.attributes['$' + name]
        else:
            raise AttributeError('No such attribute: ' + name)


    @property
    def properties(self):
        return list(self._complete_properties.keys())


    def on_message(self, topic, payload):
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
        with self._homie_client._callback_mutex:
            if self.device.is_ready() and self._homie_client.on_property_updated:
                try:
                    self._homie_client.on_property_updated(self, property, self._get_property(property))
                except Exception as e:
                    print(e)
                    pass


    def _get_property(self, property):
        datatype = self._complete_properties[property]['$datatype']
        unit = self._complete_properties[property].get('$unit')
        name = self._complete_properties[property]['$name']
        raw_value = self._property_values[property]
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

        return {
            "name": name,
            "value": value, 
            "unit": unit
        }
