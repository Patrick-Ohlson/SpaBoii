import time
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Button, ButtonInfo
from paho.mqtt.client import Client, MQTTMessage

# Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host="192.168.68.71",username="mqtt",password="Zx12as78qw!")

# Information about the button
button_info = ButtonInfo(name="SPABoii.test")

settings = Settings(mqtt=mqtt_settings, entity=button_info)

# Define the custom action to be performed
def perform_my_custom_action():
    print("Button pressed!")

# To receive button commands from HA, define a callback function:
def my_callback(client: Client, user_data, message: MQTTMessage):
    perform_my_custom_action()

# Define an optional object to be passed back to the callback
user_data = "Some custom data"

# Instantiate the button
my_button = Button(settings, my_callback, user_data)

# Publish the button's discoverability message to let HA automatically notice it
my_button.write_config()

#wait 5 minutes
time.sleep(2*60)

my_button.delete()
