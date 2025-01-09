## SPA Boii - No cloud access to ARCTIC SPA based systems
## Disclaimer
USE AT OWN RISK, I TAKE NO RESPONSIBILITY FOR ANY ERRORS THIS MIGHT CAUSE

[License](License.md)

## Background 
This started with the Home Assistant Forum thread, regarding Arctic SPA API

https://community.home-assistant.io/t/jacuzzi-arctic-spas-api/464596

It might get it's own thread

## Preface

This is boilerplate code for accessing Arctic Spa's and derivatives with python 3.8

Feel free to test it with your own spa, it requires Home Assistant with MQTT and somewhere to run Python

## Requirements
Python 3.8 (or above)
see requirements.txt

create a settings.yaml with:

host: YOURMQTT

username: MQTTUSERNAME

password: PASSWORD

## Usage
python SpaBoii.py

This should locate the SPA on your network and and initialize HA via Mqtt


SPABoii.SetPoint = Sets target temperature and starts heaters, lower than current temp stops heaters

SPABoii.CurrentTemp = Current SPA temp

SPABoii.Heater1 = Shows current status of heaters

SPABoii.CloseService = Button for restart of service



REMEMBER: This is boilerplate code, meant to provide a basic codebase for communication with Arctic SPA's

SO USE AT OWN RISK, I TAKE NO RESPONSIBILITY FOR ANY ERRORS THIS MIGHT CAUSE




