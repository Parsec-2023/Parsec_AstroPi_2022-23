from datetime import datetime, timedelta
from PIL import Image, ImageEnhance
from locale import normalize
from pathlib import Path
import numpy as np
import requests
import piexif
import csv
import cv2
import re
import ee
import os

#parameters
latitude = 33.819515149111375
longitude = -81.34991600471324
altitude = 416037 # corresponding altitude of the ISS
startString = "2000-02-25" # first date of the required dataset
endString = "2023-02-10" # last date of the required dataset
interval = 7 # required number of days between each picture
imageSize = 2888 # size in pixels of the images that will be downloaded and elaborated
picName = "image_0.jpg" # path to the AstroPi image
logName = "log.txt" # path to the log file from the ISS
dataName = "data.csv" # path to the CSV data file from the ISS

# csv file header
csvheader = [
    "Date[YYYY-MM-DD]",
    "mppx[m]",
    "Pixel_area[m2]",
    "WaterArea[m2]",
    "LakesArea[m2]",
    "SeaArea[m2]",
    "VegetationArea[m2]",
    "MeanNDWI",
    "MeanLakesNDWI",
    "MeanSeaNDWI",
    "MeanNDVI",
    "VegetationPercentage"
]

# get parent folder
baseFolder = Path(__file__).parent.resolve()

