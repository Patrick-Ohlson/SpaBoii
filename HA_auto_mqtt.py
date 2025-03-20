import time
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import (
    Button,
    ButtonInfo,
    Sensor,
    SensorInfo,
    BinarySensor,
    BinarySensorInfo,
    Number,
    NumberInfo,
    Select,
    SelectInfo
)
from paho.mqtt.client import Client, MQTTMessage
import yaml


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

global state, producer

class SensorInfoExtra(SensorInfo):
    suggested_display_precision: int
class NumberInfoExtra(NumberInfo):
    suggested_display_precision: int

# Define the custom action to be performed
def closeservice_action():
    global state
    message={"CMD": {"CloseService": 1337}}
    producer.send_message(message, "SPABoii.CloseService")


# To receive button commands from HA, define a callback function:
def my_callback(client: Client, user_data, message: MQTTMessage):
    if user_data == "closeservice": 
        closeservice_action()
    if user_data == "setpoint":
        print(f"Setpoint: {message.payload}°F")
        # Update the mock spa state
        spa_state["setpointF"] = float(message.payload)
        # Publish the new state to the MQTT broker
        message={"CMD": {"SetPoint": float(message.payload)}}
        producer.send_message(message, "SPABoii.SetPoint")

# To receive pump select commands from HA, define a callback function:
def pump_callback(client: Client, user_data, message: MQTTMessage):
    if user_data == "pump1":
        print(f"Pump1 select message: {message.payload}")

def read_settings_from_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            settings = yaml.safe_load(file)
        
        host = settings.get("host")
        username = settings.get("username")
        password = settings.get("password")

        return host, username, password
    except Exception as e:
        print(f"Error reading settings: {e}")
        return None, None, None

def init(SPAproducer):
    debug = False # True
    global state, producer
    producer = SPAproducer
    state = True
    file_path = "settings.yaml"
    host, username, password = read_settings_from_yaml(file_path)
    if debug:
        print(f"Connecting to MQTT:")
        print(f"MQTT Host: {host}, Username: {username}") # , Password: {password}")

    # Attempt to provide single client and avoid a broker connection per sensor
    # Doesn't appear to work on this version of ha_mqtt_discoverable
    #mqttClient = Client()
    #mqttClient.username_pw_set(username, password)
    #mqttClient.connect(host, 1883, 60)
    # Test only
    # mqttClient.publish("hmd/select/SPABoii-Pump1/state", 'HIGH', False)

    #mqttClient.loop_start()

    # Configure the required parameters for the MQTT broker
    mqtt_settings = Settings.MQTT(host=host, username=username, password=password, debug=debug)
    #mqtt_settings = Settings.MQTT(client=mqttClient, debug=debug)

    # Information about the button
    button_info = ButtonInfo(
        name="SPABoii.CloseService",
        # Needed to be able to assign an area (not working)
        unique_id="spa_restart_monitoring_service",
    )

    # Separate Settings object using same setting so only one MQTT connection
    closeServiceSettings = Settings(mqtt=mqtt_settings, entity=button_info)



    # Define an optional object to be passed back to the callback
    user_data = "closeservice"

    # Instantiate the button
    my_button = Button(closeServiceSettings, my_callback, user_data)

    # Publish the button's discoverability message to let HA automatically notice it
    my_button.write_config()

    #### Pump 1 ####
    pump1_info = SelectInfo(
        name="SPABoii.Pump1",
        unique_id="spa_pump1_mode",
        options=["OFF", "LOW", "HIGH"],
    )

    pump_data = "pump1"
    pump1Settings = Settings(mqtt=mqtt_settings, entity=pump1_info)

    # Instantiate the sensor
    pump1_select = Select(pump1Settings, pump_callback, pump_data)
    # pump1_select.set_option('OFF')

    pump1_select.write_config()
    
   
    # Information about the sensor
    sensor_info = SensorInfoExtra(
        name="SPABoii.CurrentTemp",
        #name="spa_temperature",
        device_class="temperature",
        unit_of_measurement="°C",
        suggested_display_precision=2,
        unique_id="spa_temp_sensor",
    )

    currentTempSettings = Settings(mqtt=mqtt_settings, entity=sensor_info)

    # Instantiate the sensor
    mysensor = Sensor(currentTempSettings)
    mysensor.write_config()

    mysensor.set_attributes({"my attribute": "awesome"})

    number_info = NumberInfoExtra(
        name="SPABoii.SetPoint",
        device_class="temperature",
        unit_of_measurement="°C",
        suggested_display_precision=2,
        unique_id="spa_setpoint_sensor",
        user_data="setpoint",
        min=10,
        max=40,
    )

    setPointSettings = Settings(mqtt=mqtt_settings, entity=number_info)

    # Instantiate the sensor
    mysetpoint = Number(setPointSettings, my_callback, "setpoint")
    mysetpoint.write_config()

    

    #get the state of the sensor
    

    #### Heater 1 ####
    #sensor_info = SensorInfoExtra(
    heater_info = BinarySensorInfo(
        name="SPABoii.Heater1",
        #suggested_display_precision=2,
        device_class="heat",
        unique_id="spa_heater1_sensor",
    )

    heaterSettings = Settings(mqtt=mqtt_settings, entity=heater_info)

    # Instantiate the sensor
    heater1_sensor = BinarySensor(heaterSettings)
    #heater1_sensor.set_state(70)
    #heater1_sensor.off();

    heater1_sensor.write_config()

    
    

    #create a sensor list, name value pair
    sensors=[]


    

    #add mysensor to a list, as name and value
    sensors.append(("Temperature", mysensor))
    sensors.append(("CloseService", my_button))
    sensors.append(("SetPoint", mysetpoint))
    sensors.append(("Heater1", heater1_sensor))
    sensors.append(("Pump1", pump1_select))
    
   
    

    

    return sensors


