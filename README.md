# Power Monitoring with NCurses
Visually monitors the power of a Power Supply that can be controlled with pyvisa and connected via USB
It can control ON/OFF of the respective channels by pressing a respective number on a keyboard
![grafik](https://github.com/user-attachments/assets/10fd924b-c5e2-4078-a77c-be3c2c18b0de)

## Currently supports:
- GW Insteak GPP-4323
- Keithley-2230-30-1

## Installation:
1. clone the repo
2. Create a virtual environment ```python3 -m venv venv```
3. activate the virtual enviroment ```source venv/bin/activate```
4. install pyvisa ```pip install -U pyvisa```
5. check with ```pyvisa-shell``` and type ```list``` to see if your device is there
6. If it's there, update the ```USB_PORT``` variable in the respective python file. If not, go troubleshooting your USB connection :-)

## Configuration
1. you can change the names of the Channels for better recognitions in the variable ```names``` in the respective python file
2. You can control if a channel can be toggled on/off with the ```toggle_allowed``` variable


## USB Troubleshooting
### Keithley-2230-30-1 
You will likely need to edit /etc/udev/rules.d/99-garmin.rules as root, adding this line:

```UBSYSTEM=="usb", ATTR{idVendor}=="VVVV", ATTR{idProduct}=="PPPP", MODE="666"```

where VVVV and PPPP are the vendor and product id, and can be found by running

`lsusb`

which yeilds this output:

`  Bus 001 Device 067: ID VVVV:PPPP Keithley Instruments`

Once the file has been edited, restart udev with:

`sudo udevadm trigger`