def main():
    # make sure that all parameters are correctly considered global
    global latitude
    global longitude
    global altitude
    global startString
    global endString
    global interval
    global imageSize
    global picName
    global logName
    global dataName

    # get the coordinates from the AstroPi picture if present
    picPath = str(baseFolder / picName)
    # check if the file exists
    if os.path.exists(picPath):
        # load the exif data from the picture
        exifDictionary = piexif.load(picPath)
        coordinates = getCoords(exifDictionary)

        # set the coordinates to the ones of the image if they are valid
        if (coordinates is not None):
            latitude, longitude = coordinates
        else:
            print("The coordinates that were loaded from the image were not valid. Using default coordinates instead.")
    else:
        print("\"" + picPath + "\"" + " not found. Using default coordinates instead. Modify the python code to change them.")

    # get the altitude based on the AstroPi image from the log file and the CSV file if both available
    logPath = str(baseFolder / logName)
    dataPath = str(baseFolder / dataName)
    # if both files are present
    if os.path.exists(logPath):
        if os.path.exists(dataPath):
            # set empty date and time strings
            date0, time0 = "", ""
            # open log file
            logfile = open(logPath, "r")
            # read each line
            found = False
            for line in logfile:
                # if the image name is found in the current line
                if picName in line:
                    # get matches corresponding to the date and time, based on the log file format [dd/mm/yyyy,hh:mm:ss]
                    match = re.match(r"\[([^,]*),(.*)\]", line)
                    if match is not None:
                        # get the date
                        date0 = match.group(1)
                        # and the time, by splitting before the ] in order to leave out the rest
                        time0 = match.group(2).split(']')[0]
                        found = True
                if found:
                    break
            if not found:
                print(picName, "was not found in the log file.")
            else: # if the date and the time in the log file were found, search them in the CSV file
                # open log file
                datafile = open(dataPath, "r")
                found = False
                for line in datafile:
                    # if the date and the time are in the current line
                    if ((date0 in line) and (time0 in line)):
                        # split the line to get the columns
                        csvItems = line.split(",")
                        # the altitude should be in the third column
                        alt0 = float(csvItems[2])
                        if (alt0 is not None) and (alt0 > 0):
                            altitude = alt0
                            print("Altitude of the image (from the CSV file):", altitude)
                            found = True
                    if found:
                        break
                if not found:
                    print("The time of the image was not found in the CSV file. Using default altitude instead. Modify the python code to change it.")
        else:
            print("\"" + dataPath + "\"" + " not found. Using default altitude instead. Modify the python code to change it.")
    else:
        print("\"" + logPath + "\"" + " not found. Using default altitude instead. Modify the python code to change it.")

    # open csv file or create it with its header if it does not exist
    datafilePath = str(baseFolder / "dataset.csv")
    datafile = open(datafilePath, "a+", newline = '', encoding = "utf-8")
    datawriter = csv.writer(datafile)
    if ((not os.path.exists(datafilePath)) or (os.path.getsize(datafilePath) == 0)):
        print("File \"data.csv\" not found. New copy created")
        datawriter.writerow(csvheader)  # write the header if the file is empty
        datafile.flush()
        os.fsync(datafile.fileno())
    
    # convert the dates into datetime objects
    start = datetime.strptime(startString, "%Y-%m-%d")
    end = datetime.strptime(endString, "%Y-%m-%d")

    # if the time interval is valid
    if (end >= start):
        # retrieve satellite images via Google Earth Engine API...
        # initialise the API
        ee.Initialize()
        print("Selected timeframe: ", start.strftime("%d/%m/%Y"), "-", end.strftime("%d/%m/%Y"))

        print("Altitude: ", altitude)
        # estimate the equivalent horizontal distance as a function of the altitude
        distance = estimateDistance(altitude)
        print("Estimated vertical distance:", distance)

        # calculate the meters per pixel of the image = actual distance in meters / length in pixels
        mppx = distance / imageSize
        # the area corresponding to each pixel will be the square of the resolution in meters per pixel
        pixelArea = mppx * mppx

        # create an Area Of Interest (aoi) of the right width around the centre
        centre = ee.Geometry.Point([longitude, latitude])
        aoi = centre.buffer(distance / 2).bounds()

        # set iteration to starting time
        time = start
        while (time <= end):
            # convert the time into a string
            time0 = time.strftime("%Y-%m-%d")
            time1 = (time + timedelta(days = interval)).strftime("%Y-%m-%d") # get the end of the interval
            print("Retrieving images", time.strftime("%d/%m/%Y"), "-", (time + timedelta(days = (interval - 1))).strftime("%d/%m/%Y"))

            # get the image from the API as an OpenCV image
            image = getPic(aoi, time0, time1)
            if (image is not None):
                print("Image successfully downloaded:", image.shape)

                # get the water mask
                waterMask = getWaterMask(image)
                # and the land mask as the inverse of the watermask
                landMask = np.where(waterMask > 0, 0, 255)

                # get NDVI and NDWI and apply the respective masks
                ndvi = calcNdvi(image)
                ndvi = np.where(landMask > 0, ndvi, 0)
                ndwi = calcNdwi(image)
                ndwi = np.where(waterMask > 0, ndwi, 0)

                # get the NDVI and NDWI masks from the respective images
                ndviMask = mask(ndvi, landMask)
                ndwiMask = mask(ndwi, waterMask)

                # remove from the mask the water bodies that touch the border of the image
                # these will mostly be oceans or seas, and even if they are rivers or lakes, it would not be possible to estimate their real surface
                lakesMask = removeBorderLabels(ndwiMask)

                # get sea mask
                invertedLakes = cv2.bitwise_not(lakesMask)
                seaMask = cv2.bitwise_and(ndwiMask, invertedLakes)

                # vegetation and water assessment:

                # count the water and the vegetation pixels
                waterPixels = np.count_nonzero(ndwiMask)
                lakesPixels = np.count_nonzero(lakesMask)
                seaPixels = np.count_nonzero(seaMask)
                vegetationPixels = np.count_nonzero(ndviMask)
                # calculate the area covered by water and vegetation by multiplying the number of pixels by their individual area
                waterSurface = pixelArea * waterPixels
                lakesSurface = pixelArea * lakesPixels
                seaSurface = pixelArea * seaPixels
                vegetationSurface = pixelArea * vegetationPixels

                # get separated NDWI images for lakes and sea
                ndwiLakes = np.where(lakesMask > 0, ndwi, 0)
                ndwiSea = np.where(seaMask > 0, ndwi, 0)

                # find average NDVI and NDWI in the image as the sum of all the values divided by the area of the image
                averageNdwi = np.mean(ndwi)
                averageLakesNdwi = np.mean(ndwiLakes)
                averageSeaNdwi = np.mean(ndwiSea)
                averageNdvi = np.mean(ndvi)
                # find the percentage of healthy vegetation
                percentVegetation = vegetationPixels / ndvi.size * 100

                # save the data on the csv file
                try:                                                                              
                    datawriter.writerow([time0, str(mppx), str(pixelArea), str(waterSurface), str(lakesSurface), str(seaSurface), str(vegetationSurface), str(averageNdwi), str(averageLakesNdwi), str(averageSeaNdwi), str(averageNdvi), str(percentVegetation)])
                    datafile.flush()
                    os.fsync(datafile.fileno())
                    print("Image data successfully saved")
                except:
                    print("Image data not saved")
            else:
                print("Error while downloading the image")

            # update the time based on the interval
            time += timedelta(days = interval)
    else:
        print("Timeframe not valid")
        return -1
    return 0

