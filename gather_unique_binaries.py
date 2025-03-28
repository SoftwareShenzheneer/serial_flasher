import os

directory = 'new_serial_ids'

with open("unique_binaries.txt", "w+") as outp:
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        outp.write(filename + "\r\n")

