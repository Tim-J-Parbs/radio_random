import time
import pexpect
import numpy as np
from passwd_data import *
from bt_data import *
import paho.mqtt.client as mqtt
import sys
import bluetooth
import subprocess

def get_device_name(mac_address):
    name = bluetooth.lookup_name(mac_address, timeout=10)  # Timeout in seconds
    if name:
        print(f"Device {mac_address} is named: {name}")
        return name
    else:
        print(f"Could not retrieve name for device {mac_address}")
        return ''
def connect_to_speaker(address):
    response=''
    print('READY')
    p = pexpect.spawn('bluetoothctl', encoding='utf-8')
    print('SPAWNED')
    p.logfile_read = sys.stdout
    p.expect('#')
    print('GOT IT')
    p.sendline("select "+PREFERRED_INTERFACE[1])
    print(f"SELECTED {PREFERRED_INTERFACE[1]}")
    p.expect("#")
    p.sendline("scan on")
    print('SCANNING')
    mylist = ["Discovery started","Failed to start discovery","Device "+address+" not available","Failed to connect","Connection successful"]
    c = 0
    response = True
    while response != "Connection successful":
        p.expect(mylist)
        response=p.after
        p.sendline("connect "+address)
        time.sleep(1)
        c += 1
        if c > 10:
            print('Device unavailable')
            response = False
            break
    p.sendline("quit")
    p.close()
    #time.sleep(1)
    return response
def disconnect_from_speaker(address):
    response=''
    print('READY')
    p = pexpect.spawn('bluetoothctl', encoding='utf-8')
    print('SPAWNED')
    p.logfile_read = sys.stdout
    p.expect('#')
    print('GOT IT')
    p.sendline("select "+PREFERRED_INTERFACE[1])
    print(f"SELECTED {PREFERRED_INTERFACE[1]}")
    p.expect("#")
    p.sendline("disconnect " + address)
    p.sendline("quit")
    p.close()
    #time.sleep(1)
    return response

def disconnect_speaker(mac_address):
    print(f"Disconnecting from speaker at {mac_address}...")

    # Using `bluetoothctl` to connect to the speaker
    try:
        # Connect to the device
        subprocess.run(["bluetoothctl", "disconnect", mac_address])

        print("Disconnection successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error disconnecting from speaker: {e}")
        return False

def get_connected_devices():
    try:
        # Get a list of all devices using bluetoothctl
        result = subprocess.run(["bluetoothctl", "paired-devices"], capture_output=True, text=True)
        devices = result.stdout.splitlines()

        connected_devices = []

        # Iterate over each device
        for device in devices:
            parts = device.split(" ")
            if len(parts) >= 2:
                mac_address = parts[1]
                device_name = " ".join(parts[2:])

                # Check if the device is connected
                info_result = subprocess.run(["bluetoothctl", "info", mac_address], capture_output=True, text=True)
                if "Connected: yes" in info_result.stdout:
                    connected_devices.append((mac_address, device_name))
        return connected_devices


    except subprocess.CalledProcessError as e:
        print(f"Error retrieving connected devices: {e}")
        return None


class bluetooth_connector():
    def __init__(self):
        # MQTT Settings
        self.MQTT_BROKER = MQTT_IP
        self.MQTT_PORT = MQTT_PORT
        self.MQTT_REQUEST_TOPIC = "home-assistant/bluetooth/bt_request"
        self.MQTT_DEVICE_TOPIC = "home-assistant/bluetooth/bt_device"
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_message = self.on_message
        # Connect to the MQTT broker
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        self.client.subscribe(self.MQTT_REQUEST_TOPIC)
        self.debug = True
        self.client.loop_start()

        try:
            # Periodically check and publish the status of pins 23 and 24
            while True:
                self.check_connection()
                time.sleep(10)
        except:
            print('Oh no :(')
    def check_connection(self):
        devices = get_connected_devices()
        if devices:
            dev_names = ','.join([d[1] for d in devices])
            self.client.publish(self.MQTT_DEVICE_TOPIC, dev_names)

    def on_message(self, client, userdata, message):
            # Decode the incoming message
            payload = message.payload.decode("utf-8").split(',')
            command = payload[0]
            bt_device = payload[1]
            try:
                MAC = [d[1] for d in BT_DEVICES if d[0] == bt_device]
                if len(MAC) == 0:
                    print(f"Device {bt_device} not in known devices.")
                    return
                MAC = MAC[0]
                if command == 'connect':
                    connection_succesful = connect_to_speaker(MAC)
                    print('OKE')
                    self.check_connection()

                elif command == 'disconnect':
                    disconnect_speaker(MAC)

            except Exception as A:
                print(A)
                print(f"Something gone wrong.")

if __name__ == "__main__":
    bluetooth_connector()