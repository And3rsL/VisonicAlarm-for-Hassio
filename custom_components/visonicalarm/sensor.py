"""
Interfaces with the Visonic Alarm sensors.
"""
import logging
from datetime import timedelta

from . import HUB as hub
from homeassistant.const import (STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME)
from homeassistant.const import (STATE_ALARM_DISARMED, STATE_UNKNOWN,
                                 STATE_OPEN, STATE_CLOSED)
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

STATE_ALARM_ARMING_EXIT_DELAY_HOME = 'arming_exit_delay_home'
STATE_ALARM_ARMING_EXIT_DELAY_AWAY = 'arming_exit_delay_away'
STATE_ALARM_ENTRY_DELAY = 'entry_delay'

STATE_ATTR_SYSTEM_NAME = 'system_name'
STATE_ATTR_SYSTEM_SERIAL_NUMBER = 'serial_number'
STATE_ATTR_SYSTEM_MODEL = 'model'
STATE_ATTR_SYSTEM_READY = 'ready'
STATE_ATTR_SYSTEM_ACTIVE = 'active'
STATE_ATTR_SYSTEM_CONNECTED = 'connected'

CONTACT_ATTR_ZONE = 'zone'
CONTACT_ATTR_LOCATION = 'location'
CONTACT_ATTR_DEVICE_TYPE = 'device_type'
CONTACT_ATTR_TYPE = 'type'
CONTACT_ATTR_SUBTYPE = 'subtype'

SCAN_INTERVAL = timedelta(seconds=10)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Visonic Alarm platform."""
    hub.update()

    for device in hub.alarm.devices:
        if device.subtype == 'CONTACT_AUX' or device.subtype == 'CONTACT' or device.subtype == 'MOTION_CAMERA' or device.subtype == 'MOTION' or device.subtype == 'CURTAIN':
          _LOGGER.debug("New device found [Type:" + str(device.subtype) + "] [ID:" + str(device.id) + "]")
          add_devices([VisonicAlarmContact(hub.alarm, device.id)], True)


class VisonicAlarmContact(Entity):
    """ Implementation of a Visonic Alarm Contact sensor. """

    def __init__(self, alarm, contact_id):
        """ Initialize the sensor """
        self._state = STATE_UNKNOWN
        self._alarm = alarm
        self._id = contact_id
        self._zone = None
        self._location = None
        self._device_type = None
        self._type = None
        self._subtype = None

    @property
    def name(self):
        """ Return the name of the sensor """
        return 'Visonic Alarm ' + str(self._id)

    @property
    def state_attributes(self):
        """Return the state attributes of the alarm system."""
        return {
            CONTACT_ATTR_ZONE: self._zone,
            CONTACT_ATTR_LOCATION: self._location,
            CONTACT_ATTR_DEVICE_TYPE: self._device_type,
            CONTACT_ATTR_TYPE: self._type,
            CONTACT_ATTR_SUBTYPE: self._subtype
        }

    @property
    def icon(self):
        """ Return icon """
        icon = None
        if self._state == STATE_CLOSED:
            icon = 'mdi:door-closed'
        elif self._state == STATE_OPEN:
            icon = 'mdi:door-open'
        return icon

    @property
    def state(self):
        """ Return the state of the sensor. """
        return self._state

    def update(self):
        """ Get the latest data """
        try:
            hub.update()

            device = self._alarm.get_device_by_id(self._id)

            status = device.state

            if status is None:
                _LOGGER.warning("Device could not be found: %s.", self._id)
                return

            if status == 'opened':
                self._state = STATE_OPEN
            elif status == 'closed':
                self._state = STATE_CLOSED
            else:
                self._state = STATE_UNKNOWN

            self._zone = device.zone
            self._location = device.location
            self._device_type = device.device_type
            self._type = device.type
            self._subtype = device.subtype

            _LOGGER.debug("Device state updated to %d W", self._state)
        except OSError as error:
            _LOGGER.warning("Could not update the device information: %s", error)
