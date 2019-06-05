import json
import requests
from dateutil.relativedelta import *

from datetime import datetime
from dateutil import parser


class Device(object):
    """ Base class definition of a device in the alarm system. """

    # Property variables
    __id = None
    __zone = None
    __location = None
    __device_type = None
    __type = None
    __subtype = None
    __preenroll = None
    __soak = None
    __bypass = None
    __alarms = None
    __alerts = None
    __troubles = None
    __bypass_availability = None
    __partitions = None

    def __init__(self, id, zone, location, device_type, type, subtype,
                 preenroll, soak, bypass, alarms, alerts, troubles,
                 bypass_availability, partitions):
        """ Set the private variable values on instantiation. """

        self.__id = id
        self.__zone = zone
        self.__location = location
        self.__device_type = device_type
        self.__type = type
        self.__subtype = subtype
        self.__preenroll = preenroll
        self.__soak = soak
        self.__bypass = bypass
        self.__alarms = alarms
        self.__alerts = alerts
        self.__troubles = troubles
        self.__bypass_availability = bypass_availability
        self.__partitions = partitions

    # Device properties
    @property
    def id(self):
        """ Device ID. """
        return self.__id

    @property
    def zone(self):
        """ Device zone. """
        return self.__zone

    @property
    def location(self):
        """ Device location. """
        return self.__location

    @property
    def device_type(self):
        """ Device: device type. """
        return self.__device_type

    @property
    def type(self):
        """ Device type. """
        return self.__type

    @property
    def subtype(self):
        """ Device subtype. """
        return self.__subtype

    @property
    def pre_enroll(self):
        """ Device pre_enroll. """
        return self.__preenroll

    @property
    def soak(self):
        """ Device soak. """
        return self.__soak

    @property
    def bypass(self):
        """ Device bypassed. """
        return self.__bypass

    @property
    def alarms(self):
        """ Device alarm count. """
        return self.__alarms

    @property
    def alerts(self):
        """ Device alert count. """
        return self.__alerts

    @property
    def troubles(self):
        """ Device trouble count. """
        return self.__troubles

    @property
    def bypass_availability(self):
        """ Device bypass_availability. """
        return self.__bypass_availability

    @property
    def partitions(self):
        """ Device partitions. """
        return self.__partitions


class ContactDevice(Device):
    """ Contact device class definition. """

    @property
    def state(self):
        """ Returns the current state of the contact. """

        if self.troubles:
            if 'OPENED' in self.troubles:
                return 'opened'
        else:
            return 'closed'


class CameraDevice(Device):
    """ Camera device class definition. """
    pass


class SmokeDevice(Device):
    """ Smoke device class definition. """
    pass


class GenericDevice(Device):
    """ Smoke device class definition. """
    pass


