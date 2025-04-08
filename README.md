# serial_flasher
Solution to flash devices with individually unique binaries (like UUIDs).
___

## Table of contents
- [Project description](#project-description)
- [Install](#install)
- [Use](#use)
___

## Project Description
The goal of this project is to solve the tedious issue of flashing a lot of devices with individual binary files. The need for this surfaced when I wanted to flash individual UUID's to devices.
This issue is solved by assigning a mastercontroller which controls the boot state of the target device. The current implementation covers a BOOT and RESET mode. This can be built upon to realise any arbitrary number of production states. Currently the master controller also controls the feedback LEDs upon flashing completion, whether that is successful, ongoing or failed.

___

## Install
### Git clone this repository.
```
git clone https://github.com/SoftwareShenzheneer/serial_flasher.git
```
___
### Ensure Python is installed. Version tested is: Python v3.11.2
```
python --version
```
Else download Python from their official website.
___
### Depending on what platform is used, ensure flashing tools are present. In this case, esptool for esp32:
```
pip show esptool
```
My configuration currently uses esptool v4.7.0.
Else download pip using the following command:
```
pip install esptool
```
___

## Prerequisites
The script starts off with gathering a list of unique binaries from the unique binary directory. Up to a size of 1050 has been tested. Providing the unique binaries is required for the script to generate and iterate this list. Do not forget to adjust the serial ports to the actual ports used in your personal case.

## Use
Either put the files which need to be downloaded in the file path as stated in the script, or adjust the file path to point to the location of your binaries.
Make sure the serial ports are configured accordingly. If you use different ports for the mastercontroller or target device, make sure to change these in the script.

Since it may be possible that different targets provide you with different serial ports, this may be an inconvenience. In my setup this is not the case and thus the solution to it is not in this repository. If I feel like it, I might add this in the future.

In this specific example, the target binary that is consistently flashed to all devices is place in my_psuedo_firmware and all unique binaries are stored in unique_bin.

Finally, this repository contains an Arduino project for the mastercontroller. This platform has been chosen so it's easy for anyone who reads this to modify and use for different microcontroller families.

Feel free to copy and adjust this script to your needs.

