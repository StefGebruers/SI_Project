import requests
import random
import time

import serial
import sys
import crcmod.predefined
import re
from tabulate import tabulate
import os

# Create clear function to clear the terminal
clear = lambda: os.system('clear')

# Change your serial port here:
serialport = '/dev/ttyUSB0'

# Enable debug if needed:
debug = False

# Add/update OBIS codes here:
obiscodes = {
    "1-0:21.7.0": "L1 consumption",
    "1-0:22.7.0": "L1 production",
    }


def checkcrc(p1telegram):
    # check CRC16 checksum of telegram and return False if not matching
    # split telegram in contents and CRC16 checksum (format:contents!crc)
    for match in re.compile(b'\r\n(?=!)').finditer(p1telegram):
        p1contents = p1telegram[:match.end() + 1]
        # CRC is in hex, so we need to make sure the format is correct
        givencrc = hex(int(p1telegram[match.end() + 1:].decode('ascii').strip(), 16))
    # calculate checksum of the contents
    calccrc = hex(crcmod.predefined.mkPredefinedCrcFun('crc16')(p1contents))
    # check if given and calculated match
    if debug:
        print(f"Given checksum: {givencrc}, Calculated checksum: {calccrc}")
    if givencrc != calccrc:
        if debug:
            print("Checksum incorrect, skipping...")
        return False
    return True


def parsetelegramline(p1line):
    # parse a single line of the telegram and try to get relevant data from it
    unit = ""
    timestamp = ""
    if debug:
        print(f"Parsing:{p1line}")
    # get OBIS code from line (format:OBIS(value)
    obis = p1line.split("(")[0]
    if debug:
        print(f"OBIS:{obis}")
    # check if OBIS code is something we know and parse it
    if obis in obiscodes:
        # get values from line.
        # format:OBIS(value), gas: OBIS(timestamp)(value)
        values = re.findall(r'\(.*?\)', p1line)
        value = values[0][1:-1]
        # separate value and unit (format:value*unit)
        lvalue = value.split("*")
        value = float(lvalue[0])
        if len(lvalue) > 1:
            unit = lvalue[1]
        # return result in tuple: description,value,unit,timestamp
        if debug:
            print (f"description:{obiscodes[obis]}, \
                     value:{value}, \
                     unit:{unit}")
        return (obiscodes[obis], value, unit)
    else:
        return ()


def main():
    ser = serial.Serial(serialport, 115200, xonxoff=1)
    p1telegram = bytearray()
    while True:
        try:
            # read input from serial port
            p1line = ser.readline()
            if debug:
                print ("Reading: ", p1line.strip())
            # P1 telegram starts with /
            # We need to create a new empty telegram
            if "/" in p1line.decode('ascii'):
                if debug:
                    print ("Found beginning of P1 telegram")
                p1telegram = bytearray()
                #print('*' * 60 + "\n")
                clear()
                
            # add line to complete telegram
            p1telegram.extend(p1line)
            # P1 telegram ends with ! + CRC16 checksum
            if "!" in p1line.decode('ascii'):
                if debug:
                    print("Found end, printing full telegram")
                    print('*' * 40)
                    print(p1telegram.decode('ascii').strip())
                    print('*' * 40)
                if checkcrc(p1telegram):
                    # parse telegram contents, line by line
                    output = []
                    for line in p1telegram.split(b'\r\n'):
                        r = parsetelegramline(line.decode('ascii'))
                        if r:
                            output.append(r)
                            if debug:
                                print(f"desc:{r[0]}, val:{r[1]}, u:{r[2]}")
                    #print(tabulate(output,
                    #              headers=['Description', 'Value', 'Unit'],
                    #             tablefmt='github'))
                    prepare_data(output)
        except KeyboardInterrupt:
            print("Stopping...")
            ser.close()
            break
        except:
            if debug:
                print(traceback.format_exc())
            # print(traceback.format_exc())
            print ("Something went wrong...")
            ser.close()
        # flush the buffer
        ser.flush()

# Configuration settings
influxdb_url = "http://localhost:8086/api/v2/write?org=docs&bucket=home"
api_token = "opbXBXfTUfD8POAT3WYYGtlC2PTbkwx4QwbzIH4tREDTSw1TttqNKTfExafd0opk1Eixx_pK6eD285kjuGSwDw=="

def prepare_data(values):
    for line in values:
        data = f"Meter {line[0].replace(' ', '_')}={line[1]}"
        print(data)
        send_to_influxdb(data)

def send_to_influxdb(values):
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "text/plain"
    }
    response = requests.post(influxdb_url, data=values, headers=headers)
    if response.status_code == 204:
        print(f"Successfully written to InfluxDB.")
    else:
        print(f"Failed to write to InfluxDB. Status code: {response.status_code}")

if __name__ == "__main__":
    main()
