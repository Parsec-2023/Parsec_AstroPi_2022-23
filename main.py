import numpy as np
from orbit import ISS, ephemeris
from skyfield.api import load
from pathlib import Path
from PIL import Image, ImageEnhance
from sense_hat import SenseHat
from datetime import datetime, timedelta
from picamera import PiCamera
import csv
import os
import cv2

# get start time
startTime = datetime.now()

# initialise sense hat
sense = SenseHat()

# get parent folder
baseFolder = Path(__file__).parent.resolve()

# open log file or create it if it does not exist
logfile = open(baseFolder / "log.txt", "a", encoding = "utf-8")

def main():
    # csv file header
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
        log("File \"data.csv\" not found. New copy created")

    datawriter = csv.writer(datafile)
    # write the header if the file is empty
    if datafile.read() == "":
        datawriter.writerow(header)
        datafile.flush()
        os.fsync(datafile)

    try:
        # initialise camera
        camera = PiCamera()
        camera.resolution = (4056, 3040)
        camera.framerate = 15
        log("Camera initialised")
    except Exception as e:
        log("Error initialising camera: " + str(e))

    # reset current time and picture timer
    now = datetime.now()
    picTime = datetime.now()
    
    # picture counter
    n = 0

    # run the loop for 2 hours and 55 minutes after start time
    while (now < (startTime + timedelta(hours = 2, minutes = 55))):

        #-start counting the time
        s = datetime.now()

        # take a picture and save data every >=15 seconds
        if (now >= (picTime + timedelta(seconds = 15))):
            # if it is nighttime, do not take the picture
            if (ISS.at(load.timescale().now()).is_sunlit(ephemeris)):
                try:
                    # set picture path
                    picPath = str(baseFolder) + "/Pictures/" + "image_" + str(n) + ".jpg"

                    # locate the ISS
                    altitude, latitude, longitude = getISSPos()

                    # convert the ISS location to an EXIF-suitable format
                    south, exifLatitude = convertToExif(latitude)
                    west, exifLongitude = convertToExif(longitude)

                    # save the location in the metadata of the picture
                    camera.exif_tags['GPS.GPSAltitude'] = altitude
                    camera.exif_tags['GPS.GPSLatitude'] = exifLatitude
                    camera.exif_tags['GPS.GPSLatitudeRef'] = ("S" if south else "N")
                    camera.exif_tags['GPS.GPSLongitude'] = exifLongitude
                    camera.exif_tags['GPS.GPSLongitudeRef'] = ("W" if west else "E")

                    # take a picture at full resolution
                    camera.capture(picPath)

                    # open the picture as an OpenCV image
                    image = cv2.imread(picPath)

                    # scale down the image to make the following operations faster
                    scalingFactor = 0.4
                    scaledImage = cv2.resize(image, None, fx = scalingFactor, fy = scalingFactor)

                    # perform image segmentation on the scaled picture
                    segmented = segmentation(scaledImage)

                    # if the picture is relevant to our research (there is enough land)
                    score = evaluate(segmented)
                    if (score >= 2.5):
                        # crop the image to the window of the ISS to save storage space
                        image = cropCircle(scaledImage, image, scalingFactor)

                        # save the cropped image
                        cv2.imwrite(picPath, image)

                        # log the coordinates where the pic was taken
                        log("Picture " + "\"image_" + str(n) + ".jpg\"" + " taken at: (" + str(latitude) + ", " + str(longitude) + ") [score: " + str(round(score, 3)) + "]")
                    else:
                        log("Picture not taken - Not relevant")

                    #-print time taken
                    print(datetime.now() - s)

                except Exception as e:
                    log("Error taking a picture: " + str(e))
            else:
                log("Picture not taken - ISS not sunlit")

            # write data to data.csv and log.txt, and make sure the changes are saved
            try:
                datawriter.writerow(getData())
                log("Succesfully added data")
            except Exception as e:
                log("Error writing data: " + str(e))
            
            # reset picture timer
            picTime = datetime.now()

            # increment picture counter
            n += 1

        # update the current time
        now = datetime.now()

    # close camera and files
    camera.close()
    datafile.close()
    logfile.close()

