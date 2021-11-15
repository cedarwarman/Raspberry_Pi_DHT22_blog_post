#!/usr/bin/env python3

# Cedar Warman
# 2021

# This script reads a DHT22 temperature/humidity sensor then writes the 
# data to a local file and uploads the data it to a Google Sheet. For proper
# function, ensure Google service account is set up according to the gspread 
# documentation. Each DHT22 sensor requires one URL file in the "url"
# directory. URL files contain tab-separated key/value pairs, one per line. 
# Required keys are "id", "pin", and "name". "id" refers to the spreadsheet 
# ID, the alphanumeric string starting after /d/ and ending before the next 
# slash in the Google Sheet URL. "pin" is the Raspberry Pi GPIO pin number 
# that the sensor is connected to. "name" is the name of the sensor. Example 
# URL file:

# id    1DGjbXkpqrkglqMmGkD95zWBSfHBzGcjPj48pBIQ8Isa
# pin   4
# name  example_sensor

# Data reading adapted from https://pimylifeup.com/raspberry-pi-humidity-sensor-dht22/

import os
import time
import glob
import Adafruit_DHT
import gspread


### Open Google Sheet URLs file
# The url file is a tsv file described above
def open_url_files(dir_path, sensor_list):
    url_dict = {}
    for file_path in glob.glob(dir_path + '*'):
        print("working on " + file_path)
        # Getting the file name
        file_string = os.path.basename(file_path)
        file_string = os.path.splitext(file_string)[0]
        # Checking to see if it's on the sensor_list
        print("file_string: " + file_string)
        #print("sensor_list: " + sensor_list)
        if any(sensor_string in file_string for sensor_string in sensor_list):
            print("Matched string")
            with open(file_path, 'r') as url_file:
                nest_dict = {}
                for line in url_file:
                    # Adding values to the nested dictionary
                    (key, value) = line.split()
                    nest_dict[key] = value
                # Adding the nested dictionary to the main dictionary
                url_dict[file_string] = nest_dict
        else:
            print("no match")
    return(url_dict)

### Open the file to write out
def open_output_file():
    output_dir = os.path.join(os.path.realpath(__file__), "output")
    output_file_path = os.path.join(output_dir, "sensor_output.csv")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        f = open(output_file_path, 'a+')
        if os.stat(output_file_path).st_size == 0:
                f.write('date\ttime\ttemp_c\ttemp_f\thumidity\tpin\r\n')
        return(f)
    except:
        pass


### Read the sensor 
def read_sensor(dht_sensor, dht_pin, input_time):
    humidity, temp_c = Adafruit_DHT.read_retry(dht_sensor, dht_pin)

    if humidity is not None and temp_c is not None:
        # C to F conversion
        temp_f = (temp_c * 9/5) + 32

        # Test print
        # print("Temp={0:0.1f} C ({1:0.1f} F) Humidity={2:0.1f}%".format(temp_c, temp_f, humidity))

        sensor_list = [time.strftime('%H:%M:%S', input_time), temp_c, temp_f, humidity]
        return(sensor_list)

    else:
        print("Failed to retrieve data from humidity sensor")


### Append to file
def append_file(input_file_handle, input_list, input_time, dht_pin):
    try:
        input_file_handle.write('{0}\t{1}\t{2:0.1f}\t{3:0.1f}\t{4:0.1f}\t{5}\r\n'.format(time.strftime('%Y-%m-%d',
        input_time),
        input_list[0], input_list[1], input_list[2], input_list[3], dht_pin))
        input_file_handle.flush()
    except:
        print("Fail to write to file")


### Append to Google sheet
def append_google_sheet(input_list, sheet_key, input_time):
    try:
        # Setting up the service account info
        # (/home/pi/.config/gspread/service_account.json)
        gc = gspread.service_account()

        # Reading the sheet
        sheet = gc.open_by_key(sheet_key).sheet1    

        # Writing the data
        append_list = [time.strftime('%Y-%m-%d', input_time), 
        input_list[0], 
        round(input_list[1], 1), 
        round(input_list[2], 1), 
        round(input_list[3], 1)]
        sheet.append_row(append_list)
    except:
        print("Failed to upload to Google Sheets")


def main():
    dht_sensor = Adafruit_DHT.DHT22
    start_time = time.time() # Initial time for fancy sleep

    # Opening the file with the Google sheet IDs
    url_file_dir_path = os.path.join(os.path.realpath(__file__), "url")
    sheet_ids = open_url_files(url_file_dir_path, 
        ###### CHANGE SENSORS HERE ######
        ["home_livingroom", "home_outside"])

    f = open_output_file()

    while True:
        # Gives everything the same time to fix a bug that came from calling 
        # time() a bunch of times
        read_time = time.localtime()
        
        for sensor_location, sensor_dict in sheet_ids.items():
            dht_pin = sensor_dict.get('pin')
            sensor_output = read_sensor(dht_sensor, dht_pin, read_time)
            append_file(f, sensor_output, read_time, dht_pin)
            # Appends to Google Sheet
            append_google_sheet(sensor_output, sensor_dict.get('id'), read_time)

        time.sleep(120.0 - ((time.time() - start_time) % 60.0))


if __name__ == "__main__":
    main()
