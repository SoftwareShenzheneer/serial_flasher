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

VERBOSE = False
TEST_CASES = True

SERIAL_ID_BYTE = 15
SERIAL_ID_VERIFICATION_IDX = 9

PARSING_TIMEOUT = 5

sercom1 = None # Serial connection with master controller
sercom2 = None # Serial connection with flashing target

introduce_error = 0

# Configure your master controller settings here
MASTER_PORT = "COM11"
# Configure your target settings here
TARGET_PORT = "COM18"
TARGET_CHIP = "esp32s3"
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
        '0x1C000', 'unique_binary.bin',
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
        # '0x1000', 'my_pseudo_firmware/build/bootloader/bootloader.bin',
        '0x0', 'my_pseudo_firmware/build/bootloader/bootloader.bin',
        '0x8000', 'my_pseudo_firmware/build/partition_table/partition-table.bin',
        '0x10000', 'my_pseudo_firmware/build/my_pseudo_firmware.bin'
        ]

verification_command = [
        'esptool',
        '-p', TARGET_PORT,
        '--chip', TARGET_CHIP,
        'verify_flash',
        '--diff', 'yes',
        '0x1C000', 'unique_binary.bin'
        ]

check_encryption_command = [
        'esptool',
        '-p', TARGET_PORT,
        'get_security_info'
        ]

# Some debugging commands to verify the flashing commands - can also be used to generate a single command for manual flashing
# serial_command[15] = "unique_bin/example.bin"
# print(f"[DEBUG] ", end="")
# for i in range(16):
#     print(f"{serial_command[i]} ", end="")
# print("")
# print(f"[DEBUG] ", end="")
# for i in range(20):
#     print(f"{application_command[i]} ", end="")
# print("")
# print(f"[DEBUG] ", end="")
# for i in range(10):
#     print(f"{verification_command[i]} ", end="")
# print("")

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
        if mode == "FLASH_NOK":
            print(f"[STATE] FLASH_NOK")
            sercom1.write(b'3')
        if mode == "FLASH_RETRY":
            print(f"[STATE] FLASH_RETRY")
            sercom1.write(b'4')
        if mode == "FLASH_OK":
            # Choose not to print it here because it will bloat the terminal and this is the easiest solution
            # print(f"[STATE] FLASH_OK")
            sercom1.write(b'5')
        # Small delay to let the device settle - 100ms is fine
        time.sleep(0.1)

def flash_target(stage=None):
    print(f"[FLASH] Flashing target.")
    # We will use the same serial port for parsing and flashing, so to close it before flashing
    global sercom2
    close_serial(sercom2)
    if stage == "UNIQUE_BIN":
        print(f"[FLASH] Unique bin")
        try:
            if VERBOSE:
                subprocess.Popen(serial_command, shell=True).wait()
            else:
                subprocess.Popen(serial_command, stdout=subprocess.DEVNULL, shell=True).wait()
        except Exception as e:
            print(f"[DEBUG] [ERROR] Error with running subprocess.")

    if stage == "APPLICATION":
        print(f"[FLASH] Application")
        try:
            if VERBOSE:
                subprocess.Popen(application_command,  shell=True).wait()
            else:
                subprocess.Popen(application_command, stdout=subprocess.DEVNULL, shell=True).wait()
        except Exception as e:
            print(f"[DEBUG] [ERROR] Error with running subprocess.")

    print(f"[FLASH] Flashing target done - This does not say anything about succesful flashing.")
    # After flashing is completed, open up the serial port again to make it available for parsing
    sercom2 = open_serial(TARGET_PORT)

def verify_unique_binary():
    print(f"[FLASH] Verifying unique binary.")
    ret = 1
    global unique_binary_list_index
    global sercom2
    close_serial(sercom2)
    global introduce_error
    introduce_error = introduce_error + 1

    try:
        # verification_command[SERIAL_ID_VERIFICATION_IDX] = str(unique_binary_list[unique_binary_list_index])
        # verification_command[SERIAL_ID_VERIFICATION_IDX] = "unique_bin/04E3E1BD-FE70-40E7-A8FD-85D8ADE979C9.bin"
        if TEST_CASES:
            if introduce_error == 2:
                print(f"\r\n############################ introducing an error! ############################")
                verification_command[SERIAL_ID_VERIFICATION_IDX] = "new_unique_bin/050415dc-5764-4f57-bb42-daae7324d8fc.bin"
            elif introduce_error == 3:
                print(f"\r\n############################ introducing an error! ############################")
                verification_command[SERIAL_ID_VERIFICATION_IDX] = "new_unique_bin/050415dc-5764-4f57-bb42-daae7324d8fc.bin"
            elif introduce_error == 4:
                print(f"\r\n############################ introducing an error! ############################")
                verification_command[SERIAL_ID_VERIFICATION_IDX] = "new_unique_bin/050415dc-5764-4f57-bb42-daae7324d8fc.bin"
            else:
                verification_command[SERIAL_ID_VERIFICATION_IDX] = str(unique_binary_list[unique_binary_list_index])
        else:
            verification_command[SERIAL_ID_VERIFICATION_IDX] = str(unique_binary_list[unique_binary_list_index])

        unique_binary_list_index = unique_binary_list_index + 1
        out = subprocess.check_output(verification_command, encoding='utf-8')
        if out.find("-- verify OK") > 0:
            print("[VERIFICATION] Verification success")
            ret = 0
        else:
            print("[VERIFICATION] Verification failed, but I don't know why")
    except Exception as e:
        print("[VERIFICATION] Verification failed")
        # print("[VERIFICATION] Error: ", str(e))

    return ret