class System(object):
    """ Class definition of the main alarm system. """

    # API Connection
    __api = None

    # Property variables
    __system_name = None
    __system_serial = None
    __system_model = None
    __system_ready = False
    __system_state = None
    __system_active = False
    __system_connected = False
    __system_devices = []
    __is_master_user = False

    def __init__(self, hostname, user_code, user_id, panel_id, partition):
        """ Initiate the connection to the Visonic API """
        self.__api = API(hostname, user_code, user_id, panel_id, partition)

    # System properties
    @property
    def serial_number(self):
        """ Serial number of the system. """
        return self.__system_serial

    @property
    def name(self):
        """ Name of the system. """
        return self.__system_name

    @property
    def model(self):
        """ Model of the system. """
        return self.__system_model

    @property
    def ready(self):
        """ If the system is ready to be armed. If doors or windows are open
        the system can't be armed. """
        return self.__system_ready

    @property
    def state(self):
        """ Current state of the alarm system. """
        return self.__system_state

    @property
    def active(self):
        """ If the alarm system is active or not. """
        return self.__system_active

    @property
    def session_token(self):
        """ Return the current session token. """
        return self.__api.session_token

    @property
    def connected(self):
        """ If the alarm system is connected to the API server or not. """
        return self.__system_connected

    @property
    def devices(self):
        """ A list of devices connected to the alarm system and their state. """
        return self.__system_devices

    def get_device_by_id(self, id):
        """ Get a device by its ID. """
        for device in self.__system_devices:
            if device.id == id:
                return device
        return None

    def disarm(self):
        """ Send Disarm command to the alarm system. """
        self.__api.disarm(self.__api.partition)

    def arm_home(self):
        """ Send Arm Home command to the alarm system. """
        self.__api.arm_home(self.__api.partition)

    def arm_home_instant(self):
        """ Send Arm Home Instant command to the alarm system. """
        self.__api.arm_home_instant(self.__api.partition)

    def arm_away(self):
        """ Send Arm Away command to the alarm system. """
        self.__api.arm_away(self.__api.partition)

    def arm_away_instant(self):
        """ Send Arm Away Instant command to the alarm system. """
        self.__api.arm_away_instant(self.__api.partition)

    def connect(self):
        """ Connect to the alarm system and get the static system info. """

        # Check that the server support API version 4.0.
        rest_versions = self.__api.get_version_info()['rest_versions']
        if '4.0' in rest_versions:
            print('Rest API version 4.0 is supported.')
        else:
            raise Exception('Rest API version 4.0 is not supported by server.')

        # Check that the panel ID of your device is registered with the server.
        if self.__api.get_panel_exists():
            print('Panel ID {0} is registered with the API server.'.format(
                                                        self.__api.panel_id))
        else:
            raise Exception('The Panel ID could not be found on the server. '
                            'Please check your configuration.')

        # Try to login and get a session token.
        # This will raise an exception on failure.
        self.__api.login()
        print('Login successful.')

        # Check if logged in user is a Master User.
        self.__is_master_user = self.__api.is_master_user()

        # Get general panel information
        gpi = self.__api.get_general_panel_info()
        self.__system_name = gpi['name']
        self.__system_serial = gpi['serial']
        self.__system_model = gpi['model']

        self.update_status()

    def get_last_event(self, timestamp_hour_offset=0):
        """ Get the last event. """

        events = self.__api.get_events()

        if events is None:
            return None
        else:
            last_event = events[-1]
            data = dict()

            # Event ID
            data['event_id'] = last_event['event']

            # Determine the arm state.
            if last_event['type_id'] == 89:
                data['action'] = 'Disarm'
            elif last_event['type_id'] == 85:
                data['action'] = 'ArmHome'
            elif last_event['type_id'] == 86:
                data['action'] = 'ArmAway'
            else:
                data['action'] = 'Unknown type_id: {0}'.format(
                    str(last_event['type_id']))

            # User that caused the event
            data['user'] = last_event['appointment']

            # Event timestamp
            dt = parser.parse(last_event['datetime'])
            dt = dt + relativedelta(hours=timestamp_hour_offset)
            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            data['timestamp'] = timestamp

            return data

    def print_system_information(self):
        """ Print system information. """

        print()
        print('---------------------------------')
        print(' Connection specific information ')
        print('---------------------------------')
        print('Host:          {0}'.format(self.__api.hostname))
        print('User Code:     {0}'.format(self.__api.user_code))
        print('User ID:       {0}'.format(self.__api.user_id))
        print('Panel ID:      {0}'.format(self.__api.panel_id))
        print('Partition:     {0}'.format(self.__api.partition))
        print('Session-Token: {0}'.format(self.__api.session_token))
        print()
        print('----------------------------')
        print(' General system information ')
        print('----------------------------')
        print('Name:         {0}'.format(self.__system_name))
        print('Serial:       {0}'.format(self.__system_serial))
        print('Model:        {0}'.format(self.__system_model))
        print('Ready:        {0}'.format(self.__system_ready))
        print('State:        {0}'.format(self.__system_state))
        print('Active:       {0}'.format(self.__system_active))
        print('Connected:    {0}'.format(self.__system_connected))
        print('Master User:  {0}'.format(self.__is_master_user))

    def print_system_devices(self, detailed=False):
        """ Print information about the devices in the alarm system. """

        for index, device in enumerate(self.__system_devices):
            print()
            print('--------------')
            print(' Device #{0} '.format(index+1))
            print('--------------')
            print('ID:             {0}'.format(device.id))
            print('Zone:           {0}'.format(device.zone))
            print('Location:       {0}'.format(device.location))
            print('Device Type:    {0}'.format(device.device_type))
            print('Type:           {0}'.format(device.type))
            print('Subtype:        {0}'.format(device.subtype))
            print('Alarms:         {0}'.format(device.alarms))
            print('Alerts:         {0}'.format(device.alerts))
            print('Troubles:       {0}'.format(device.troubles))
            if detailed:
                print('Pre-enroll:     {0}'.format(device.pre_enroll))
                print('Soak:           {0}'.format(device.soak))
                print('Bypass:         {0}'.format(device.bypass))
                print('Bypass Avail.:  {0}'.format(device.bypass_availability))
                print('Partitions:     {0}'.format(device.partitions))
            if isinstance(device, ContactDevice):
                print('State:          {0}'.format(device.state))

    def print_events(self):
        """ Print a list of all recent events. """

        events = self.__api.get_events()

        for index, event in enumerate(events):
            print()
            print('--------------')
            print(' Event #{0} '.format(index+1))
            print('--------------')
            print('Event:         {0}'.format(event['event']))
            print('Type ID:       {0}'.format(event['type_id']))
            print('Label:         {0}'.format(event['label']))
            print('Description:   {0}'.format(event['description']))
            print('Appointment:   {0}'.format(event['appointment']))
            print('Datetime:      {0}'.format(event['datetime']))
            print('Video:         {0}'.format(event['video']))
            print('Device Type:   {0}'.format(event['device_type']))
            print('Zone:          {0}'.format(event['zone']))
            print('Partitions:    {0}'.format(event['partitions']))

    def update_status(self):
        """ Update all variables that are populated by the call
        to the status() API method. """

        status = self.__api.get_status()
        partition = status['partitions'][0]
        self.__system_ready = partition['ready_status']
        self.__system_state = partition['state']
        self.__system_active = partition['active']
        self.__system_connected = status['is_connected']

    def update_devices(self):
        """ Update all devices in the system with fresh information. """

        devices = self.__api.get_all_devices()

        # Clear the list since there is no way to uniquely identify the devices.
        self.__system_devices.clear()

        for device in devices:
            if device['subtype'] == 'CONTACT_AUX':
                contact_device = ContactDevice(
                    id=device['device_id'],
                    zone=device['zone'],
                    location=device['location'],
                    device_type=device['device_type'],
                    type=device['type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    soak=device['soak'],
                    bypass=device['bypass'],
                    alarms=device['alarms'],
                    alerts=device['alerts'],
                    troubles=device['troubles'],
                    bypass_availability=device['bypass_availability'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(contact_device)
            elif device['subtype'] == 'MOTION_CAMERA':
                camera_device = CameraDevice(
                    id=device['device_id'],
                    zone=device['zone'],
                    location=device['location'],
                    device_type=device['device_type'],
                    type=device['type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    soak=device['soak'],
                    bypass=device['bypass'],
                    alarms=device['alarms'],
                    alerts=device['alerts'],
                    troubles=device['troubles'],
                    bypass_availability=device['bypass_availability'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(camera_device)
            elif device['subtype'] == 'SMOKE':
                smoke_device = SmokeDevice(
                    id=device['device_id'],
                    zone=device['zone'],
                    location=device['location'],
                    device_type=device['device_type'],
                    type=device['type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    soak=device['soak'],
                    bypass=device['bypass'],
                    alarms=device['alarms'],
                    alerts=device['alerts'],
                    troubles=device['troubles'],
                    bypass_availability=device['bypass_availability'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(smoke_device)
            else:
                generic_device = GenericDevice(
                    id=device['device_id'],
                    zone=device['zone'],
                    location=device['location'],
                    device_type=device['device_type'],
                    type=device['type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    soak=device['soak'],
                    bypass=device['bypass'],
                    alarms=device['alarms'],
                    alerts=device['alerts'],
                    troubles=device['troubles'],
                    bypass_availability=device['bypass_availability'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(generic_device)


class API(object):
    """ Class used for communication with the Visonic API """

    # Client configuration
    __app_type = 'com.visonic.PowerMaxApp'
    __user_agent = 'Visonic%20GO/2.8.62.91 CFNetwork/901.1 Darwin/17.6.0'
    __rest_version = '4.0'
    __hostname = 'visonic.tycomonitor.com'
    __user_code = '1234'
    __user_id = '00000000-0000-0000-0000-000000000000'
    __panel_id = '123456'
    __partition = 'ALL'

    # The Visonic API URLs used
    __url_base = None
    __url_version = None
    __url_is_panel_exists = None
    __url_login = None
    __url_status = None
    __url_alarms = None
    __url_alerts = None
    __url_troubles = None
    __url_is_master_user = None
    __url_general_panel_info = None
    __url_events = None
    __url_wakeup_sms = None
    __url_all_devices = None
    __url_arm_home = None
    __url_arm_home_instant = None
    __url_arm_away = None
    __url_arm_away_instant = None
    __url_disarm = None
    __url_locations = None
    __url_active_users_info = None
    __url_set_date_time = None
    __url_allow_switch_to_programming_mode = None

    # API session token
    __session_token = None

    # Use a session to reuse one TCP connection instead of creating a new
    # connection for every call to the API
    __session = None

    def __init__(self, hostname, user_code, user_id, panel_id, partition):
        """ Class constructor initializes all URL variables. """

        # Set connection specific details
        self.__hostname = hostname
        self.__user_code = user_code
        self.__user_id = user_id
        self.__panel_id = panel_id
        self.__partition = partition

        # Visonic API URLs that should be used
        self.__url_base = 'https://' + self.__hostname + '/rest_api/' + \
                          self.__rest_version

        self.__url_version = 'https://' + self.__hostname + '/rest_api/version'
        self.__url_is_panel_exists = self.__url_base + \
            '/is_panel_exists?panel_web_name=' + self.__panel_id
        self.__url_login = self.__url_base + '/login'
        self.__url_status = self.__url_base + '/status'
        self.__url_alarms = self.__url_base + '/alarms'
        self.__url_alerts = self.__url_base + '/alerts'
        self.__url_troubles = self.__url_base + '/troubles'
        self.__url_is_master_user = self.__url_base + '/is_master_user'
        self.__url_general_panel_info = self.__url_base + '/general_panel_info'
        self.__url_events = self.__url_base + '/events'
        self.__url_wakeup_sms = self.__url_base + '/wakeup_sms'
        self.__url_all_devices = self.__url_base + '/all_devices'
        self.__url_arm_home = self.__url_base + '/arm_home'
        self.__url_arm_home_instant = self.__url_base + '/arm_home_instant'
        self.__url_arm_away = self.__url_base + '/arm_away'
        self.__url_arm_away_instant = self.__url_base + '/arm_away_instant'
        self.__url_disarm = self.__url_base + '/disarm'
        self.__url_locations = self.__url_base + '/locations'
        self.__url_active_users_info = self.__url_base + '/active_users_info'
        self.__url_set_date_time = self.__url_base + '/set_date_time'
        self.__url_allow_switch_to_programming_mode = self.__url_base + \
            '/allow_switch_to_programming_mode'

        # Create a new session
        self.__session = requests.session()

    def __send_get_request(self, url, with_session_token):
        """ Send a GET request to the server. Includes the Session-Token
        only if with_session_token is True. """

        # Prepare the headers to be sent
        headers = {
            'Host': self.__hostname,
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': self.__user_agent,
            'Accept-Language': 'en-us',
            'Accept-Encoding': 'br, gzip, deflate'
        }

        # Include the session token in the header
        if with_session_token:
            headers['Session-Token'] = self.__session_token

        # Perform the request and raise an exception
        # if the response is not OK (HTML 200)
        response = self.__session.get(url, headers=headers)
        response.raise_for_status()

        if response.status_code == requests.codes.ok:
            value = json.loads(response.content.decode('utf-8'))
            return value

    def __send_post_request(self, url, data_json, with_session_token):
        """ Send a POST request to the server. Includes the Session-Token
        only if with_session_token is True. """

        # Prepare the headers to be sent
        headers = {
            'Host': self.__hostname,
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': self.__user_agent,
            'Content-Length': str(len(data_json)),
            'Accept-Language': 'en-us',
            'Accept-Encoding': 'br, gzip, deflate'
        }

        # Include the session token in the header
        if with_session_token:
            headers['Session-Token'] = self.__session_token

        # Perform the request and raise an exception
        # if the response is not OK (HTML 200)
        response = self.__session.post(url, headers=headers, data=data_json)
        response.raise_for_status()

        # Check HTTP response code
        if response.status_code == requests.codes.ok:
            return json.loads(response.content.decode('utf-8'))
        else:
            return None

    ######################
    # Public API methods #
    ######################

    @property
    def session_token(self):
        """ Property to keep track of the session token. """
        return self.__session_token

    @property
    def hostname(self):
        """ Property to keep track of the API servers hostname. """
        return self.__hostname

    @property
    def user_code(self):
        """ Property to keep track of the user code beeing used. """
        return self.__user_code

    @property
    def user_id(self):
        """ Property to keep track of the user id (UUID) beeing used. """
        return self.__user_id

    @property
    def panel_id(self):
        """ Property to keep track of the panel id (panel web name). """
        return self.__panel_id

    @property
    def partition(self):
        """ Property to keep track of the partition. """
        return self.__partition

    def get_version_info(self):
        """ Find out which REST API versions are supported. """
        return self.__send_get_request(self.__url_version,
                                       with_session_token=False)

    def get_panel_exists(self):
        """ Check if our panel exists on the server. """
        return self.__send_get_request(self.__url_is_panel_exists,
                                       with_session_token=False)

    def login(self):
        """ Try to login and get a session token. """
        # Setup authentication information
        login_info = {
            'user_code': self.__user_code,
            'app_type': self.__app_type,
            'user_id': self.__user_id,
            'panel_web_name': self.__panel_id
        }

        login_json = json.dumps(login_info, separators=(',', ':'))
        res = self.__send_post_request(self.__url_login, login_json,
                                       with_session_token=False)
        self.__session_token = res['session_token']

    def is_logged_in(self):
        """ Check if the session token is still valid. """
        try:
            self.get_status()
            return True
        except requests.HTTPError:
            return False

    def get_status(self):
        """ Get the current status of the alarm system. """
        return self.__send_get_request(self.__url_status,
                                       with_session_token=True)

    def get_alarms(self):
        """ Get the current alarms. """
        return self.__send_get_request(self.__url_alarms,
                                       with_session_token=True)

    def get_alerts(self):
        """ Get the current alerts. """
        return self.__send_get_request(self.__url_alerts,
                                       with_session_token=True)

    def get_troubles(self):
        """ Get the current troubles. """
        return self.__send_get_request(self.__url_troubles,
                                       with_session_token=True)

    def is_master_user(self):
        """ Check if the current user is a master user. """
        ret = self.__send_get_request(self.__url_is_master_user,
                                      with_session_token=True)
        return ret['is_master_user']

    def get_general_panel_info(self):
        """ Get the general panel information. """
        return self.__send_get_request(self.__url_general_panel_info,
                                       with_session_token=True)

    def get_events(self):
        """ Get the alarm panel events. """
        return self.__send_get_request(self.__url_events,
                                       with_session_token=True)

    def get_wakeup_sms(self):
        """ Get the information needed to send a
        wakeup SMS to the alarm system. """
        return self.__send_get_request(self.__url_wakeup_sms,
                                       with_session_token=True)

    def get_all_devices(self):
        """ Get the device specific information. """
        return self.__send_get_request(self.__url_all_devices,
                                       with_session_token=True)

    def get_locations(self):
        """ Get all locations in the alarm system. """
        return self.__send_get_request(self.__url_locations,
                                       with_session_token=True)

    def get_active_user_info(self):
        """ Get information about the active users.
        Note: Only master users can see the active_user_ids! """
        return self.__send_get_request(self.__url_active_users_info,
                                       with_session_token=True)

    def set_date_time(self):
        """ Set the time on the alarm panel.
        Note: Only master users can set the time! """

        # Make sure the time has the correct format: 20180704T185700
        current_time = datetime.now().isoformat().replace(':', '').replace('.',
                                                    '').replace('-', '')[:15]

        time_info = {'time': current_time}
        time_json = json.dumps(time_info, separators=(',', ':'))
        return self.__send_post_request(self.__url_set_date_time, time_json,
                                        with_session_token=True)

    def arm_home(self, partition):
        """ Arm in Home mode and with Exit Delay. """
        arm_info = {'partition': partition}
        arm_json = json.dumps(arm_info, separators=(',', ':'))
        return self.__send_post_request(self.__url_arm_home, arm_json,
                                        with_session_token=True)

    def arm_home_instant(self, partition):
        """ Arm in Home mode instantly (without Exit Delay). """
        arm_info = {'partition': partition}
        arm_json = json.dumps(arm_info, separators=(',', ':'))
        return self.__send_post_request(self.__url_arm_home_instant, arm_json,
                                        with_session_token=True)

    def arm_away(self, partition):
        """ Arm in Away mode and with Exit Delay. """
        arm_info = {'partition': partition}
        arm_json = json.dumps(arm_info, separators=(',', ':'))
        return self.__send_post_request(self.__url_arm_away, arm_json,
                                        with_session_token=True)

    def arm_away_instant(self, partition):
        """ Arm in Away mode instantly (without Exit Delay). """
        arm_info = {'partition': partition}
        arm_json = json.dumps(arm_info, separators=(',', ':'))
        return self.__send_post_request(self.__url_arm_away_instant, arm_json,
                                        with_session_token=True)

    def disarm(self, partition):
        """ Disarm the alarm system. """
        disarm_info = {'partition': partition}
        disarm_json = json.dumps(disarm_info, separators=(',', ':'))
        return self.__send_post_request(self.__url_disarm, disarm_json,
                                        with_session_token=True)