def segmentation(im):
    # Image Segmentation
    # outputs the segmented 'im'
    # colour classes:
    #   glaciers + clouds: white
    #   water: blue
    #   vegetation: green
    #   other: red

    # get mask of the round window
    mk = mask(im) # single channel
    mk3 = cv2.merge([mk, mk, mk]) # 3 channels

    # remove the parts of the image that are outside of the mask
    im = np.bitwise_and(im, mk3)

    # separate channels blue, green, red from image and store them into different arrays
    b, g, r = cv2.split(im)
    # adjust data type to float
    b = b.astype(float)
    g = g.astype(float)
    r = r.astype(float)

    # NDVI
    # find the areas covered by vegetation
    # calculate ndvi value for each pixel
    # the blue channel contains the infrared value
    denominator = b + r
    denominator[denominator == 0] = 0.001
    ndvi = (b - r)/denominator
    # blur the image to remove any small artifacts
    ndvi = cv2.GaussianBlur(ndvi, (5, 5), 0)
    # remove the parts of the image that are not really land and have a low NDVI
    _, ndvi = cv2.threshold(ndvi, 0.25, 1, cv2.THRESH_BINARY)
    # convert it into BGR
    ndvi = cv2.convertScaleAbs(ndvi, alpha = 255)
    # fill in the holes of the mask
    ndvi = fill(ndvi)

    # NDWI
    # find the oceans and lakes
    # calculate NDWI value for each pixel
    # the blue channel contains the infrared value
    denominator = b + g
    denominator[denominator == 0] = 0.001 # calculate the denominator separately to check its value and adjust it in case it is zero
    ndwi = (g - b) / denominator
    # blur the image to remove any small artifacts
    ndwi = cv2.GaussianBlur(ndwi, (5, 5), 0)
    # remove the parts of the image that are not really water and have a low NDWI
    _, ndwi = cv2.threshold(ndwi, 0.01, 1, cv2.THRESH_BINARY)
    # convert it into BGR
    ndwi = cv2.convertScaleAbs(ndwi, alpha = 255)
    # fill in the holes of the mask
    ndwi = fill(ndwi)

    # WHITE
    # extracting the white areas from the original image
    # 'white' will be used to find glaciers, 'whiteMask' for the rest of the segmentation process
    # increment the contrast of the image
    im = contrast(im, 15)
    # convert the image to grayscale
    white = cv2.cvtColor(contrast(im), cv2.COLOR_BGR2GRAY)
    # apply a threshold to the mask in order to select only the brightest pixels
    _, white = cv2.threshold(white, 232, 255, cv2.THRESH_BINARY)
    white = cv2.convertScaleAbs(white, alpha = 255)
    # blur the image to blend the details together
    whiteMask = cv2.GaussianBlur(white, (7, 7), 0)
    # increase the definition again
    _, whiteMask = cv2.threshold(whiteMask, 64, 255, cv2.THRESH_BINARY)
    # fill in the holes of the mask
    whiteMask = fill(whiteMask)

    # LAND
    # detect areas not necessarily covered with vegetation by removing water and anything white from the mask
    # invert the white parts to get the mask of the areas that are not white = land + water
    notWhite = cv2.bitwise_not(white)
    notWhite = cv2.bitwise_and(notWhite, mk, mask = mk)
    # remove the areas covered in water from the "not white" areas to get the land
    land = notWhite - ndwi

    # FINAL IMAGE
    # make an empty image
    res = np.zeros_like(im)
    # intersect notWhite and ndwi to get the water only
    water = cv2.bitwise_and(notWhite, ndwi)
    # intersect notWhite and land to get the land only
    other = cv2.bitwise_and(notWhite, land)
    # intersect notWhite and ndvi to get the vegetation only
    veget = cv2.bitwise_and(notWhite, ndvi)
    # remove the vegetation from the water and from the clouds
    water -= veget
    water -= other
    white -= veget
    # remove the vegetation from the rest of the land
    other -= veget
    # convert the white image to 3 channels
    white = cv2.merge([white, white, white])
    # water -> blue
    water = colourise(water, 0, 0, 255)
    # vegetation -> green
    veget = colourise(veget, 0, 255, 0)
    # rest -> red
    other = colourise(other, 255, 0, 0)
    # overlay and merge all the masks
    res = cv2.bitwise_or(white, water, mask = mk)
    res = cv2.bitwise_or(res, veget, mask = mk)
    res = cv2.bitwise_or(res, other, mask = mk)

    return res

