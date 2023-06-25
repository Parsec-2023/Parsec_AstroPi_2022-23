import numpy as np
from pathlib import Path
from PIL import Image, ImageEnhance
from datetime import datetime
from datetime import timedelta
import os
import cv2

def main():
    #single("glaciers.jpg")
    #single("netherlands.jpg")
    single("photo_01183.jpg")
    #multiple(5)

def single(filename):
    start = datetime.now()
    im = cv2.imread(filename)

    # Calculate the scaling factor
    scaling_factor = min(720 / im.shape[1], 600 / im.shape[0])
    im = cv2.resize(im, None, fx = scaling_factor, fy = scaling_factor)

    mix = segmentation(im)
    im = cropCircle(im)
    
    isRelevant(mix)

    cv2.imshow("original " + filename, im)
    cv2.imshow("mix" + filename, mix)

    print((datetime.now() - start).total_seconds())
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def multiple(n):
    files = os.listdir()

    # Filter the list to include only image files
    image_files = [f for f in files if f.endswith('.jpg') or f.endswith('.png')]
    import random
    # Choose n random elements from the list
    random_imgs = random.sample(image_files, n)

    for filename in random_imgs:
        start = datetime.now()
        im = cv2.imread(filename)

        # Calculate the scaling factor
        scaling_factor = min(720 / im.shape[1], 600 / im.shape[0])
        im = cv2.resize(im, None, fx = scaling_factor, fy = scaling_factor)

        mix = segmentation(im)
        im = cropCircle(im)

        isRelevant(mix)

        cv2.imshow("original " + filename, im)
        cv2.imshow("mix" + filename, mix)

        print((datetime.now() - start).total_seconds())

    cv2.waitKey(0)
    cv2.destroyAllWindows()

def isRelevant(im):
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

    # calculate the percentage of green pixels
    percentageRed = redPixels / totalPixels * 100

    # calculate the score of the image
    score = (20 * percentageGreen) + (2 * percentageRed)

    print("Score:", score)
    print("Relevant" if (score > 15.0) else "Not Relevant")

    return score > 5.0

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
    # overlay all the masks
    res = cv2.bitwise_or(white, water, mask = mk)
    res = cv2.bitwise_or(res, veget, mask = mk)
    res = cv2.bitwise_or(res, other, mask = mk)

    return res

def cropCircle(im):
    # get the size of the image
    height, width, _ = im.shape

    # make a copy of the image. "image" will stay intact, "im" will be manupulated to extract the mask
    image = im
    
    # get the round mask of the window
    mk = mask(im)

    # find contours
    contours, _ = cv2.findContours(mk, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    for contour in contours: # for each contour...
        # find a circle that fits the contour of the frame of the window
        (xCenter, yCenter), radius = cv2.minEnclosingCircle(contour)
        # if the circle is the right size (1/4 height < radius < 2/3 height)
        if ((radius > (min(height, width) / 4)) and (radius < (min(height, width) / 1.5))):
            # calculate the size of the circle
            size = (2 * int(radius), 2 * int(radius))

            # crop the image to fit the circle that has been found
            image = cv2.getRectSubPix(image, size, (int(xCenter + 5), int(yCenter)))
            break
    return image

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

main()