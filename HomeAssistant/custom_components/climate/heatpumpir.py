'''
HeatpumpIR platform that offers a climate device to control remote device with ESPEasy - HeatPumpIR library.
'''
import asyncio

import logging

import voluptuous as vol

from homeassistant.core import callback

import homeassistant.components.mqtt as mqtt

from homeassistant.components.climate import (
    ClimateDevice, ATTR_MAX_TEMP, ATTR_MIN_TEMP, ATTR_TARGET_TEMP_STEP, 
    STATE_HEAT, STATE_COOL, STATE_IDLE, STATE_AUTO, STATE_DRY, STATE_FAN_ONLY,
    PLATFORM_SCHEMA)

from homeassistant.components.mqtt import (CONF_COMMAND_TOPIC, CONF_QOS,
    CONF_RETAIN, CONF_STATE_TOPIC)
    
from homeassistant.const import (
    CONF_NAME, TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE)

import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['mqtt']

DEFAULT_NAME = 'MQTT Heatpump IR'
DEFAULT_QOS = 0
DEFAULT_RETAIN = True
DEFAULT_MIN_TEMP = 18
DEFAULT_MAX_TEMP = 30
DEFAULT_TARGET_TEMP_STEP = 1.0

PROTOCOL_FUJITSU = 'fujitsu_awyz'

FAN_AUTO = 'Auto'
FAN_HIGH = 'High'
FAN_MED = 'Med'
FAN_LOW = 'Low'
FAN_QUIET = 'Quiet'

CONF_PROTOCOL = 'protocol'
CONF_TEMPERATURE_STATE_TOPIC = 'temperature_state_topic'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PROTOCOL): cv.string,
    vol.Required(CONF_STATE_TOPIC): mqtt.valid_subscribe_topic,
    vol.Required(CONF_COMMAND_TOPIC): mqtt.valid_publish_topic,
    vol.Required(CONF_TEMPERATURE_STATE_TOPIC): mqtt.valid_subscribe_topic,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(ATTR_MIN_TEMP, default=DEFAULT_MIN_TEMP): vol.Coerce(int),
    vol.Optional(ATTR_MAX_TEMP, default=DEFAULT_MAX_TEMP): vol.Coerce(int),
    vol.Optional(ATTR_TARGET_TEMP_STEP, default=DEFAULT_TARGET_TEMP_STEP): vol.Coerce(int),
})

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    protocol = config.get(CONF_PROTOCOL)
    stateTopic = config.get(CONF_STATE_TOPIC)
    commandTopic = config.get(CONF_COMMAND_TOPIC)
    temperatureStateTopic = config.get(CONF_TEMPERATURE_STATE_TOPIC)

    name = config.get(CONF_NAME)
    min_temp = config.get(ATTR_MIN_TEMP)
    max_temp = config.get(ATTR_MAX_TEMP)
    target_temp_step = config.get(ATTR_TARGET_TEMP_STEP)

    async_add_devices([
        HeatPumpIRPClimate(hass, name, protocol, stateTopic, commandTopic, 
                      temperatureStateTopic, min_temp, max_temp, target_temp_step, TEMP_CELSIUS)])

