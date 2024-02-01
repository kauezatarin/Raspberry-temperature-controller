# Raspberry temperature controller
This script is to help you to control your raspberry pi temperature.

## Change Logs

### Version 1.0:

-first release
-supports auto install and auto init
-supports command line options
-supports temperature operation range

### Version 1.5:

-added configuration file
-added command to generate a default config file template

### Version 1.6:

-added thingspeak integration to send raspberry temperature infos.
-added thingspeak configurations to config file.
-added reaload config command to remove the need to reboot the system to make config file changes to take effect.

### Version 1.6.5:

-added installer bash script to install tempController script.
-prepared the code to be compatible with NPN and Reley fan activation mode.

### Version 1.7:

-added fullstat option that displays all collected system infos.
-added option to choose between transistor and relay fan activation mode.

### version 1.7.5:

-added the option to get the temperature directly fom the raspberry pi soc.

### version 1.8:

-migrated the script to python 3.7

### version 1.9:

-added the option to mantain the fan always on via config file