def estimateDistance(alt):
    sensorHeight = 0.004712 # real size of the Camera Module sensor
    focalLength = 0.005
    # actual distance on the surface in meters from the center (height)
    # it can be found with the formula distance = altitude * sensorHeight / focalLength
    return (alt * sensorHeight / focalLength)

# returns the satellite image of a given location and date as a cv2 image
def getPic(aoi, startTime, endTime):
    global imageSize

    # check if the given date is within the MODIS database limits
    if validDate(startTime, endTime, "2000-02-24", "2023-02-10"):
        # modis
        collection = (
            ee.ImageCollection("MODIS/006/MCD43A4") # dataset
            .filterBounds(aoi) # filter the area of interest
            .filterDate(startTime, endTime) # filter the date
            .sort("system:time_start", opt_ascending = False) # sort by date
            .select(["Nadir_Reflectance_Band1", "Nadir_Reflectance_Band4", "Nadir_Reflectance_Band2"]) #2 for IR, 3 for blue, 6 for SWIR
        )

        # combine all of the mosaics into one image and transform it into a 24-bit image (3x 8-bit channels 0-255)
        image24bit = collection.mosaic().divide(2000).multiply(255).clip(aoi).toByte()

        # format the image size from 1234 as a number to 1234x1234 string
        size = str(imageSize) + "x" + str(imageSize)
        # retrieve the url of the final image
        url = image24bit.getThumbURL({
            "region": aoi.getInfo()["coordinates"], # limit the region to the Area of Interest
            "crs": "EPSG:4326", # set the coordinate system
            "format": "jpg", # ask for a jpg image
            "dimensions": size # specify the dimensions of the image
        })

        # make a request to the image URL
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            # convert the image to a numpy array
            arr = np.asarray(bytearray(r.content), dtype=np.uint8)
            # decode the image from the array
            imageFromGoogle = cv2.imdecode(arr, -1)
            # check if the image is not empty
            if imageFromGoogle is not None:
                height, width, _ = imageFromGoogle.shape
                if (width > 0) and (height > 0):
                    # return the image if it is not empty
                    return imageFromGoogle
                else:
                    print("Empty image")
                    return None
            else:
                print("Unable to read the image")
                return None
        else:
            print("Error while downloading the image: error code", r.status_code)
            return None
    else:
        print("Timeframe not valid")
        return None

def validDate(imstart, imend, datastart, dataend) -> bool:
    # if at least one of the dates is within the interval, then the two intervals intersect (have at least a day in common)
    return (((imstart > datastart) and (imstart < dataend)) or ((imend > datastart) and (imend < dataend)))

def getCoords(exifDict):
    # get the GPS data
    try:
        gpsData = exifDict["GPS"]
        if len(gpsData) > 0:
            # extract the angles and convert them to decimal degrees
            lat = convertToAngle(gpsData[2])
            latRef = gpsData[1]
            lon = convertToAngle(gpsData[4])
            lonRef = gpsData[3]
            
            # make the angle negative when needed
            if latRef != "N":                     
                lat *= -1
            if lonRef != "E":
                lon *= -1

            print("Coordinates from the image:", str(lat) + ",", lon)
                    
            return lat, lon
        else:
            print("Empty GPS data")
    except Exception as e:
        print("GPS data not found in the image")
    return None

def convertToExif(angle):
    # convert a decimal degrees angle into a degrees, minutes, seconds tuple for piexif
    d = abs(angle)
    m = (d - int(d)) * 60
    s = (m - int(m)) * 60
    return [(int(d), 1), (int(m), 1), (int(s * 10000), 10000)]

def convertToAngle(angle):
    # convert an exif angle into decimal degrees
    # get degrees
    d0 = angle[0][0]
    d1 = angle[0][1]
    d = float(d0) / float(d1)
    # get minutes
    m0 = angle[1][0]
    m1 = angle[1][1]
    m = float(m0) / float(m1)
    # get seconds
    s0 = angle[2][0]
    s1 = angle[2][1]
    s = float(s0) / float(s1)
    # calculate the absolute value of the angle in degrees
    return d + (m / 60.0) + (s / 3600.0)

