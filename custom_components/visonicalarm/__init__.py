"""
Support for Visonic Alarm components.

"""
import logging
import threading
from datetime import timedelta
from datetime import datetime

import voluptuous as vol

from homeassistant.const import (CONF_HOST, CONF_NAME)
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['visonicalarm2==2.1.0', 'python-dateutil==2.7.3']

_LOGGER = logging.getLogger(__name__)

CONF_ALARM = 'alarm'
CONF_DOOR_WINDOW = 'door_window'
CONF_NO_PIN_REQUIRED = 'no_pin_required'
CONF_ARM_DISARM_INSTANT = 'arm_disarm_instant'
CONF_USER_CODE = 'user_code'
CONF_USER_ID = 'user_id'
CONF_PANEL_ID = 'panel_id'
CONF_PARTITION = 'partition'
CONF_EVENT_HOUR_OFFSET = 'event_hour_offset'

STATE_ATTR_SYSTEM_NAME = 'system_name'
STATE_ATTR_SYSTEM_SERIAL_NUMBER = 'serial_number'
STATE_ATTR_SYSTEM_MODEL = 'model'
STATE_ATTR_SYSTEM_READY = 'ready'
STATE_ATTR_SYSTEM_ACTIVE = 'active'
STATE_ATTR_SYSTEM_CONNECTED = 'connected'

DEFAULT_NAME = 'Visonic Alarm'
DEFAULT_PARTITION = 'ALL'

DOMAIN = 'visonicalarm'

HUB = None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USER_CODE): cv.string,
        vol.Required(CONF_USER_ID): cv.string,
        vol.Required(CONF_PANEL_ID): cv.string,
        vol.Optional(CONF_PARTITION, default=DEFAULT_PARTITION): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ALARM, default=True): cv.boolean,
        vol.Optional(CONF_DOOR_WINDOW, default=True): cv.boolean,
        vol.Optional(CONF_NO_PIN_REQUIRED, default=False): cv.boolean,
        vol.Optional(CONF_ARM_DISARM_INSTANT, default=False): cv.boolean,
        vol.Optional(CONF_EVENT_HOUR_OFFSET, default=0): vol.All(vol.Coerce(int), vol.Range(min=-24, max=24)),
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """ Setup the Visonic Alarm component."""
    from visonic import alarm as visonicalarm
    global HUB
    HUB = VisonicAlarmHub(config[DOMAIN], visonicalarm)
    if not HUB.connect():
        return False

    HUB.update()

    # Load the supported platforms
    for component in ('sensor', 'alarm_control_panel'):
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True


class VisonicAlarmHub(Entity):
    """ A Visonic Alarm hub wrapper class. """

    def __init__(self, domain_config, visonicalarm):
        """ Initialize the Visonic Alarm hub. """

        self.config = domain_config
        self._visonicalarm = visonicalarm
        self._last_update = None

        self._lock = threading.Lock()

        self.alarm = visonicalarm.System(domain_config[CONF_HOST],
                                         domain_config[CONF_USER_CODE],
                                         domain_config[CONF_USER_ID],
                                         domain_config[CONF_PANEL_ID],
                                         domain_config[CONF_PARTITION])

    def connect(self):
        """ Setup a connection to the Visonic API server. """
        try:
            self.alarm.connect()
            return True
        except Exception as ex:
            _LOGGER.error('Connection failed: %s', ex)
            return False

    @property
    def last_update(self):
        """ Return the last update timestamp. """
        return self._last_update

    @Throttle(timedelta(seconds=10))
    def update(self):
        """ Update all alarm statuses. """
        try:
            if self.alarm.is_token_valid == False:
                self.alarm.connect()
            
            self.alarm.update_status()
            #self.alarm.update_alarms()
            #self.alarm.update_troubles()
            #self.alarm.update_alerts()
            self.alarm.update_devices()

            self._last_update = datetime.now()
#            _LOGGER.error('Update went OK [%s].', self.alarm.model)
        except Exception as ex:
            _LOGGER.error('Update failed: %s', ex)
            raise

    @property
    def name(self):
        """ Return the name of the hub."""
        return "Visonic Alarm Hub"