def evaluate(im):
    # split the image into the 3 colour channels
    b, g, r = cv2.split(im)

    # get the total number of pixels in the image
    totalPixels = im.shape[0] * im.shape[1]
    
    # count the number of green pixels, excluding the white pixels
    greenPixels = len(np.where((g != b) & (g != r))[0])
    # count the number of red pixels, excluding the white pixels
    redPixels = len(np.where((r != b) & (r != g))[0])

    # calculate the percentage of green pixels
    percentageGreen = greenPixels / totalPixels * 100
    # calculate the percentage of red pixels
    percentageRed = redPixels / totalPixels * 100

    # calculate the score of the image [score = 10g% + r%]
    score = (10 * percentageGreen) + percentageRed

    return score

def convertToExif(angle):
    # get the sign
    sign = angle

    # get the degrees
    degrees = int(angle)
  
    # keep the decimal part and multiply by 60
    angle = (angle - degrees) * 60
    # get the minutes
    minutes = int(angle)
  
    # keep the decimal part and multiply by 60
    angle = (angle - minutes) * 60
    # get the seconds
    seconds = int(angle)

    # format the angle as a string
    exifAngle = f"{degrees:.0f}/1,{minutes:.0f}/1,{seconds*1000000:.0f}/1000000"
    
    return (sign < 0), exifAngle

def formatTime(val):
    # adds a 0 before the number in case it is <10
    return (str(val) if (val >= 10) else ("0" + str(val)))

def getDate():
    # returns current date as dd/mm/yyyy
    return (formatTime(datetime.now().day) + "/" + formatTime(datetime.now().month) + "/" + formatTime(datetime.now().year))

def getTime():
    # returns current time as hh:mm:ss.sss
    return (formatTime(datetime.now().hour) + ":" + formatTime(datetime.now().minute) + ":" + formatTime(datetime.now().second))

def log(msg):
    # appends a line that indicates the current time and date and the message msg to the file f 
    logfile.write("[" + getDate() + "," + getTime() + "] " + msg + "\n")
    logfile.flush()
    os.fsync(logfile)

def cropCircle(scaledIm, im, scalingFactor):
    # get the size of the scaled image
    height, width, _ = scaledIm.shape
    
    # get the round mask of the window
    mk = mask(scaledIm)

    # find contours in the image
    contours, _ = cv2.findContours(mk, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    for contour in contours: # for each contour...
        # find a circle that fits the contour of the frame of the window
        (xCentre, yCentre), radius = cv2.minEnclosingCircle(contour)
        # if the circle is the right size (1/4 height < radius < 2/3 height)
        if ((radius > (min(height, width) / 4)) and (radius < (min(height, width) / 1.5))):
            # upscale the circle according to the size of the original image
            radius /= scalingFactor
            xCentre /= scalingFactor
            yCentre /= scalingFactor
            
            # calculate the size of the circle
            size = (2 * int(radius), 2 * int(radius))

            # crop the image to fit the circle that has been found
            im = cv2.getRectSubPix(im, size, (int(xCentre + 5), int(yCentre)))
            break
    return im

def colourise(im, r, g, b):
    # turns a single channel black and white image into a 3 channel BGR image of a given colour

    # get mask of the white pixels
    mk = im > 192

    # copy the image in every channel
    redChannel = im.copy()
    greenChannel = im.copy()
    blueChannel = im.copy()

    # set the colour
    redChannel[mk] = r
    greenChannel[mk] = g
    blueChannel[mk] = b

    # create the image with the three channels
    _, res = cv2.threshold(cv2.merge([blueChannel, greenChannel, redChannel]), 16, 255, cv2.THRESH_BINARY)
    return res

def mask(im):
    # convert the image into a PIL image
    pil_image = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))

    # increase contrast
    enhancer = ImageEnhance.Contrast(pil_image)
    pil_image = enhancer.enhance(1 + 100 / 100)
    # increase brightness
    enhancer = ImageEnhance.Brightness(pil_image)
    pil_image = enhancer.enhance(100)

    # convert the image back into a cv2 image
    im = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    # find the pixels that are not white...
    colours = np.where((im[:, :, 0] != 255) | (im[:, :, 1] != 255) | (im[:, :, 2] != 255))
    # ...and set them to black
    im[colours] = [0, 0, 0]

    # convert the image into grayscale
    grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    # apply a threshold to make sure that the picture is only black and white
    _, grey = cv2.threshold(grey, 10, 255, cv2.THRESH_BINARY)

    # fill up any holes in the mask
    grey = fill(grey)

    return grey