def setTimeLocation(fileName, time, lat, lon):
    # convert the date from "YYYY-MM-DD" to a datetime string "YYYY:MM:DD 00:00:00"
    time = datetime.strptime(time, "%Y-%m-%d").strftime("%Y:%m:%d 00:00:00")

    # location data
    gpsIfd = {
        piexif.GPSIFD.GPSLatitudeRef: "N" if lat >= 0 else "S",
        piexif.GPSIFD.GPSLatitude: convertToExif(lat),
        piexif.GPSIFD.GPSLongitudeRef: "E" if lon >= 0 else "W",
        piexif.GPSIFD.GPSLongitude: convertToExif(lon),
    }

    # create exif data dictionary and convert it into raw exif data
    exifDict = {"GPS": gpsIfd, "Exif": {piexif.ExifIFD.DateTimeOriginal: time}}
    exifBytes = piexif.dump(exifDict)

    # open the image with PIL and overwrite the time and the geolocation data
    img = Image.open(fileName)
    img.save(fileName, exif = exifBytes)

def calcNdvi(img):
    # convert the image to a float array
    imgf = img.astype('float32')
    # extract the channels
    red = imgf[:, :, 2]
    nir = imgf[:, :, 0]
    # calculate the NDVI array: NDVI = (NIR - RED) / (NIR + RED)
    num = nir - red
    den = nir + red
    epsilon = 1e-6 # a small value to prevent division by zero
    den += epsilon
    ndvi = np.where(den <= epsilon, 0, num / den) # avoid dividing by zero
    # normalise the values to the byte 0-255 range
    ndvi = cv2.normalize(ndvi, None, 0, 255, cv2.NORM_MINMAX, dtype = cv2.CV_8UC1)
    return ndvi

def calcNdwi(img):
    # convert the image to a float array
    imgf = img.astype('float32')
    # extract the channels
    green = imgf[:, :, 1]
    nir = imgf[:, :, 0]
    # calculate the NDWI array: NDWI = (GREEN - NIR) / (GREEN + NIR)
    num = green - nir
    den = green + nir
    epsilon = 1e-6 # a small value to prevent division by zero
    den += epsilon
    ndwi = np.where(den <= epsilon, 0, num / den) # avoid dividing by zero
    # normalise the values to the byte 0-255 range
    ndwi = cv2.normalize(ndwi, None, 0, 255, cv2.NORM_MINMAX, dtype = cv2.CV_8UC1)
    return ndwi

def getWaterMask(img):
    # strongly contrast the image
    img = contrast(img, 50)
    # turn it into grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = np.where(img < 16, 255, 0)
    return img

def mask(img, msk):
    # get a more detailed mask
    img = contrast(img)
    _, img = cv2.threshold(img, 80, 255, cv2.THRESH_TOZERO)
    img = contrast(img)
    # erode and dilate to eliminate irrelevant details
    img = cv2.erode(img, np.ones((3,3),np.uint8), iterations = 3)
    img = cv2.dilate(img, np.ones((3,3),np.uint8), iterations = 3)
    _, img = cv2.threshold(img, 80, 255, cv2.THRESH_BINARY)
    # apply the mask again
    img = np.where(msk > 16, img, 0)
    return img

def contrast(image, factor = 2.5):
    # convert the image from cv2 to PIL
    pilImg = Image.fromarray(image)
    # create enhancer object
    enhancer = ImageEnhance.Contrast(pilImg)
    # increase the contrast
    enhancedImg = enhancer.enhance(factor)
    # convert back to numpy array
    enhanced = np.array(enhancedImg)
    return enhanced

def removeBorderLabels(msk):
    # find the connected components
    numLabels, labelsIm = cv2.connectedComponents(msk)
    # find the labels that touch the border
    borderLabels = np.unique(np.vstack([labelsIm[0, :], labelsIm[-1, :], labelsIm[:, 0], labelsIm[:, -1]]))
    # set to black the areas of the original image that were white and touched the border
    for label in borderLabels:
        msk[labelsIm == label] = 0
    return msk

if __name__ == "__main__":
    main()