import cv2
import numpy as np
from PIL import Image, ImageEnhance
import os
from datetime import datetime, timedelta

def contrast(im): #increase contrast, sharpness, brightness
    
    # convert cv2 image to PIl image
    pil_image = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))

    # contrast
    enhancer = ImageEnhance.Contrast(pil_image)
    pil_image = enhancer.enhance(1 + 75 / 100)

    # sharpness
    enhancer = ImageEnhance.Sharpness(pil_image)
    pil_image = enhancer.enhance(1)

    # brightness
    enhancer = ImageEnhance.Brightness(pil_image)
    pil_image = enhancer.enhance(1)

    # convert PIL image into cv2 image
    im = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return im

def createNdviImage(im): #returns NDVI greyscale image
       
    
    #separate channels blue, green, red from image and store them into different arrays
    b, g, r = cv2.split(im)
    
    #adjust data type to float
    b = b.astype(float)
    g = g.astype(float)
    r = r.astype(float)
    
    
    #calculate ndvi value for each pixel
    #blue channel contains infrared value
    #now much the difference between IR and VIS is big compared to the value of total light
    #calculate denominator separately to check its value and fix it different from zero
    denominator = b + r
    denominator[denominator==0] = 0.01 
    ndvi = (b - r)/denominator
    
    #ndvi values are currently in range [0;1] but we need them in range [0;255] to build the image
    ndvi = ndvi * 255
    #ndvi values are currently float but we need integers
    ndvi = ndvi.astype(np.uint8)
  
    #image must have separate values for B, G, R in each pixel to be handled by contrast()    
    ndvi_bgr_format = cv2.merge([ndvi,ndvi,ndvi])
    return ndvi_bgr_format

def main():
    start_time = datetime.now()
    # load image
    image = cv2.imread('/home/pi/Desktop/park_ir.jpg')
    #enhance contrast
    contrasted = contrast(image)
    #get NDVI image
    ndviImage = createNdviImage(contrasted)
    #enhance contrast of NDVI image    
    ndviContrasted = contrast(ndviImage)
    #os.chdir('/home/pi/Desktop') #save NDVI image to specified path
    cv2.imwrite('ndvi.jpg', ndviContrasted)
    end_time = datetime.now()
    run_time = end_time - start_time
    print('process finished in ')
    print(run_time)
    print('seconds')


main()