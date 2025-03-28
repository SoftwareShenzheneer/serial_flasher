import os

directory = "new_unique_bin"

with open("unique_bin.txt", "w+") as outp:
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        outp.write(filename + "\r\n")

