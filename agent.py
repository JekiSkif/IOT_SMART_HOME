import paho.mqtt.client as mqtt
from init import *
from icecream import ic
from datetime import datetime

# Configure logging format
ic.configureOutput(prefix=lambda: f'{datetime.now()}  Agent|> ', includeContext=False)

class MqttClient:
    def __init__(self):
        # Initialize connection parameters
        self.broker = ''
        self.topic = ''
        self.port = ''
        self.clientname = ''
        self.username = ''
        self.password = ''
        self.subscribeTopic = ''
        self.publishTopic = ''
        self.publishMessage = ''
        self.on_connected_to_form = ''
        self.connected = False
        self.subscribed = False

    # Setters and getters
    def set_on_connected_to_form(self, func): self.on_connected_to_form = func
    def set_broker(self, value): self.broker = value
    def set_port(self, value): self.port = value
    def set_clientname(self, value): self.clientname = value
    def set_username(self, value): self.username = value
    def set_password(self, value): self.password = value
    def set_subscribeTopic(self, value): self.subscribeTopic = value
    def set_publishTopic(self, value): self.publishTopic = value
    def set_publishMessage(self, value): self.publishMessage = value

    def get_broker(self): return self.broker
    def get_port(self): return self.port
    def get_clientname(self): return self.clientname
    def get_username(self): return self.username
    def get_password(self): return self.password
    def get_subscribeTopic(self): return self.subscribeTopic
    def get_publishTopic(self): return self.publishTopic
    def get_publishMessage(self): return self.publishMessage

    # MQTT client callbacks
    def on_log(self, client, userdata, level, buf): ic(f"log: {buf}")
    def on_connect(self, client, userdata, flags, rc):
        self.connected = rc == 0
        if self.connected:
            ic("Connected OK")
            self.on_connected_to_form()
        else:
            ic(f"Bad connection. Returned code={rc}")

    def on_disconnect(self, client, userdata, flags, rc=0):
        self.connected = False
        ic(f"Disconnected. Result code {rc}")

    def on_message(self, client, userdata, msg):
        ic(f"Message from {msg.topic}: {msg.payload.decode('utf-8', 'ignore')}")

    # MQTT client operations
    def connect_to(self):
        self.client = mqtt.Client(self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)
        ic(f"Connecting to broker {self.broker}")
        self.client.connect(self.broker, self.port)

    def disconnect_from(self): self.client.disconnect()
    def start_listening(self): self.client.loop_start()
    def stop_listening(self): self.client.loop_stop()

    def subscribe_to(self, topic):
        if self.connected:
            self.client.subscribe(topic)
            self.subscribed = True
        else:
            ic("Cannot subscribe. Connection must be established first.")

    def publish_to(self, topic, message):
        if self.connected:
            self.client.publish(topic, message)
        else:
            ic("Cannot publish. Connection must be established first.")
