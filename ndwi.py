import cv2
import numpy as np
from PIL import Image, ImageEnhance
import os
from datetime import datetime, timedelta

prev_time = datetime.now()

def contrast(im): #increase contrast, sharpness, brightness
    
    # convert cv2 image to PIl image
    pil_image = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))

    # contrast
    enhancer = ImageEnhance.Contrast(pil_image)
    pil_image = enhancer.enhance(1 + 75 / 100)

    # sharpness
    #enhancer = ImageEnhance.Sharpness(pil_image)
    #pil_image = enhancer.enhance(1)

    # brightness
    #enhancer = ImageEnhance.Brightness(pil_image)
    #pil_image = enhancer.enhance(1)

    # convert PIL image into cv2 image
    im = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return im

def createNdwiImage(im): #returns NDWI grayscale image
       
    
    #separate channels blue, green, red from image and store them into different arrays
    b, g, r = cv2.split(im)
    
    #adjust data type to float
    b = b.astype(float)
    g = g.astype(float)
    r = r.astype(float)
    
    
    #calculate ndwi value for each pixel
    #blue channel contains infrared value
    #now much the difference between green and IR is big compared to the value of the total light
    denominator = b + g
    denominator[denominator==0] = 0.01 #calculate denominator separately to check its value and adjust it in case it is zero
    ndwi = (g - b)/denominator
    
    #values are currently in range [0;1] but we need them in range [0;255] to build the image
    ndwi = ndwi * 255
    #values are currently float but we need integers
    ndwi = ndwi.astype(np.uint8)
    #image must have separate values for B, G, R in each pixel to be handled by contrast()    
    
    ndwi_bgr_format = cv2.merge([ndwi,ndwi,ndwi])
    return ndwi_bgr_format


def main():
    start_time = datetime.now()
    prev_time = datetime.now()
    # load image
    image = cv2.imread('/home/pi/Pictures/astropi-ndvi-en-resources/cslab3ogel_Files_RawData_raw_image_247.jpeg')
    print('loaded image in ', datetime.now() - prev_time)
    prev_time = datetime.now()
    
    #enhance contrast
    contrasted = contrast(image)
    print('contrasted image in ', datetime.now() - prev_time)
    prev_time = datetime.now()
    
    #get NDWI image
    ndwiImage = createNdwiImage(contrasted)
    print('NDWI calculated in ', datetime.now() - prev_time)
    prev_time = datetime.now()
    
    #enhance contrast of NDWI image    
    ndwiContrasted = contrast(ndwiImage)
    print('contrasted image in ', datetime.now() - prev_time)
    prev_time = datetime.now()
    #save NDWI image to specified path
    os.chdir('/home/pi/Desktop') 
    cv2.imwrite('ndwi.jpg', ndwiContrasted)
    end_time = datetime.now()
    run_time = end_time - start_time
    print('process finished in ')
    print(run_time)
    print('seconds')

