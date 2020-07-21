"""
Interfaces with the Visonic Alarm control panel.
"""
import logging
from time import sleep
from datetime import timedelta

import homeassistant.components.alarm_control_panel as alarm
import homeassistant.components.persistent_notification as pn
from homeassistant.const import (STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME,
                                 STATE_ALARM_DISARMED, STATE_UNKNOWN,
                                 STATE_ALARM_ARMING, STATE_ALARM_PENDING, STATE_ALARM_TRIGGERED )
from homeassistant.const import (EVENT_STATE_CHANGED)
from homeassistant.const import (ATTR_CODE_FORMAT)
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME
)
from . import HUB as hub
from . import (CONF_USER_CODE, CONF_EVENT_HOUR_OFFSET, CONF_NO_PIN_REQUIRED, CONF_ARM_DISARM_INSTANT)

SUPPORT_VISONIC = (SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY)

_LOGGER = logging.getLogger(__name__)

ATTR_SYSTEM_NAME = 'system_name'
ATTR_SYSTEM_SERIAL_NUMBER = 'serial_number'
ATTR_SYSTEM_MODEL = 'model'
ATTR_SYSTEM_READY = 'ready'
ATTR_SYSTEM_ACTIVE = 'active'
ATTR_SYSTEM_CONNECTED = 'connected'
ATTR_SYSTEM_SESSION_TOKEN = 'session_token'
ATTR_SYSTEM_LAST_UPDATE = 'last_update'
ATTR_CODE_FORMAT = 'code_format'
ATTR_CHANGED_BY = 'changed_by'
ATTR_CHANGED_TIMESTAMP = 'changed_timestamp'
ATTR_ALARMS = 'alarm'

