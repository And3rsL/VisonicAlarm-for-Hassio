[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
<br><a href="https://www.buymeacoffee.com/4nd3rs" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-black.png" width="150px" height="35px" alt="Buy Me A Coffee" style="height: 35px !important;width: 150px !important;" ></a>

## Visonic/Bentel/Tyco Alarm Sensor
This component interfaces with the API server hosted by your home alarm system company.

It is dependant on the Python module: https://github.com/And3rsL/VisonicAlarm2 which will automatically be installed when running the sensor component. This library has much more functionality than this component utilises, so feel free to check it out of you are into Python 3 programming.

This is unsupported by Visonic - they don't publish their REST API. It is also unsupported by me. I accept no liability for your use of the component or library nor for any loss or damage resulting from security breaches at your property.

### Introduction
This component will create one **alarm_control_panel** that let you show the current state of the alarm system and also to arm and disarm the system. It will also create one **sensor** for every door/window contact that let you see if the doors or windows are open or closed.

The Alarm Control Panel will be called **alarm_control_panel.visonic_alarm** and the contact sensors will be called **sensor.visonic_alarm_contact_ID** (where ID is the contact ID in the alarm system).

It polls the API server every 10 seconds, which is the same interval as the app does its updates. So there is up to a 10 second delay between updates.

### Requirements
The component has only been tested with a Visonic PowerMaster 10 with a PowerLink 3 ethernet module, so it might not work with (but should) other Visonic alarm systems.

### Configuration
Now to the configuration of Home Assistant.

Open the configuration file (`configuration.yaml`) and use the following code:
```yaml
visonicalarm:
  host: YOURALARMCOMPANY.tycomonitor.com
  panel_id: 123456
  user_code: 1234
  app_id: 00000000-0000-0000-0000-000000000000
  user_email: 'example@email.com'
  user_password: 'yourpassword'
  partition: -1
  no_pin_required: False
```

The **host**, **user_code**, **panel_id**, **user_email**, **user_password** are the same you are using when logging in to your system via the Visonic-GO/BW app,
and **app_id** is just a uniqe id generated from this site: https://www.uuidgenerator.net/ so make sure you replace 00000000-0000-0000-0000-000000000000 with an ID that you generate with that site. There is only support for the -1 partition.

Please be sure that the user is the MASTER USER and you alredy added your panel in your registered account

### Screenshots ###
![Alarm Panel dialog](https://github.com/And3rsL/VisonicAlarm-for-Hassio/blob/master/HomeAssistantArmDialog2.png)
