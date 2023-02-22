import numpy as np
from PIL import Image
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
logfile = open(str(baseFolder / "log.txt"), "a", encoding = "utf-8")

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

    # initialise the path to the folder that will contain the pictures
    picsFolder = str(baseFolder) + "/Pictures"
    try:
        # and create it if it does not exist
        if (not os.path.exists(picsFolder)):
            os.makedirs(picsFolder)
    except Exception as e:
        log("FATAL ERROR - unable to find or create Pictures folder: " + str(e))

    # open csv file or create it if it does not exist
    try:
        datafile = open(str(baseFolder / "data.csv"), "r+", encoding = "utf-8")
    except:
        datafile = open(str(baseFolder / "data.csv"), "a+", encoding = "utf-8")
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
        camera.framerate = 24
        log("Camera initialised")
    except Exception as e:
        log("Error initialising camera: " + str(e))

    # initialise time and picture timer
    now = datetime.now()
    picTime = datetime.now()
    
    # initialise picture counters
    n = 0 # total number of cycles
    p = 0 # number of pictures taken

    # initialise the size of the Pictures folder (...<baseFolder>/Pictures)
    picFolderSize = 0

    # set the initial interval for taking pictures to 3 seconds
    interval = 3

    # run the loop for 2 hours and 55 minutes after start time
    while (now < (startTime + timedelta(hours = 2, minutes = 57, seconds = 30))):

        # start counting the time for each picture
        picDeltaTime = datetime.now()

        # take a picture and save data every 'interval' seconds, if interval is bigger than 3
        # (we have calculated that if we take a picture every 3 seconds, the data limit of 3GB should not be exceeded)
        if (now >= (picTime + timedelta(seconds = (int(interval) if (interval >= 3) else 3)))):
            # if it is nighttime, do not take the picture
            if (ISS.at(load.timescale().now()).is_sunlit(ephemeris)):
                try:
                    # temporary picture path
                    tmpPicPath = picsFolder + "/tmpImage.jpg"
                    # set the path where the final image will be saved
                    picPath = picsFolder + "/image_" + str(n) + ".jpg"

                    # locate the ISS
                    altitude, latitude, longitude = getISSPos()

                    # convert the ISS location to an EXIF-suitable format
                    south, exifLatitude = convertToExif(latitude)
                    west, exifLongitude = convertToExif(longitude)

                    # save the location in the metadata of the picture
                    camera.exif_tags['GPS.GPSAltitude'] = (str(int(altitude)) + "/1")
                    camera.exif_tags['GPS.GPSLatitude'] = exifLatitude
                    camera.exif_tags['GPS.GPSLatitudeRef'] = ("S" if south else "N")
                    camera.exif_tags['GPS.GPSLongitude'] = exifLongitude
                    camera.exif_tags['GPS.GPSLongitudeRef'] = ("W" if west else "E")

                    # take a picture at full resolution and save it as temporary
                    camera.capture(tmpPicPath, quality = 100)
                    print("Tmp picture saved at: " + tmpPicPath)

                    # open the picture as an OpenCV image
                    image = cv2.imread(tmpPicPath)
                    print("Tmp picture opened")

                    # scale down the image to make the following operations faster
                    scalingFactor = 0.3
                    scaledImage = cv2.resize(image, None, fx = scalingFactor, fy = scalingFactor)
                    print("Picture resized")

                    # perform image segmentation on the scaled picture
                    segmented = segmentation(scaledImage)
                    print("Picture segmented")

                    # if the picture is relevant to our research (there is enough land)...
                    score = evaluate(segmented)
                    print("Score: " + str(score))
                    if (score >= 2.5):
                        # crop the original image to the window of the ISS to save storage space
                        image = cropCircle(scaledImage, image, scalingFactor)
                        print("Picture cropped")

                        # save the cropped image with its final name
                        cv2.imwrite(picPath, image)
                        print("Picture saved at: " + picPath)

                        # save the exif data to the final image
                        try:
                            # open the temporary image with PIL
                            tmpImage = Image.open(tmpPicPath)
                            # get its exif data
                            exifData = tmpImage.info["exif"]
                            # open the cropped image with PIL
                            finalImage = Image.open(picPath)
                            # save the exif data to the final image
                            finalImage.save(picPath, exif = exifData)
                        except Exception as e:
                            log("Unable to save EXIF data: " + str(e))

                        # increment the number of pictures
                        p += 1
                        # increment the size of the Pictures folder
                        picFolderSize += os.path.getsize(picPath)

                        # update the minimum time interval for taking pictures according to the remaining time and remaining storage space:
                        # the remaining space is the total space (we went for 2.975GB to leave some wiggle room for safety) minus the current space taken
                        remainingSpace = 2975000000 - picFolderSize
                        # the remaining time is the initial time plus almost three hours minus the current time
                        remainingTime = (startTime + timedelta(hours = 2, minutes = 57, seconds = 30) - datetime.now()).seconds
                        # given 'remainingSpace' bytes left and 'remainingTime' seconds to save an 'averageSpace' amount of bytes every 'interval' seconds, the following proportion applies:
                        # interval : averageSpace = remainingTime : remainingSpace
                        # therefore -> interval = averageSpace * remainingTime / remainingSpace
                        # the average space of one picture is calculated by dividing the total size of the Pictures folder by the number of pictures it contains
                        interval = ((picFolderSize / p) * remainingTime / remainingSpace)

                        # log the coordinates where the pic was taken
                        log("Picture " + "\"image_" + str(n) + ".jpg\"" + " taken at: (" + str(latitude) + ", " + str(longitude) + ") [score: " + str(round(score, 3)) + "]")

                        # log the new time interval
                        log("Time interval: " + str(interval))
                    else:
                        log("Picture not taken - Not relevant")
                    
                    # print time taken
                    log("Time taken: " + str(datetime.now() - picDeltaTime))
                    
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

        # if the size of the folder exceeds 2.75GB, stop the program
        if (picFolderSize >= 2750000000):
            elapsedTime = str(int((now - startTime).seconds))
            log("Program aborted after " + elapsedTime + "s: size limit exceeded")
            break
    
    # log the final time in case the program ended correctly after 2h:55m
    totalTime = datetime.now() - startTime
    if (totalTime >= timedelta(hours = 2, minutes = 57, seconds = 30)):
        log("Program successfully terminated after " + str(totalTime.seconds) + "s")

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
    greenPixels = np.sum((g != b) & (g != r))
    # count the number of red pixels, excluding the white pixels
    redPixels = np.sum((r != b) & (r != g))

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

    # make the angle positive
    angle = abs(angle)

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
    exifAngle = f"{degrees:.0f}/1,{minutes:.0f}/1,{seconds*1000:.0f}/1000"
    
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
    message = ("[" + getDate() + "," + getTime() + "] " + msg + "\n")
    logfile.write(message)
    logfile.flush()
    os.fsync(logfile)

    # print the message to console
    print(message)

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
    # return the original image object
    # if it has been cropped, the object itself is the cropped image
    # otherwise, if it has not been cropped, the image is the same
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
