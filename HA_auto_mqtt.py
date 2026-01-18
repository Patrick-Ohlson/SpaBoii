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
    SelectInfo,
    Switch,
    SwitchInfo
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

# --- NEW: Custom classes to add our field ---
class SensorInfoExtra(SensorInfo):
    suggested_display_precision: int = 0

class NumberInfoExtra(NumberInfo):
    suggested_display_precision: int = 0
# ------------------------------------------

# To receive button commands from HA, define a callback function:
def my_callback(client: Client, user_data, message: MQTTMessage):
    # This callback now handles all stateless buttons
    
    if user_data == "closeservice": 
        print("CloseService button pressed")
        msg={"CMD": {"CloseService": 1337}}
        producer.cmd_queue.put(msg)

    if user_data == "setpoint":
        print(f"Setpoint: {message.payload}°F")
        # Publish the new state to the MQTT broker
        msg={"CMD": {"SetPoint": float(message.payload)}}
        # Use producer.cmd_queue directly
        producer.cmd_queue.put(msg)

    if user_data == "boost":
        print("Boost button pressed")
        msg={"CMD": {"boost": "ON"}}
        producer.cmd_queue.put(msg)


# To receive pump select commands from HA, define a callback function:
def pump_callback(client: Client, user_data, message: MQTTMessage):
    if user_data == "pump1":
        command_state = message.payload.decode('utf-8') # "OFF", "LOW", "HIGH"
        print(f"Pump1 select message: {command_state}")
        
        # Create the command message
        msg = {"CMD": { "pump1": command_state }}
        
        # Use producer.cmd_queue directly
        producer.cmd_queue.put(msg)

# To receive switch commands from HA, define a callback function:
def switch_callback(client: Client, user_data, message: MQTTMessage):
    # user_data will be "lights", "pump2", "pump3", "blower1", "blower2"
    # message.payload will be b'ON' or b'OFF'
    command_name = str(user_data) # "lights", "pump2", etc.
    command_state = message.payload.decode('utf-8') # "ON" or "OFF"
    print(f"Switch '{command_name}' command: {command_state}")

    # Create the command message
    msg = {"CMD": { command_name: command_state }}
    
    # Use producer.cmd_queue directly
    producer.cmd_queue.put(msg)

# --- NEW CALLBACK FOR Cl Range ---
# --- UPDATED CALLBACK WITH DEBUGGING ---
def cl_range_callback(client: Client, user_data, message: MQTTMessage):
    # Print EVERYTHING received to debug the trigger
    payload = message.payload.decode('utf-8')
    print(f"DEBUG: MQTT Callback Triggered! Data: {user_data}, Payload: {payload}")

    if user_data == "cl_range":
        print(f"Cl Range select message: {payload}")
        msg = {"CMD": { "cl_range": payload }}
        producer.cmd_queue.put(msg)
# --- END NEW CALLBACK ---

def read_settings_from_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            settings = yaml.safe_load(file)
        
        # Use .get() to avoid errors if keys are missing
        host = settings.get("host")
        username = settings.get("username")
        password = settings.get("password")
        spa_ip = settings.get("spa_ip")

        return host, username, password, spa_ip
    except Exception as e:
        print(f"Error reading settings: {e}")
        return None, None, None, None

