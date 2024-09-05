# Intended to manage the SafeSleep system
# Insert data into the SafeSleep DB

import paho.mqtt.client as mqtt
import time
import random
from init import *
import data_acquisition as da
from icecream import ic
from datetime import datetime


def time_format():
    """Function to format log messages with current time."""
    return f'{datetime.now()}  Manager|> '


ic.configureOutput(prefix=time_format)
ic.configureOutput(includeContext=False)  # Set to True to include script file context


# Define callback functions for MQTT client
def on_log(client, userdata, level, buf):
    """Callback for log messages."""
    ic("log: " + buf)


def on_connect(client, userdata, flags, rc):
    """Callback for successful connection to the broker."""
    if rc == 0:
        ic("connected OK")
    else:
        ic("Bad connection Returned code=", rc)


def on_disconnect(client, userdata, flags, rc=0):
    """Callback for disconnection from the broker."""
    ic("DisConnected result code " + str(rc))


def on_message(client, userdata, msg):
    """Callback for receiving a message."""
    topic = msg.topic
    m_decode = str(msg.payload.decode("utf-8", "ignore"))
    ic("message from: " + topic, m_decode)
    insert_DB(topic, m_decode)


def send_msg(client, topic, message):
    """Function to send a message to a specified topic."""
    ic("Sending message: " + message)
    client.publish(topic, message)


def client_init(cname):
    """Initialize and return an MQTT client instance."""
    r = random.randrange(1, 10000000)
    ID = str(cname + str(r + 21))
    client = mqtt.Client(ID, clean_session=True)  # Create new client instance
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log
    client.on_message = on_message

    if username != "":
        client.username_pw_set(username, password)

    ic("Connecting to broker ", broker_ip)
    client.connect(broker_ip, int(port))  # Connect to broker
    return client


def insert_DB(topic, m_decode):
    """Insert data into the database based on message content."""
    if 'DHT' in m_decode:
        value = parse_data(m_decode)
        if value != 'NA':
            da.add_IOT_data(
                m_decode.split('From: ')[1].split(' Temperature: ')[0],
                da.timestamp(),
                value
            )
    elif 'Meter' in m_decode:
        da.add_IOT_data('ElectricityMeter', da.timestamp(),
                        m_decode.split(' Electricity: ')[1].split(' Sensitivity: ')[0])
        da.add_IOT_data('SensitivityMeter', da.timestamp(), m_decode.split(' Sensitivity: ')[1])


def parse_data(m_decode):
    """Parse temperature data from the message."""
    value = 'NA'
    value = m_decode.split(' Temperature: ')[1].split(' Humidity: ')[0]
    return value


def enable(client, topic, msg):
    """Enable or send a message to a topic."""
    ic(topic + ' ' + msg)
    client.publish(topic, msg)


def alarm(client, topic, msg):
    """Handle alarm messages."""
    ic(topic)
    enable(client, topic, msg)


def actuator(client, topic, msg):
    """Handle actuator messages."""
    enable(client, topic, msg)


def check_DB_for_change(client):
    """Check the database for changes and publish alerts if thresholds are exceeded."""
    df = da.fetch_data(db_name, 'data', 'SensitivityMeter')

    if len(df.value) == 0:
        return

    if float(df.value[-1]) > sensitivityMax:
        msg = 'Current Sensitivity consumption exceed the normal! ' + df.value[-1]
        ic(msg)
        client.publish(comm_topic + 'alarm', msg)

    df = da.fetch_data(db_name, 'data', 'ElectricityMeter')
    if len(df.value) == 0:
        return
    if float(df.value[-1]) > Elec_max:
        msg = 'Current electricity consumption exceed the normal! ' + df.value[-1]
        ic(msg)
        client.publish(comm_topic + 'alarm', msg)


def check_Data(client):
    """Check the data for changes and send commands if necessary."""
    try:
        rrows = da.check_changes('iot_devices')
        for row in rrows:
            topic = row[17]
            if row[10] == 'alarm':
                msg = 'Set temperature to: ' + str(row[15])
                alarm(client, topic, msg)
                da.update_IOT_status(int(row[0]))
            else:
                msg = 'actuated'
                actuator(client, topic, msg)
    except:
        pass


def main():
    """Main function to initialize client and start monitoring loop."""
    cname = "Manager-"
    client = client_init(cname)

    # Start the MQTT client loop and subscribe to topics
    client.loop_start()
    client.subscribe(comm_topic + '#')

    try:
        while conn_time == 0:
            check_DB_for_change(client)
            time.sleep(conn_time + manag_time)
            check_Data(client)
            time.sleep(3)
        ic("con_time ending")
    except KeyboardInterrupt:
        client.disconnect()  # Disconnect from broker
        ic("interrupted by keyboard")

    client.loop_stop()  # Stop the MQTT client loop
    client.disconnect()  # Disconnect from broker
    ic("End manager run script")


if __name__ == "__main__":
    main()
