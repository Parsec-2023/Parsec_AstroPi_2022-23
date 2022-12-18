#import tensorflow as tf
#from tensorflow import keras
import numpy as np
from orbit import ISS
from pathlib import Path
from sense_hat import SenseHat
from datetime import datetime
from picamera import PiCamera
from time import sleep
import csv
import os

# initialise sense hat
sense = SenseHat()

def main():
    baseFolder = Path(__file__).parent.resolve()
    header = [
        "Date[DD/MM/YYYY]",
        "Time[UTC-24H h:m:s]",
        "Altitude[m]",
        "Latitude[Deg]",
        "Longitude[Deg]",
        "Yaw[Deg]",
        "Pitch[Deg]",
        "Roll[Deg]",
        "xAcceleration[g]",
        "yAcceleration[g]",
        "zAcceleration[g]",
        "xMag[µT]",
        "yMag[µT]",
        "zMag[µT]",
        "xω[rad/s]",
        "yω[rad/s]",
        "zω[rad/s]",
        "Temperature[°C]",
        "Pressure[hPa]",
        "Humidity[%]",
    ]

    # open csv file or create it if it does not exist
    try:
        datafile = open(baseFolder / "data.csv", "r+", encoding = "utf-8")
    except:
        datafile = open(baseFolder / "data.csv", "a+", encoding = "utf-8")

    datawriter = csv.writer(datafile)
    # write the header if the file is empty
    if datafile.read() == "":
        datawriter.writerow(header)
        datafile.flush()
        os.fsync(datafile)

    # open log file or create it if it does not exist
    logfile = open(baseFolder / "log.txt", "a", encoding = "utf-8")

    try:
        # initialise camera
        camera = PiCamera()
        camera.resolution = (3040, 3040)
        camera.framerate = 15
        log(logfile, "Camera connected")
    except:
        log(logfile, "Error connecting camera")
    
    for i in range(3):
        camera.capture(str(baseFolder) + "/Pictures/" + "image_" + str(i) + ".jpg")  # Take a picture every minute for 3 hours)

        # write data to data.csv and log.txt, and make sure the changes are saved
        try:
            log(logfile, "Succesfully added data")
        except:
            log(logfile, "Error writing data")

        sleep(1)

    datafile.close()
    logfile.close()

def getDate():
    return (str(datetime.now().day) + "/" + str(datetime.now().month) + "/" + str(datetime.now().year))

def getTime():
    return (str(datetime.now().hour) + ":" + str(datetime.now().minute) + ":" + str(datetime.now().second + round(datetime.now().microsecond / 1000000, 3)))

def log(f, msg):
    f.write("[" + getDate() + "," + getTime() + "] " + msg + "\n")
    f.flush()
    os.fsync(f)

def getSenseData():
    senseData = []

    # get date [DD/MM/YYYY]
    senseData.append(getDate())

    # get UTC time [hh:mm:ss...]
    senseData.append(getTime())

    # get current coordinates [Deg] and altitude [m] of the ISS
    location = ISS.coordinates()
    senseData.append(str(location.elevation.m))
    senseData.append(str(location.latitude.degrees()))
    senseData.append(str(location.longitude.degrees()))

    # get orientation [Deg]
    orientation = sense.get_orientation()
    senseData.append(str(orientation["yaw"]))
    senseData.append(str(orientation["pitch"]))
    senseData.append(str(orientation["roll"]))

    # get acceleration [g]
    acceleration = sense.get_accelerometer_raw()
    senseData.append(str(acceleration["x"]))
    senseData.append(str(acceleration["y"]))
    senseData.append(str(acceleration["z"]))

    # get magnetic field intensity
    mag = sense.get_compass_raw()
    senseData.append(str(mag["x"]))
    senseData.append(str(mag["y"]))
    senseData.append(str(mag["z"]))

    # get angular velocity
    gyro = sense.get_gyroscope_raw()
    senseData.append(str(gyro["x"]))
    senseData.append(str(gyro["y"]))
    senseData.append(str(gyro["z"]))

    # get temperature [°C]
    senseData.append(str(sense.get_temperature()))

    # get pressure [mbar = hPa]
    senseData.append(str(sense.get_pressure()))

    # get humidity [%]
    senseData.append(str(sense.get_humidity()))

    return senseData

# call the main function
main()