def init(SPAproducer):
    debug = False
    global state, producer
    producer = SPAproducer
    state = True
    file_path = "settings.yaml"
    host, username, password, spa_ip = read_settings_from_yaml(file_path)
    if debug:
        print(f"Connecting to MQTT:")
        print(f"MQTT Host: {host}, Username: {username}") # , Password: {password}")

    # Configure the required parameters for the MQTT broker
    mqtt_settings = Settings.MQTT(host=host, username=username, password=password, debug=debug)

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
    pump1_select.write_config()
    
    sensor_info = SensorInfoExtra(
        name="SPABoii.CurrentTemp",
        device_class="temperature",
        unit_of_measurement="°F",
        unique_id="spa_temp_sensor",
        suggested_display_precision=0,
    )

    currentTempSettings = Settings(mqtt=mqtt_settings, entity=sensor_info)

    # Instantiate the sensor
    mysensor = Sensor(currentTempSettings)
    mysensor.write_config()
    mysensor.set_attributes({"my attribute": "awesome"})

    number_info = NumberInfoExtra(
        name="SPABoii.SetPoint",
        device_class="temperature",
        unique_id="spa_setpoint_sensor",
        user_data="setpoint",
        min=80, 
        max=104, 
        suggested_display_precision=0,
    )

    setPointSettings = Settings(mqtt=mqtt_settings, entity=number_info)

    # Instantiate the sensor
    mysetpoint = Number(setPointSettings, my_callback, "setpoint")
    mysetpoint.write_config()
    

    #### Heater 1 ####
    heater_info = BinarySensorInfo(
        name="SPABoii.Heater1",
        device_class="heat",
        unique_id="spa_heater1_sensor",
    )

    heaterSettings = Settings(mqtt=mqtt_settings, entity=heater_info)

    # Instantiate the sensor
    heater1_sensor = BinarySensor(heaterSettings)
    heater1_sensor.write_config()

    
    #### ---------- ADDED NEW ENTITIES BELOW ---------- ####

    #### Heater 2 ####
    heater2_info = BinarySensorInfo(
        name="SPABoii.Heater2",
        device_class="heat",
        unique_id="spa_heater2_sensor",
    )
    heater2Settings = Settings(mqtt=mqtt_settings, entity=heater2_info)
    heater2_sensor = BinarySensor(heater2Settings)
    heater2_sensor.write_config()

    #### Lights ####
    lights_info = SwitchInfo(
        name="SPABoii.Lights",
        unique_id="spa_lights_switch",
    )
    lightsSettings = Settings(mqtt=mqtt_settings, entity=lights_info)
    lights_switch = Switch(lightsSettings, switch_callback, "lights")
    lights_switch.write_config()

    #### Pump 2 ####
    pump2_info = SwitchInfo(
        name="SPABoii.Pump2",
        unique_id="spa_pump2_switch",
        icon="mdi:pump",
    )
    pump2Settings = Settings(mqtt=mqtt_settings, entity=pump2_info)
    pump2_switch = Switch(pump2Settings, switch_callback, "pump2")
    pump2_switch.write_config()

    #### Pump 3 ####
    pump3_info = SwitchInfo(
        name="SPABoii.Pump3",
        unique_id="spa_pump3_switch",
        icon="mdi:pump",
    )
    pump3Settings = Settings(mqtt=mqtt_settings, entity=pump3_info)
    pump3_switch = Switch(pump3Settings, switch_callback, "pump3")
    pump3_switch.write_config()

    #### Blower 1 ####
    blower1_info = SwitchInfo(
        name="SPABoii.Blower1",
        unique_id="spa_blower1_switch",
        icon="mdi:weather-windy",
    )
    blower1Settings = Settings(mqtt=mqtt_settings, entity=blower1_info)
    blower1_switch = Switch(blower1Settings, switch_callback, "blower1")
    blower1_switch.write_config()

    #### Blower 2 ####
    blower2_info = SwitchInfo(
        name="SPABoii.Blower2",
        unique_id="spa_blower2_switch",
        icon="mdi:weather-windy",
    )
    blower2Settings = Settings(mqtt=mqtt_settings, entity=blower2_info)
    blower2_switch = Switch(blower2Settings, switch_callback, "blower2")
    blower2_switch.write_config()
    
    # ----- ADDED Boost BUTTON ----- #
    #### Boost Button ####
    boost_info = ButtonInfo(
        name="SPABoii.Boost",
        unique_id="spa_boost_button",
        icon="mdi:rocket-launch",
    )
    boostSettings = Settings(mqtt=mqtt_settings, entity=boost_info)
    # Re-use the main my_callback, passing "boost" as the user_data
    boost_button = Button(boostSettings, my_callback, "boost")
    boost_button.write_config()
    # ---------------------------------- #

    # ----- ADDED pH and ORP SENSORS ----- #
    #### pH Sensor ####
    ph_info = SensorInfoExtra(
        name="SPABoii.pH",
        device_class="ph",
        unique_id="spa_ph_sensor",
        suggested_display_precision=2,
    )
    phSettings = Settings(mqtt=mqtt_settings, entity=ph_info)
    ph_sensor = Sensor(phSettings)
    ph_sensor.write_config()

    #### ORP Sensor ####
    orp_info = SensorInfoExtra(
        name="SPABoii.ORP",
        icon="mdi:gauge",
        unit_of_measurement="mV",
        unique_id="spa_orp_sensor",
        suggested_display_precision=0,
    )
    orpSettings = Settings(mqtt=mqtt_settings, entity=orp_info)
    orp_sensor = Sensor(orpSettings)
    orp_sensor.write_config()
    # ------------------------------------ #

    # ----- ADDED Cl Range SELECT ----- #
    cl_range_info = SelectInfo(
        name="SPABoii.ClRange",
        unique_id="spa_cl_range_select",
        options=["Low", "Mid", "High"],
        icon="mdi:creation",
        # FORCE the topics so there is no ambiguity about case sensitivity
        command_topic="hmd/select/SPABoii-ClRange/command",
        state_topic="hmd/select/SPABoii-ClRange/state"
    )
    clRangeSettings = Settings(mqtt=mqtt_settings, entity=cl_range_info)
    cl_range_select = Select(clRangeSettings, cl_range_callback, "cl_range")
    cl_range_select.write_config()
    # --------------------------------- #

    # ----- ADDED NEW STATUS SENSORS ----- #
    #### Filter Status ####
    filter_status_info = SensorInfo(
        name="SPABoii.FilterStatus",
        unique_id="spa_filter_status_sensor",
        icon="mdi:filter",
    )
    filterStatusSettings = Settings(mqtt=mqtt_settings, entity=filter_status_info)
    filter_status_sensor = Sensor(filterStatusSettings)
    filter_status_sensor.write_config()

    #### Ozone Status ####
    ozone_status_info = SensorInfo(
        name="SPABoii.OzoneStatus",
        unique_id="spa_ozone_status_sensor",
        icon="mdi:air-filter",
    )
    ozoneStatusSettings = Settings(mqtt=mqtt_settings, entity=ozone_status_info)
    ozone_status_sensor = Sensor(ozoneStatusSettings)
    ozone_status_sensor.write_config()

    #### Heater ADC ####
    heater_adc_info = SensorInfo(
        name="SPABoii.HeaterADC",
        unique_id="spa_heater_adc_sensor",
        unit_of_measurement="ADC",
        icon="mdi:chart-line",
    )
    heaterAdcSettings = Settings(mqtt=mqtt_settings, entity=heater_adc_info)
    heater_adc_sensor = Sensor(heaterAdcSettings)
    heater_adc_sensor.write_config()

    #### Current ADC ####
    current_adc_info = SensorInfo(
        name="SPABoii.CurrentADC",
        unique_id="spa_current_adc_sensor",
        unit_of_measurement="ADC",
        icon="mdi:current-ac",
    )
    currentAdcSettings = Settings(mqtt=mqtt_settings, entity=current_adc_info)
    current_adc_sensor = Sensor(currentAdcSettings)
    current_adc_sensor.write_config()

    #### Heater 1 Status ####
    heater1_status_info = SensorInfo(
        name="SPABoii.Heater1Status",
        unique_id="spa_heater1_status_sensor",
        icon="mdi:heat-wave",
    )
    heater1StatusSettings = Settings(mqtt=mqtt_settings, entity=heater1_status_info)
    heater1_status_sensor = Sensor(heater1StatusSettings)
    heater1_status_sensor.write_config()

    #### Heater 2 Status ####
    heater2_status_info = SensorInfo(
        name="SPABoii.Heater2Status",
        unique_id="spa_heater2_status_sensor",
        icon="mdi:heat-wave",
    )
    heater2StatusSettings = Settings(mqtt=mqtt_settings, entity=heater2_status_info)
    heater2_status_sensor = Sensor(heater2StatusSettings)
    heater2_status_sensor.write_config()

    # --- ADDED CONNECTION SENSOR ---
    #### Connection Status ####
    connection_info = BinarySensorInfo(
        name="SPABoii.ConnectionStatus",
        unique_id="spa_connection_status_sensor",
        device_class="connectivity",
    )
    connectionSettings = Settings(mqtt=mqtt_settings, entity=connection_info)
    connection_sensor = BinarySensor(connectionSettings)
    connection_sensor.write_config()
    # ------------------------------- #
    

    #create a sensor list, name value pair
    sensors=[]


    

    #add mysensor to a list, as name and value
    sensors.append(("Temperature", mysensor))
    sensors.append(("CloseService", my_button))
    sensors.append(("SetPoint", mysetpoint))
    sensors.append(("Heater1", heater1_sensor))
    sensors.append(("Pump1", pump1_select))
    
    # --- ADDED NEW SENSORS TO LIST --- #
    sensors.append(("Heater2", heater2_sensor))
    sensors.append(("Lights", lights_switch))
    sensors.append(("Pump2", pump2_switch))
    sensors.append(("Pump3", pump3_switch))
    sensors.append(("Blower1", blower1_switch))
    sensors.append(("Blower2", blower2_switch))
    sensors.append(("PH", ph_sensor)) 
    sensors.append(("ORP", orp_sensor)) 
    sensors.append(("Boost", boost_button))
    sensors.append(("ClRange", cl_range_select))
    
    # --- ADDED NEW STATUS SENSORS TO LIST --- #
    sensors.append(("FilterStatus", filter_status_sensor))
    sensors.append(("OzoneStatus", ozone_status_sensor))
    sensors.append(("HeaterADC", heater_adc_sensor))
    sensors.append(("CurrentADC", current_adc_sensor))
    sensors.append(("Heater1Status", heater1_status_sensor))
    sensors.append(("Heater2Status", heater2_status_sensor))

    # --- ADDED CONNECTION SENSOR TO LIST ---
    sensors.append(("ConnectionStatus", connection_sensor))
    
    
    return sensors, spa_ip
