####################################################################################################
# Note:                                                                                            #
# In the original implementation an esp32 has been used as a master controller. For this reason,   #
# the baudrate of 115200 baud is very reasonable. When using a slower/weaker microcontroller,      #
# consider lowering the baudrate if error occur with the serial communication.                     #
####################################################################################################

import serial
import subprocess
import sys
import time

SERIAL_ID_BYTE = 15

sercom1 = None # Serial connection with master controller
sercom2 = None # Serial connection with flashing target

# Configure your master controller settings here
MASTER_PORT = "COM4"
# Configure your target settings here
TARGET_PORT = "COM18"
TARGET_CHIP = "esp32"
TARGET_BAUDRATE = "460800"
TARGET_FLASH_SIZE = "16MB"
serial_command = [
        'esptool',
        '-p', TARGET_PORT,
        '--chip', TARGET_CHIP,
        '-b', TARGET_BAUDRATE,
        'write_flash',
        '--flash_mode', 'dio',
        '--flash_size', TARGET_FLASH_SIZE,
        '--flash_freq', '40m',
        '0x1000', 'my_pseudo_firmware/build/bootloader/UUID.bin',
        ]

application_command = [
        'esptool',
        '-p', TARGET_PORT,
        '--chip', TARGET_CHIP,
        '-b', TARGET_BAUDRATE,
        'write_flash',
        '--flash_mode', 'dio',
        '--flash_size', TARGET_FLASH_SIZE,
        '--flash_freq', '40m',
        '0x1000', 'my_pseudo_firmware/build/bootloader/bootloader.bin',
        '0x8000', 'my_pseudo_firmware/build/partition_table/partition-table.bin',
        '0x10000', 'my_pseudo_firmware/build/my_pseudo_firmware.bin'
        ]

# Some debugging commands to verify the flashing commands - can also be used to generate a single command for manual flashing
# serial_command[15] = "New_UUID_here.bin"
# print(f"[DEBUG] ", end="")
# for i in range(16):
#     print(f"{serial_command[i]} ", end="")
# print("")
# print(f"[DEBUG] ", end="")
# for i in range(20):
#     print(f"{application_command[i]} ", end="")

# Pass a serial PORT to open a connection
def open_serial(port=None):
    print(f"[SERIAL] Opening serial {port}.")
    ser = serial.Serial(port, baudrate=115200, timeout=1)
    return ser

# Pass a serial handle to close the serial connection
def close_serial(ser=None):
    print(f"[SERIAL] Closing serial {ser.port}.")
    ser.close()

# Write byte to master controller to force boot mode or reset mode
def set_target_mode(mode=None):
    if sercom1 and sercom1.is_open:
        if mode == "BOOT":
            print(f"[STATE] BOOT")
            sercom1.write(b'1')
        if mode == "RESET":
            print(f"[STATE] RESET")
            sercom1.write(b'2')

def flash_target(stage=None):
    print(f"[FLASH] Flashing target.")
    # We will use the same serial port for parsing and flashing, so to close it before flashing
    global sercom2
    close_serial(sercom2)
    if stage == "UNIQUE_BIN":
        print(f"[FLASH] Unique bin")
        subprocess.Popen(serial_command, shell=True).wait()
    if stage == "APPLICATION":
        print(f"[FLASH] Application")
        subprocess.Popen(application_command, shell=True).wait()

    print(f"")
    print(f"[FLASH] Flashing target done - This does not say anything about succesful flashing.")

    # After flashing is completed, open up the serial port again to make it available for parsing
    sercom2 = open_serial(TARGET_PORT)

if __name__ == "__main__":
    state = "FETCH_UNIQUE_BIN"
    uuid_index = 0
    unique_binary_list = []
    unique_binary_list_index = 0
    count = 0

    # Generate the list of unique binaries to flash
    with open('unique_bin.txt', 'r+') as inp:
        for num, line in enumerate(inp):
            # Strip the new line, read the binary name and add .bin to its name
            unique_binary_list.append("unique_bin/" + line.strip() + ".bin")
            # print(unique_binary_list[num])

    for i in range (len(unique_binary_list)):
        serial_command[SERIAL_ID_BYTE] = unique_binary_list[unique_binary_list_index]
        unique_binary_list_index = unique_binary_list_index + 1
        # Quick debug line to check if the list is correctly generated; 
        # print(f"[DEBUG] {unique_binary_list[i]}")

    # Make sure to reset this one before continueing flashing; we want to start at the beginning
    unique_binary_list_index = 0
        
    # We're all set from here and ready to focus on the actual flashing process
    sercom1 = open_serial(MASTER_PORT)
    sercom2 = open_serial(TARGET_PORT)

    # while False:
    while True:
        # 1. Prepare the flashing commands
        if state == "FETCH_UNIQUE_BIN":
            # print(f"[STATEMACHINE] FETCH_UNIQUE_BIN")
            serial_command[SERIAL_ID_BYTE] = str(unique_binary_list[unique_binary_list_index])
            print(f"###################################################")
            print(f"{serial_command[SERIAL_ID_BYTE]}")
            print(f"###################################################")
            unique_binary_list_index = unique_binary_list_index + 1
            # Catch the last unique binary and break the loop
            if unique_binary_list_index == len(unique_binary_list):
                break
            state = "FORCE_BOOT"

        # 2. Send serial command to mastercontroller to enable BOOT mode
        if state == "FORCE_BOOT":
            # print(f"[STATEMACHINE] FORCE_BOOT")
            set_target_mode("BOOT")
            state = "FLASH_UNIQUE_BIN"

        # 3. Flash unique binary to target
        if state == "FLASH_UNIQUE_BIN":
            # print(f"[STATEMACHINE] FLASH_UNIQUE_BIN")
            flash_target("UNIQUE_BIN")
            state = "VERIFY_UNIQUE_BIN"

        # 4. Verify the unique binary has been properly flashed
        if state == "VERIFY_UNIQUE_BIN":
            # print(f"[STATEMACHINE] VERIFY_UNIQUE_BIN")
            state = "FLASH_APPLICATION"

        # 5. Flash the APPLICATION
        if state == "FLASH_APPLICATION":
            # print(f"[STATEMACHINE] FLASH_APPLICATION")
            set_target_mode("RESET")
            set_target_mode("BOOT")
            flash_target("APPLICATION")
            # set_target_mode("RESET")
            state = "PARSE_OUTPUT"

        # 6. Parse incoming data and look for expected debug tags
        #    [PROD][OK] & [PROD][NO_SERIAL_ID]
        if state == "PARSE_OUTPUT":
            max_num_of_lines = 0
            start_time = time.time()
            # print(f"[STATEMACHINE] PARSE_OUTPUT")
            set_target_mode("RESET")
            while (time.time() - start_time < 10):
                if sercom2 and sercom2.is_open:
                    data = sercom2.readline()
                    if data:
                        line = data.decode('utf-8').strip()
                        print(line)
                # print(f"Breaker is: {max_num_of_lines}.")
                max_num_of_lines = max_num_of_lines + 1
                if max_num_of_lines == 200:
                    print(f"We've gotten too many lines fed, breaking..")
                    break
            state = "FETCH_UNIQUE_BIN"

        # Enter a wait state for the next target to be connected
        input("Press enter to continue...")

