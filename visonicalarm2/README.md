# Visonic Alarm Library
Based on https://github.com/CrientClash/visonicalarm

## Information
A simple library for the Visonic PowerMaster API written in Python 3. It is only tested with a PowerMaster-10 using a PowerLink 3 IP module. The PowerLink 3 is a requirement for this library to work.

## Installation
Install with pip3
```
$ sudo pip3 install visonicalarm2
```

## Code examples
### Current status
Getting the current alarm status. Available states are 'armed_away', 'armed_home', 'arming_exit_delay_away', 'arming_exit_delay_home' or 'disarmed'.
```python
#!/usr/bin/env python3
from visonic import alarm

hostname  = 'visonic.tycomonitor.com'
user_code = '1234'
user_id   = '2d978962-daa6-4e18-a5e5-b4a99100bd3b'
panel_id  = '123456'
partition = 'P1'

api = alarm.API(hostname, user_code, user_id, panel_id, partition)

res = api.login()

if api.is_logged_in():
    print('Logged in')
else:
    print('Not logged in')

print(api.get_status())
```
Example output:
```
{
   'is_connected': True,
   'exit_delay': 30,
   'partitions': [
      {
         'partition': 'ALL',
         'active': True,
         'state': 'Disarm',
         'ready_status': True
      }
   ]
}
```