class HeatPumpIRPClimate(ClimateDevice):
    def __init__(self, hass, name, protocol, stateTopic, commandTopic, 
                temperatureStateTopic, min_temp, max_temp, target_temp_step, unit_of_measurement):
                
        self._hass = hass
        self._name = name
        
        self._qos = DEFAULT_QOS
        self._retain = DEFAULT_RETAIN
        
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._target_temperature_step = target_temp_step
        self._state_topic = stateTopic
        self._command_topic = commandTopic
        self._temperature_state_topic = temperatureStateTopic

        self._current_temperature = 20
        
        self._target_temperature = 20
        self._unit_of_measurement = unit_of_measurement
        self._away_mode = False
        
        self._protocol = protocol.lower()
        
        if self._protocol == PROTOCOL_FUJITSU:
            self._fan_list = [FAN_AUTO, FAN_QUIET, FAN_LOW, FAN_MED, FAN_HIGH]
            self._operation_list = [STATE_AUTO, STATE_HEAT, STATE_COOL, STATE_DRY, STATE_FAN_ONLY, STATE_IDLE]

            self._current_fan_mode = FAN_MED
            self._current_operation = STATE_FAN_ONLY
        else:
            _LOGGER.fatal('Protocol ' + self._protocol + ' not supported.')
            return self._protocol_not_supported

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Subscribe to MQTT events.
        This method is a coroutine.
        """
        
        """
        @callback
        def heatpump_state_received(topic, payload, qos):
            items = payload.split(',')
            
            if len(items) != 8:
                _LOGGER.warning("Invalid state : parameters")
                return
        
            if items[1] != self._protocol:
                _LOGGER.warning("Invalid state : protocol")
                return
            
            powerState = int(items[2])
            operationMode = int(items[3])
            fanSpeed = int(items[4])
            temperature = self.clamp(self._min_temp, int(items[5]), self._max_temp)
            vDirection = int(items[6])
            hDirection = int(items[7])
            
            if powerState == 0:
                self._current_operation = STATE_IDLE
            else:
                self._current_operation = self._operation_list[operationMode]
            
            self._current_fan_mode = self._fan_list[fanSpeed]
            self._target_temperature = temperature

            self.hass.async_add_job(self.async_update_ha_state())

        if self._state_topic is not None:
            yield from mqtt.async_subscribe(
                self.hass, self._state_topic, heatpump_state_received, self._qos)
        """      
        
        @callback
        def temperature_state_received(topic, payload, qos):
            self._current_temperature = int(payload)
            self.hass.async_add_job(self.async_update_ha_state())

        if self._temperature_state_topic is not None:
            yield from mqtt.async_subscribe(
                self.hass, self._temperature_state_topic, temperature_state_received, self._qos)

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def temperature_unit(self):
        return self._unit_of_measurement

    @property
    def min_temp(self):
        return self._min_temp

    @property
    def max_temp(self):
        return self._max_temp

    @property
    def current_temperature(self):
        return self._current_temperature
        
    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def target_temperature_step(self):
        return self._target_temperature_step

    @property
    def current_operation(self):
        return self._current_operation

    @property
    def operation_list(self):
        return self._operation_list

    @property
    def is_away_mode_on(self):
        return self._away_mode

    @property
    def current_fan_mode(self):
        return self._current_fan_mode

    @property
    def fan_list(self):
        return self._fan_list

    def set_temperature(self, **kwargs):
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = int(kwargs.get(ATTR_TEMPERATURE))
        
        self.send_command()
        self.schedule_update_ha_state()
    
    def set_fan_mode(self, fan_mode):
        self._current_fan_mode = fan_mode  
        self.send_command()    
        self.schedule_update_ha_state()

    def set_operation_mode(self, operation_mode):
        self._current_operation = operation_mode
        self.send_command()
        self.schedule_update_ha_state()

    def turn_away_mode_on(self):
        '''Turn away mode on.'''
        self._away_mode = True
        self.send_command()
        self.schedule_update_ha_state()

    def turn_away_mode_off(self):
        self._away_mode = False
        self.send_command()
        self.schedule_update_ha_state()

    def clamp(self, minimum, x, maximum):
        return max(minimum, min(x, maximum))
        
    def send_command(self):
        powerState = int(self._current_operation != STATE_IDLE)
        operationMode = self._operation_list.index(self._current_operation) + 1
        fanSpeed = self._fan_list.index(self._current_fan_mode)
        temperature = self._target_temperature
        if self._away_mode == True:
            if self._current_operation == STATE_COOL:
                temperature += 4;
            elif self._current_operation == STATE_HEAT:
                temperature -= 4;
                
        temperature = self.clamp(self._min_temp, temperature, self._max_temp)
                
        vDirection = 0
        hDirection = 0
        
        mqtt_payload = 'heatpumpir,' + self._protocol + ',' + str(powerState) + ',' + str(operationMode) +',' + str(fanSpeed) + ',' + str(temperature) + ',' + str(vDirection) + ',' + str(hDirection)
        mqtt.async_publish(self.hass, self._command_topic, mqtt_payload, self._qos, self._retain)

        _LOGGER.debug(self._name + ' command payload ' + mqtt_payload)
