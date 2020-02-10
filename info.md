# Home Assistant Development
Based on https://github.com/CrientClash/homeassistant

## Visonic Alarm Sensor
This component interfaces with the API server hosted by your home alarm system company.

It is dependant on the Python module: https://github.com/And3rsL/VisonicAlarm2 which will automatically be installed when running the sensor component. This library has much more functionality than this component utilises, so feel free to check it out of you are into Python 3 programming.

This is unsupported by Visonic - they don't publish their REST API. It is also unsupported by me. I accept no liability for your use of the component or library nor for any loss or damage resulting from security breaches at your property.

### Introduction
This component will create one **alarm_control_panel** that let you show the current state of the alarm system and also to arm and disarm the system. It will also create one **sensor** for every door/window contact that let you see if the doors or windows are open or closed.

It has been reverse engineered by sniffing the traffic sent to and from the Visonic-GO app on an Apple iPhone. I used the application **Fiddler 4** to proxy the HTTPS traffic via a Windows machine to intercept the REST API calls.

The Alarm Control Panel will be called **alarm_control_panel.visonic_alarm** and the contact sensors will be called **sensor.visonic_alarm_contact_1001001** (where 1001001 is the contact ID in the alarm system).

It polls the API server every 10 seconds, which is the same interval as the app does its updates. So there is up to a 10 second delay between updates.

### Requirements
The component has only been tested with a Visonic PowerMaster 10 with a PowerLink 3 ethernet module, so it might not work with (but should) other Visonic alarm systems.

### Configuration
Now to the configuration of Home Assistant.

Open the configuration file (`configuration.yaml`) and use the following code:
```yaml
visonicalarm:
  host: host.alarmcompany.com
  user_code: 1234
  user_id: 00000000-0000-0000-0000-000000000000
  panel_id: 123456
  partition: ALL
```

The **host**, **user_code** and **panel_id** are the same you are using when logging in to your system via the Visonic-GO app,
and **user_id** is just a uniqe id generated from this site: https://www.uuidgenerator.net/ so make sure you replace 00000000-0000-0000-0000-000000000000 with an ID that you generate with that site. There is only support for the ALL partition.

### Screenshots ###
![Alarm Panel dialog](https://github.com/And3rsL/VisonicAlarm-for-Hassio/blob/master/HomeAssistantArmDialog2.png)