def fill(im):
    # make a copy of the current image
    mk = im.copy()

    # make a slightly bigger mask (two pixels)
    im2 = np.zeros((im.shape[0] + 2, im.shape[1] + 2), dtype = np.uint8)

    # fill the copy of the mask from the top-left and bottom-right corners
    cv2.floodFill(im, im2, (0, 0), 255, 0, 0)
    cv2.floodFill(im, im2, (im.shape[1] - 1, im.shape[0] - 1), 255, 0, 0)

    # invert it (it is all white except the parts that have to be)
    im = np.invert(im)

    # add the filled area to the image to fill up any black patches
    return cv2.bitwise_or(im, mk)

def contrast(im, k = 75):
    #increases contrast, sharpness, brightness. The default contrast value is 75
    
    # convert cv2 image to PIl image
    pil_image = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))

    # contrast
    enhancer = ImageEnhance.Contrast(pil_image)
    pil_image = enhancer.enhance(1 + k / 100)

    # sharpness
    enhancer = ImageEnhance.Sharpness(pil_image)
    pil_image = enhancer.enhance(1)

    # brightness
    enhancer = ImageEnhance.Brightness(pil_image)
    pil_image = enhancer.enhance(1)

    # convert PIL image into cv2 image
    im = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return im

def getISSPos():
    # get current ISS location
    loc = ISS.at(load.timescale().now()).subpoint()

    # return the altitude in meters, and latitude and longitude in degrees
    return (loc.elevation.m, loc.latitude.degrees, loc.longitude.degrees)

def getData():
    senseData = []

    # get date [DD/MM/YYYY]
    try:
        senseData.append(getDate())
    except Exception as e:
        log("ERROR getting date: " + str(e))
        senseData.append("-")

    # get UTC time [hh:mm:ss]
    try:
        senseData.append(getTime())
    except Exception as e:
        log("ERROR getting time: " + str(e))
        senseData.append("-")

    # get current coordinates [Deg] and altitude [m] of the ISS
    try:
        # find where the ISS is now
        altitude, latitude, longitude = getISSPos()
        senseData.append(str(int(altitude)))
        senseData.append(str(latitude))
        senseData.append(str(longitude))
    except Exception as e:
        log("ERROR getting ISS location: " + str(e))
        senseData.append("-")
        senseData.append("-")
        senseData.append("-")

    # get orientation [Deg]
    try:
        orientation = sense.get_orientation()
        senseData.append(str(orientation["yaw"]))
        senseData.append(str(orientation["pitch"]))
        senseData.append(str(orientation["roll"]))
    except Exception as e:
        log("Compass ERROR: " + str(e))
        senseData.append("-")
        senseData.append("-")
        senseData.append("-")

    # get acceleration [g]
    try:
        acceleration = sense.get_accelerometer_raw()
        senseData.append(str(acceleration["x"]))
        senseData.append(str(acceleration["y"]))
        senseData.append(str(acceleration["z"]))
    except Exception as e:
        log("Accelerometer ERROR: " + str(e))
        senseData.append("-")
        senseData.append("-")
        senseData.append("-")

    # get magnetic field intensity
    try:
        mag = sense.get_compass_raw()
        senseData.append(str(mag["x"]))
        senseData.append(str(mag["y"]))
        senseData.append(str(mag["z"]))
    except Exception as e:
        log("Compass ERROR: " + str(e))
        senseData.append("-")
        senseData.append("-")
        senseData.append("-")

    # get angular velocity
    try:
        gyro = sense.get_gyroscope_raw()
        senseData.append(str(gyro["x"]))
        senseData.append(str(gyro["y"]))
        senseData.append(str(gyro["z"]))
    except Exception as e:
        log("Gyro ERROR: " + str(e))
        senseData.append("-")
        senseData.append("-")
        senseData.append("-")

    # get temperature [°C]
    try:
        senseData.append(str(sense.get_temperature()))
    except Exception as e:
        log("Thermometer ERROR: " + str(e))
        senseData.append("-")

    # get pressure [mbar = hPa]
    try:
        senseData.append(str(sense.get_pressure()))
    except Exception as e:
        log("Barometer ERROR: " + str(e))
        senseData.append("-")

    # get humidity [%]
    try:
        senseData.append(str(sense.get_humidity()))
    except Exception as e:
        log("Humidity ERROR: " + str(e))
        senseData.append("-")

    return senseData

# call the main function
main()