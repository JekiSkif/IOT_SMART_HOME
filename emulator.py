# Emulator for Home IoT Devices (DHT, Electric meter, Sensitivity meter, etc.)
import sys
import random
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from init import *
from agent import Mqtt_client
from icecream import ic
from datetime import datetime
import logging

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logfile_emulator.log')
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Configure icecream debugging
def time_format():
    return f'{datetime.now()}  Emulator|> '


ic.configureOutput(prefix=time_format, includeContext=False)

# Generate unique client name
global clientname, tmp_upd
clientname = f"IOT_clYT-Id-{random.randrange(1, 10000000)}"


class MC(Mqtt_client):
    """MQTT Client with message handling for emulator."""

    def __init__(self):
        super().__init__()

    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        topic = msg.topic
        m_decode = str(msg.payload.decode("utf-8", "ignore"))
        ic("message from:" + topic, m_decode)
        try:
            mainwin.connectionDock.update_btn_state(m_decode)
        except:
            ic("Failed to update button state.")


class ConnectionDock(QDockWidget):
    """Dock widget for connection and device control."""

    def __init__(self, mc, name, topic_sub, topic_pub):
        super().__init__()
        self.name = name
        self.topic_sub = topic_sub
        self.topic_pub = topic_pub
        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)

        # UI Elements Setup
        self.setup_ui()

    def setup_ui(self):
        """Setup UI elements for the connection dock."""
        self.eHostInput = QLineEdit()
        self.eHostInput.setInputMask('999.999.999.999')
        self.eHostInput.setText(broker_ip)

        self.ePort = QLineEdit()
        self.ePort.setValidator(QIntValidator())
        self.ePort.setMaxLength(4)
        self.ePort.setText(broker_port)

        self.eClientID = QLineEdit()
        self.eClientID.setText(clientname)

        self.eUserName = QLineEdit()
        self.eUserName.setText(username)

        self.ePassword = QLineEdit()
        self.ePassword.setEchoMode(QLineEdit.Password)
        self.ePassword.setText(password)

        self.eKeepAlive = QLineEdit()
        self.eKeepAlive.setValidator(QIntValidator())
        self.eKeepAlive.setText("60")

        self.eSSL = QCheckBox()
        self.eCleanSession = QCheckBox()
        self.eCleanSession.setChecked(True)

        self.eConnectbtn = QPushButton("Enable/Connect", self)
        self.eConnectbtn.setToolTip("Click to connect")
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet("background-color: gray")

        # Layout setup based on device type
        formLayout = QFormLayout()
        self.setup_device_specific_ui(formLayout)
        widget = QWidget(self)
        widget.setLayout(formLayout)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle("IOT Emulator")

    def setup_device_specific_ui(self, formLayout):
        """Setup UI elements based on the type of IoT device."""
        if 'DHT' in self.name:
            self.ePublisherTopic = QLineEdit()
            self.ePublisherTopic.setText(self.topic_pub)
            self.Temperature = QLineEdit()
            self.Humidity = QLineEdit()
            formLayout.addRow("Turn On/Off", self.eConnectbtn)
            formLayout.addRow("Pub topic", self.ePublisherTopic)
            formLayout.addRow("Temperature", self.Temperature)
            formLayout.addRow("Humidity", self.Humidity)
        elif 'Motion' in self.name:
            self.eSubscribeTopic = QLineEdit()
            self.eSubscribeTopic.setText(self.topic_sub)
            self.ePushtbtn = QPushButton("", self)
            self.ePushtbtn.setToolTip("Push me")
            self.ePushtbtn.setStyleSheet("background-color: gray")
            self.Temperature = QLineEdit()
            formLayout.addRow("Turn On/Off", self.eConnectbtn)
            formLayout.addRow("Sub topic", self.eSubscribeTopic)
            formLayout.addRow("Status", self.ePushtbtn)
            formLayout.addRow("Distance", self.Temperature)
        elif 'Elec' in self.name:
            self.ePublisherTopic = QLineEdit()
            self.ePublisherTopic.setText(self.topic_pub)
            self.Temperature = QLineEdit()
            self.Humidity = QLineEdit()
            formLayout.addRow("Turn On/Off", self.eConnectbtn)
            formLayout.addRow("Pub topic", self.ePublisherTopic)
            formLayout.addRow("Electricity", self.Temperature)
            formLayout.addRow("Sensitivity", self.Humidity)
        else:
            self.eSubscribeTopic = QLineEdit()
            self.eSubscribeTopic.setText(self.topic_sub)
            self.ePushtbtn = QPushButton("", self)
            self.ePushtbtn.setToolTip("Push me")
            self.ePushtbtn.setStyleSheet("background-color: gray")
            self.Temperature = QLineEdit()
            formLayout.addRow("Turn On/Off", self.eConnectbtn)
            formLayout.addRow("Sub topic", self.eSubscribeTopic)
            formLayout.addRow("Status", self.ePushtbtn)

    def on_connected(self):
        """Change button color on connection."""
        self.eConnectbtn.setStyleSheet("background-color: green")

    def on_button_connect_click(self):
        """Handle connect button click event."""
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.set_username(self.eUserName.text())
        self.mc.set_password(self.ePassword.text())
        self.mc.connect_to()
        self.mc.start_listening()

    def push_button_click(self):
        """Handle push button click for publishing."""
        self.mc.publish_to(self.ePublisherTopic.text(), '"value":1')

    def update_btn_state(self, messg):
        """Update button state based on the received message."""
        global tmp_upd
        if 'Set' in messg:
            tmp = '12'
            self.ePushtbtn.setStyleSheet("background-color: green")
            try:
                tmp = messg.split('Set temperature to: ')[1]
                self.Temperature.setText(tmp)
            except:
                ic("Failed to parse temperature.")
            tmp_upd = tmp


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, args, parent=None):
        super().__init__(parent)
        self.init_args(args)
        self.setup_main_window()
        self.setup_connection_dock()

    def init_args(self, args):
        """Initialize arguments and set instance variables."""
        global tmp_upd
        self.name = args[1]
        self.units = args[2]
        self.topic_sub = comm_topic + args[3] + '/sub'
        self.topic_pub = comm_topic + args[3] + '/pub'
        self.update_rate = args[4]
        self.mc = MC()

        # Set initial values and timers based on device type
        self.setup_timers()

    def setup_timers(self):
        """Setup timers based on device type."""
        if 'DHT' in self.name:
            tmp_upd = 22
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.create_data)
            self.timer.start(int(self.update_rate) * 1000)
        elif 'Meter' in self.name:
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.create_data_EW)
            self.timer.start(int(self.update_rate) * 1000)
        elif 'Alarm' in self.name:
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.create_data_Air)
            self.timer.start(int(self.update_rate) * 1000)
        elif 'Motion' in self.name:
            tmp_upd = 80
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.create_data_Bo)
            self.timer.start(int(self.update_rate) * 1000)

    def setup_main_window(self):
        """Setup main window properties."""
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(30, 600, 300, 150)
        self.setWindowTitle(self.name)

    def setup_connection_dock(self):
        """Setup connection dock within the main window."""
        self.connectionDock = ConnectionDock(self.mc, self.name, self.topic_sub, self.topic_pub)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)

    def create_data(self):
        """Create and publish DHT data."""
        global tmp_upd
        ic('Next update')
        temp = tmp_upd + random.randrange(1, 10)
        hum = 74 + random.randrange(1, 25)
        current_data = f'From: {self.name} Temperature: {temp} Humidity: {hum}'
        self.connectionDock.Temperature.setText(str(temp))
        self.connectionDock.Humidity.setText(str(hum))
        self.ensure_connected()
        self.mc.publish_to(self.topic_pub, current_data)

    def create_data_EW(self):
        """Create and publish electricity and sensitivity data."""
        ic('Electricity-Sensitivity data update')
        hour_delta_w = 0.42 / 24
        hour_delta_el = (670 / 17) / 24
        elec = format(hour_delta_el + random.randrange(-100, 100) / 300, '.2f')
        Sensitivity = format(hour_delta_w + random.randrange(-10, 10) / 1000, '.3f')
        current_data = f'From: {self.name} Electricity: {elec} Sensitivity: {Sensitivity}'
        self.connectionDock.Temperature.setText(str(elec))
        self.connectionDock.Humidity.setText(str(Sensitivity))
        self.ensure_connected()
        self.mc.publish_to(self.topic_pub, current_data)

    def create_data_Air(self):
        """Handle alarm data updates."""
        ic('Alarm data update')
        self.ensure_connected(subscribe=True)

    def create_data_Bo(self):
        """Create and publish motion data."""
        global tmp_upd
        ic('Motion data update')
        self.ensure_connected(subscribe=True)
        temp = tmp_upd + random.randrange(1, 20) / 2
        current_data = f'Temperature: {temp}'
        self.connectionDock.Temperature.setText(str(temp))
        self.mc.publish_to(self.topic_pub, current_data)

    def ensure_connected(self, subscribe=False):
        """Ensure MQTT client is connected and optionally subscribed."""
        if not self.mc.connected:
            self.connectionDock.on_button_connect_click()
        if subscribe and not self.mc.subscribed:
            self.mc.subscribe_to(self.topic_sub)


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        argv = sys.argv
        if len(argv) == 1:
            argv.extend(['Alarm', 'Celsius', 'air-1', '7'])
        mainwin = MainWindow(argv)
        mainwin.show()
        app.exec_()
    except:
        logger.exception("Crash!")
