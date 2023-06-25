from pathlib import Path
import requests
import cv2
import ee

#parameters
latitude = 33.819515149111375
longitude = -81.34991600471324
altitude = 416037 # corresponding altitude of the ISS
start = "2017-02-05" # first date of the required dataset
end = "2017-02-07" # last date of the required dataset
imageSize = 1080 # size in pixels of the images that will be downloaded and elaborated

# get parent folder
baseFolder = Path(__file__).parent.resolve()

def main():
    # make sure that all parameters are correctly considered global
    global latitude
    global longitude
    global altitude
    global start
    global end
    global imageSize

    # if the time interval is valid
    if (end >= start):
        # initialise Google Earth Engine API
        ee.Initialize()
    
        # estimate the equivalent horizontal distance as a function of the altitude
        distance = estimateDistance(altitude)

        # create an Area Of Interest (aoi) around the centre
        centre = ee.Geometry.Point([longitude, latitude])
        aoi = centre.buffer(distance / 2).bounds()

        # make an empty list of images
        mosaics = []
        """
        if validDate(start, end, "2017-03-28", "2023-06-12"):
            # sentinel 2
            imS2 = (
                ee.ImageCollection("COPERNICUS/S2") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 100)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B4", "B3", "B2"]) # colour channels (B8 NIR)
            )

            # sentinel 2 surface reflectance
            imS2sr = (
                ee.ImageCollection("COPERNICUS/S2_SR") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 100)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B4", "B3", "B2"]) # colour channels (B8 NIR)
            )

            # harmonised sentinel 2
            imS2h = (
                ee.ImageCollection("COPERNICUS/S2_HARMONIZED") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 100)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B4", "B3", "B2"]) # colour channels (B8 NIR)
            )

            # harmonised sentinel 2 surface reflectance
            imS2srh = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 100)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B4", "B3", "B2"]) # colour channels (B8 NIR)
            )
        
            # make a mosaic of the images that have been found in each of the different datasets
            mosaicS2 = imS2.mosaic()
            mosaicS2sr = imS2sr.mosaic()
            mosaicS2h = imS2h.mosaic()
            mosaicS2srh = imS2srh.mosaic()
            # add the images to the list
            mosaics.append(mosaicS2)
            mosaics.append(mosaicS2sr)
            mosaics.append(mosaicS2h)
            mosaics.append(mosaicS2srh)

        if validDate(start, end, "1972-07-26", "1978-01-06"):
            # landsat 1
            imL1 = (
                ee.ImageCollection("LANDSAT/LM01/C02/T1") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUD_COVER_LAND", 1)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B5", "B4", "B6"]) # colour channels (B6 is already NIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicL1 = imL1.mosaic()
            # add the image to the list
            mosaics.append(mosaicL1)

        if validDate(start, end, "1975-02-01", "1982-02-02"):
            # landsat 2
            imL2 = (
                ee.ImageCollection("LANDSAT/LM02/C02/T1") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUD_COVER_LAND", 1)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B5", "B4", "B6"]) # colour channels (B6 is already NIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicL2 = imL2.mosaic()
            # add the image to the list
            mosaics.append(mosaicL2)

        if validDate(start, end, "1978-06-04", "1983-02-22"):
            # landsat 3
            imL3 = (
                ee.ImageCollection("LANDSAT/LM03/C02/T1") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUD_COVER_LAND", 1)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B5", "B4", "B6"]) # colour channels (B6 is already NIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicL3 = imL3.mosaic()
            # add the image to the list
            mosaics.append(mosaicL3)

        if validDate(start, end, "1982-08-23", "1993-06-23"):
            # landsat 4
            imL4 = (
                ee.ImageCollection("LANDSAT/LT04/C02/T1_L2") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUD_COVER_LAND", 1)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["SR_B3", "SR_B2", "SR_B1"]) # colour channels (SR_B4 NIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicL4 = imL4.mosaic()
            # add the image to the list
            mosaics.append(mosaicL4)

        if validDate(start, end, "1984-03-17", "2012-05-04"):
            # landsat 5
            imL5 = (
                ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUD_COVER_LAND", 1)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["SR_B3", "SR_B2", "SR_B1"]) # colour channels (SR_B4 NIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicL5 = imL5.mosaic()
            # add the image to the list
            mosaics.append(mosaicL5)

        if validDate(start, end, "1999-05-27", "2023-05-16"):
            # landsat 7
            imL7 = (
                ee.ImageCollection("LANDSAT/LE07/C02/T1_L2") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUD_COVER_LAND", 1)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["SR_B3", "SR_B2", "SR_B1"]) # colour channels (SR_B4 NIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicL7 = imL7.mosaic()
            # add the image to the list
            mosaics.append(mosaicL7)

        if validDate(start, end, "2013-03-17", "2023-06-03"):
            # landsat 8
            imL8 = (
                ee.ImageCollection("LANDSAT/LC08/C02/T1") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUD_COVER_LAND", 33)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B4", "B3", "B2"]) # colour channels (B5 NIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicL8 = imL8.mosaic()
            # add the image to the list
            mosaics.append(mosaicL8)

        if validDate(start, end, "2021-10-31", "2023-06-11"):
            # landsat 9
            imL9 = (
                ee.ImageCollection("LANDSAT/LC09/C02/T1") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .filter(ee.Filter.lt("CLOUD_COVER_LAND", 33)) # filter out cloudy images
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["B4", "B3", "B2"]) # colour channels (SR_B5 NIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicL9 = imL9.mosaic()
            # add the image to the list
            mosaics.append(mosaicL9)
            """
        if validDate(start, end, "2000-02-24", "2023-02-10"):
            # MODIS
            modis = (
                ee.ImageCollection("MODIS/006/MCD43A4") # dataset
                .filterBounds(aoi) # filter the area of interest
                .filterDate(start, end) # filter the date
                .sort("system:time_start", opt_ascending = False) # sort by date
                .select(["Nadir_Reflectance_Band1", "Nadir_Reflectance_Band4", "Nadir_Reflectance_Band2"]) # colour channels (2 for IR, 3 for blue, 6 for SWIR)
            )
        
            # make a mosaic of the images that have been found
            mosaicModis = modis.mosaic()
            # add the image to the list
            mosaics.append(mosaicModis)
    
        if (len(mosaics) < 1):
            print("No image was found in the given time period")
        else:
            print("Combining images from", len(mosaics), "datasets")

            # combine all of the mosaics into one image
            mosaicCombined = ee.ImageCollection(mosaics).mosaic()

            # create a 24-bit image (3 8-bit channels 0-255)
            image24bit = mosaicCombined.divide(10000).multiply(255).clip(aoi).toByte()

            # format the image size from 1234 as a number to 1234x1234 string
            size = str(imageSize) + "x" + str(imageSize)
            # retrieve the url of the final image
            url = image24bit.getThumbURL({
                "region": aoi.getInfo()["coordinates"], # limit the region to the Area of Interest
                "crs": "EPSG:4326", # set the coordinate system
                "format": "jpg", # ask for a jpg image
                "dimensions": size # specify the dimensions of the image
            })

            # download the jpg image
            r = requests.get(url, allow_redirects=True)
            # if download is possible
            if r.status_code == 200:
                # save the image
                open(str(baseFolder) + r"\imageFromGoogle.jpg", "wb").write(r.content)
                # load it with OpenCV
                imageFromGoogle = cv2.imread(str(baseFolder) + r"\imageFromGoogle.jpg")
                if imageFromGoogle is not None: # if the image is not empty
                    height, width, _ = imageFromGoogle.shape
                    if width > 0 and height > 0:
                        # display the image
                        cv2.imshow("Image from Google Earth", imageFromGoogle)
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    else:
                        print("Empty image")
                        return -1
                else:
                    print("Unable to read the image")
                    return -1
            else:
                print("Error while downloading the image: error code", r.status_code)
                return -1
    else:
        print("Timeframe not valid")
        return -1
    return 0

def validDate(imstart, imend, datastart, dataend) -> bool:
    # if at least one of the dates is within the interval, then the two intervals intersect (have at least a day in common)
    return (((imstart > datastart) and (imstart < dataend)) or ((imend > datastart) and (imend < dataend)))

def estimateDistance(alt):
    sensorHeight = 0.004712 # real size of the Camera Module sensor
    focalLength = 0.005
    # actual distance on the surface in meters from the center (height)
    # it can be found with the formula distance = altitude * sensorHeight / focalLength
    return (alt * sensorHeight / focalLength)

if __name__ == "__main__":
    main()