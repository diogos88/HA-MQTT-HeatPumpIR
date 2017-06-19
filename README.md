# HA-MQTT-HeatPumpIR
HeatPumpIR component

### Features
- Control heat pump via mqtt
- Easy integration with [ESP8266](https://github.com/diogos88/ESPEasy)

## How To
### custom_components
Copy custom_components folder in your .homeassistant config folder

### configuration.yaml
Add the component to your configuration file
```sh
climate:
  - platform: heatpumpir
    name: 'Heat Pump'
    protocol: 'fujitsu_awyz'
    state_topic: '/heatpump/state'
    command_topic: '/heatpump/cmd'
    temperature_state_topic: '/heatpump/temperature/state'
    min_temp: 18
    max_temp: 30
```