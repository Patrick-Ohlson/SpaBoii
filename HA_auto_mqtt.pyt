import time
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Button, ButtonInfo,Sensor, SensorInfo,BinarySensor, BinarySensorInfo
from paho.mqtt.client import Client, MQTTMessage

# Mock spa state for testing
spa_state = {
    "connected": True,
    "temperatureF": 100,
    "setpointF": 102,
    "lights": "off",
    "pumps": {
        "1": "off",
        "2": "off",
        "3": "off",
        "4": "off",
        "5": "off",
    },
    "filter_status": 0,
    "filter_duration": 4,
    "filter_frequency": 2.0,
    "filter_suspension": False
}

global state

class SensorInfoExtra(SensorInfo):
    suggested_display_precision: int

# Define the custom action to be performed
def perform_my_custom_action():
    global state
    state = not state
    print("Stop recieved, deleting buttons and sensors")

# To receive button commands from HA, define a callback function:
def my_callback(client: Client, user_data, message: MQTTMessage):
    perform_my_custom_action()
    
# Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host="192.168.68.71",username="mqtt",password="Zx12as78qw!")

# Information about the button
button_info = ButtonInfo(name="SPABoii.CloseService")

settings = Settings(mqtt=mqtt_settings, entity=button_info)



# Define an optional object to be passed back to the callback
user_data = "Some custom data"

# Instantiate the button
my_button = Button(settings, my_callback, user_data)

# Publish the button's discoverability message to let HA automatically notice it
my_button.write_config()

# Information about the sensor
sensor_info = SensorInfoExtra(
    name="SPABoii.CurrentTemp",
    #name="spa_temperature",
    device_class="temperature",
    unit_of_measurement="°C",
    suggested_display_precision=2,
    unique_id="spa_temp_sensor",
)

settings = Settings(mqtt=mqtt_settings, entity=sensor_info)

# Instantiate the sensor
mysensor = Sensor(settings)
mysensor.write_config()

mysensor.set_attributes({"my attribute": "awesome"})



state=True
temp=20
#wait 5 minutes

while state:
    time.sleep(10)
    #increase temperature by 1
    temp+=0.1
    # Change the state of the sensor, publishing an MQTT message that gets picked up by HA
    mysensor.set_state(temp)

my_button.delete()
mysensor.delete()