import paho.mqtt.client as mqtt
import threading

from .device import Device
from .node import Node


class HomieClient:
    def __init__(
        self,
        prefix="homie",
        server="127.0.0.1",
        port=1883
    ):
        self.prefix = prefix
        self.server = server
        self.port = port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self._complete_devices = {}
        self._incomplete_devices = {}
        self._callback_mutex = threading.RLock()
        self._on_device_discovered = None
        self._on_device_updated = None
        self._on_node_discovered = None
        self._on_node_updated = None
        self._on_property_discovered = None
        self._on_property_updated = None


    def __getattr__(self, name):
        if name in self._complete_devices:
            return self._complete_devices[name]
        else:
            raise AttributeError('No such attribute: ' + name)


    @property
    def on_device_discovered(self):
        return self._on_device_discovered

    
    @on_device_discovered.setter
    def on_device_discovered(self, func):
        with self._callback_mutex:
            self._on_device_discovered = func


    @property
    def on_device_updated(self):
        return self._on_device_updated

    
    @on_device_updated.setter
    def on_device_updated(self, func):
        with self._callback_mutex:
            self._on_device_updated = func


    @property
    def on_node_discovered(self):
        return self._on_node_discovered


    @on_node_discovered.setter
    def on_node_discovered(self, func):
        with self._callback_mutex:
            self._on_node_discovered = func


    @property
    def on_node_updated(self):
        return self._on_node_updated


    @on_node_updated.setter
    def on_node_updated(self, func):
        with self._callback_mutex:
            self._on_node_updated = func


    @property
    def on_property_discovered(self):
        return self._on_property_discovered


    @on_property_discovered.setter
    def on_property_discovered(self, func):
        with self._callback_mutex:
            self._on_property_discovered = func


    @property
    def on_property_updated(self):
        return self._on_property_updated


    @on_property_updated.setter
    def on_property_updated(self, func):
        with self._callback_mutex:
            self._on_property_updated = func

    
    @property
    def devices(self):
        return list(self._complete_devices.values())


    def connect(self):
        self.client.connect_async(self.server, self.port)
        self.client.loop_start()


    def disconnect(self):
        self.client.disconnect()


    def on_connect(self, client, userdata, flags, rc):
        client.subscribe('homie/#')


    def on_message(self, client, userdata, msg):
        (_, device, device_topic) = msg.topic.split('/', 2)
        payload = msg.payload.decode('utf-8')

        if device in self._complete_devices:
            self._complete_devices[device].on_message(device_topic, payload)
        else:
            if device not in self._incomplete_devices:
                self._incomplete_devices[device] = {}
            self._incomplete_devices[device][device_topic] = payload
            self.check_incomplete_device(device)


    def check_incomplete_device(self, device_name):
        device_data = self._incomplete_devices[device_name]

        if '$homie' in device_data and '$name' in device_data and \
                '$state' in device_data and '$nodes' in device_data:
            device = Device(self, device_name)
            self._complete_devices[device_name] = device

            for topic in ['$name', '$homie', '$state', '$nodes']:
                device.on_message(topic, device_data[topic])
                del device_data[topic]

            for topic, payload in device_data.items():
                self._complete_devices[device_name].on_message(topic, payload)

            del self._incomplete_devices[device_name]

            device._initializing = False

            with self._callback_mutex:
                if self.on_device_discovered:
                    self.on_device_discovered(device)

            