SCAN_INTERVAL = timedelta(seconds=10)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Set up the Visonic Alarm platform. """
    hub.update()
    visonic_alarm = VisonicAlarm(hass)
    add_devices([visonic_alarm])

    # Create an event listener to listen for changed arm state.
    # We will only fetch the events from the API once the arm state has changed
    # because it is quite a lot of data.
    def arm_event_listener(event):
        entity_id = event.data.get('entity_id')
        old_state = event.data.get('old_state')
        new_state = event.data.get('new_state')

        if new_state is None or new_state.state in (STATE_UNKNOWN, ''):
            return None

        if entity_id == 'alarm_control_panel.visonic_alarm' and \
                old_state.state is not new_state.state:
            state = new_state.state
            if state == 'armed_home' or state == 'armed_away' or \
                    state == 'disarmed':
                last_event = hub.alarm.get_last_event(
                    timestamp_hour_offset=visonic_alarm.event_hour_offset)
                visonic_alarm.update_last_event(last_event['user'],
                                                last_event['timestamp'])

    hass.bus.listen(EVENT_STATE_CHANGED, arm_event_listener)


class VisonicAlarm(alarm.AlarmControlPanelEntity):
    """ Representation of a Visonic Alarm control panel. """

    def __init__(self, hass):
        """ Initialize the Visonic Alarm panel. """
        self._hass = hass
        self._state = STATE_UNKNOWN
        self._code = hub.config.get(CONF_USER_CODE)
        self._no_pin_required = hub.config.get(CONF_NO_PIN_REQUIRED)
        self._arm_disarm_instant = hub.config.get(CONF_ARM_DISARM_INSTANT)
        self._changed_by = None
        self._changed_timestamp = None
        self._event_hour_offset = hub.config.get(CONF_EVENT_HOUR_OFFSET)
        self._alarm = False

    @property
    def name(self):
        """ Return the name of the device. """
        return 'Visonic Alarm'

    @property
    def state_attributes(self):
        """ Return the state attributes of the alarm system. """
        return {
            ATTR_SYSTEM_SERIAL_NUMBER: hub.alarm.serial_number,
            ATTR_SYSTEM_NAME: hub.alarm.name,
            ATTR_SYSTEM_MODEL: hub.alarm.model,
            ATTR_SYSTEM_READY: hub.alarm.ready,
            ATTR_SYSTEM_ACTIVE: hub.alarm.active,
            ATTR_SYSTEM_CONNECTED: hub.alarm.connected,
            ATTR_SYSTEM_SESSION_TOKEN: hub.alarm.session_token,
            ATTR_SYSTEM_LAST_UPDATE: hub.last_update,
            ATTR_CODE_FORMAT: self.code_format,
            ATTR_CHANGED_BY: self.changed_by,
            ATTR_CHANGED_TIMESTAMP: self._changed_timestamp,
            ATTR_ALARMS: hub.alarm.alarm,
        }

    @property
    def icon(self):
        """ Return icon """
        if self._state == STATE_ALARM_ARMED_AWAY:
            return 'mdi:lock'
        elif self._state == STATE_ALARM_ARMED_HOME:
            return 'mdi:lock-outline'
        elif self._state == STATE_ALARM_DISARMED:
            return 'mdi:lock-open'
        elif self._state == STATE_ALARM_ARMING:
            return 'mdi:lock-clock'
        else:
            return 'mdi:lock-alert'

    @property
    def state(self):
        """ Return the state of the device. """
        return self._state

    @property
    def code_format(self):
        """ Return one or more digits/characters. """
        if self._no_pin_required:
            return None
        else:
            return 'Number'

    @property
    def changed_by(self):
        """ Return the last change triggered by. """
        return self._changed_by

    @property
    def changed_timestamp(self):
        """ Return the last change triggered by. """
        return self._changed_timestamp

    @property
    def event_hour_offset(self):
        """ Return the hour offset to be used in the event log. """
        return self._event_hour_offset

    def update_last_event(self, user, timestamp):
        """ Update with the user and timestamp of the last state change. """
        self._changed_by = user
        self._changed_timestamp = timestamp

    def update(self):
        """ Update alarm status. """
        hub.update()
        status = hub.alarm.state
        if status == 'Away' or status == 'Away Instant':
            self._state = STATE_ALARM_ARMED_AWAY
        elif status == 'Home' or status == 'Home Instant':
            self._state = STATE_ALARM_ARMED_HOME
        elif status == 'Disarm':
            self._state = STATE_ALARM_DISARMED
        elif status == 'ExitDelayHome' or status == 'ExitDelayAway' or status == 'ExitDelayHome Instant' or status == 'ExitDelayAway Instant':
            self._state = STATE_ALARM_ARMING
        elif status == 'EntryDelay':
            self._state = STATE_ALARM_PENDING
        elif status == 'Alarm':
            self._state = STATE_ALARM_TRIGGERED
        else:
            self._state = status

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_VISONIC

    def alarm_disarm(self, code=None):
        """ Send disarm command. """
        if self._no_pin_required == False:
            if code != self._code:
                pn.create(self._hass, 'You entered the wrong disarm code.', title='Disarm Failed')
                return
            
        hub.alarm.disarm()
        sleep(1)
        self.update()

    def alarm_arm_home(self, code=None):
        """ Send arm home command. """
        if self._no_pin_required == False:
            if code != self._code:
                pn.create(self._hass, 'You entered the wrong arm code.', title='Arm Failed')
                return

        if hub.alarm.ready:
            if self._arm_disarm_instant:
                hub.alarm.arm_home_instant()
            else:
                hub.alarm.arm_home()

            sleep(1)
            self.update()
        else:
            pn.create(self._hass, 'The alarm system is not in a ready state. '
                                  'Maybe there are doors or windows open?',
                      title='Arm Failed')

    def alarm_arm_away(self, code=None):
        """ Send arm away command. """
        if self._no_pin_required == False:
            if code != self._code:
                pn.create(self._hass, 'You entered the wrong arm code.', title='Unable to Arm')
                return
            
        if hub.alarm.ready:
            if self._arm_disarm_instant:
                hub.alarm.arm_away_instant()
            else:
                hub.alarm.arm_away()

            sleep(1)
            self.update()
        else:
            pn.create(self._hass, 'The alarm system is not in a ready state. '
                                  'Maybe there are doors or windows open?',
                      title='Unable to Arm')