def verify_encryption():
    print(f"[VERIFICATION] Verifying flash encryption")
    ret = -1
    try:
        global sercom2
        close_serial(sercom2)
        out = subprocess.check_output(check_encryption_command, encoding='utf-8')
        if out.find("Flash Encryption: Enabled") > 0:
            if out.find("Secure Boot: Enabled") > 0:
                # print(f"[VERIFICATION] Flash encryption enabled.")
                ret = 1

        if out.find("Flash Encryption: Disabled") > 0:
            if out.find("Secure Boot: Disabled") > 0:
                # print(f"[VERIFICATION] Flash encryption disabled.")
                ret = 0
    except Exception as e:
        print(f"Error: {e}.")

    sercom2 = open_serial(TARGET_PORT)
    return ret


if __name__ == "__main__":
    state = "FETCH_UNIQUE_BIN"
    uuid_index = 0
    unique_binary_list = []
    unique_binary_list_index = 0
    count = 0
    max_tries = 3
    flash_ok_set = False

    # Generate the list of unique binaries to flash
    with open('unique_bin.txt', 'r+') as inp:
        for num, line in enumerate(inp):
            # Strip the new line, read the binary name and add .bin to its name
            unique_binary_list.append("new_unique_bin/" + line.strip() + ".bin")
            # print(f"[DEBUG] ",unique_binary_list[num])

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

    while True:
        # 1. Prepare the flashing commands
        if state == "FETCH_UNIQUE_BIN":
            print(f"[STATEMACHINE] FETCH_UNIQUE_BIN")
            flash_ok_set = False
            set_target_mode("FLASH_RETRY")
            # Catch the last unique binary and break the loop
            if unique_binary_list_index == len(unique_binary_list):
                print(f"[STATEMACHINE] No more binaries available, exiting..")
                break
            serial_command[SERIAL_ID_BYTE] = str(unique_binary_list[unique_binary_list_index])
            print(f"#######################################################")
            print(f"{serial_command[SERIAL_ID_BYTE]}")
            print(f"#######################################################")
            state = "FORCE_BOOT"

        # 2. Send serial command to mastercontroller to enable BOOT mode
        if state == "FORCE_BOOT":
            print(f"[STATEMACHINE] FORCE_BOOT")
            set_target_mode("BOOT")
            state = "FLASH_UNIQUE_BIN"

        # 3. Flash unique binary to target
        if state == "FLASH_UNIQUE_BIN":
            print(f"[STATEMACHINE] FLASH_UNIQUE_BIN")
            flash_target("UNIQUE_BIN")
            state = "VERIFY_UNIQUE_BIN"

        # 4. Verify the unique binary has been properly flashed
        if state == "VERIFY_UNIQUE_BIN":
            print(f"[STATEMACHINE] VERIFY_UNIQUE_BIN")
            set_target_mode("RESET")
            set_target_mode("BOOT")
            if verify_unique_binary() == 1:
                print("[UNIQUE_BIN] Unique binary identification failed, retry flashing..")
                state = "FETCH_UNIQUE_BIN"
                max_tries = max_tries - 1
                # We are retrying the previous unique binary so we need to undo the unique binary increment
                unique_binary_list_index = unique_binary_list_index - 1
                print(f"[UNIQUE_BIN] Attempts left: {max_tries}.")
                if 0 == max_tries:
                    print(f"[UNIQUE_BIN] Aborting...")
                    # Turn on the RED LED, wait for user input and move on to a next unit. Upon pressing enter, set LED RED off
                    set_target_mode("FLASH_NOK")
                    state = "FETCH_UNIQUE_BIN"
                else:
                    ########## DESIGN CHOICE: Do we ditch the failed UUID, or do we retry? #########
                    # state = "FETCH_UNIQUE_BIN"
                    state = "FORCE_BOOT"
                    ########## DESIGN CHOICE: Do we ditch the failed UUID, or do we retry? #########
            else:
                state = "FLASH_APPLICATION"

        # 5. Flash the APPLICATION
        if state == "FLASH_APPLICATION":
            print(f"[STATEMACHINE] FLASH_APPLICATION")
            set_target_mode("RESET")
            set_target_mode("BOOT")
            flash_target("APPLICATION")
            set_target_mode("RESET")
            state = "PARSE_OUTPUT"

        # 6. Parse incoming data and look for expected debug tags
        #    [PROD][OK] & [PROD][NO_SERIAL_ID]
        if state == "PARSE_OUTPUT":
            print(f"[STATEMACHINE] PARSE_OUTPUT")
            max_num_of_lines = 0
            start_time = time.time()
            set_target_mode("RESET")
            seconds = 0
            while (time.time() - start_time < PARSING_TIMEOUT):
                if sercom2 and sercom2.is_open:
                    data = sercom2.readline()
                    print(f"Seconds: {seconds}", end="\r")
                    seconds = seconds + 1
                    if data:
                        try:
                            line = data.decode('utf-8').strip()
                            print(line, flush=True)
                            if flash_ok_set == False:
                                flash_ok_set = True
                                set_target_mode("FLASH_OK");
                                if "[PROD][OK]" in line:
                                    set_target_mode("FLASH_OK");
                        except:
                            print(data)

                # print(f"Breaker is: {max_num_of_lines}.")
                max_num_of_lines = max_num_of_lines + 1
                if max_num_of_lines == 400:
                    print(f"[PARSER] We've gotten too many lines fed, breaking..")
                    break
            state = "FETCH_UNIQUE_BIN"

        if "FETCH_UNIQUE_BIN" == state:
            # Enter a wait state for the next target to be connected
            max_tries = 3
            input("Press enter to continue...\n")
        else:
            pass

