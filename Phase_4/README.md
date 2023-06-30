
# [Parsec-AstroPi](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23)
**2022-2023**  
Team name: Parsec  
School: *[Liceo Scientifico "Leonardo da Vinci", Gallarate (VA), IT](https://goo.gl/maps/iJFNK38aVivM7PgVA)*  
Mentor: Lucia Polidori  
Members: Daniele Nicolia, Davide Pascu, Matteo Saporiti, Leonardo Simonetti, Federico Sozzi, Jad Taljabini  
***
# PHASE 4
During the three hour period on the ISS, [our program](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/tree/main/Phase_1-3) collected 605 pictures and 2272 lines of data in a CSV file.\
Of course, for half of the time we could not take pictures, as the ISS has a day cycle of 1.5 hours and it stays in the darkness of the night for this amount of time. We were quite lucky it passed over the USA, Porto Rico, Suriname, Canada, South Africa, and part of Brazil during the 1.5 hours of light at our disposal:

![ISS trajectory](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Pictures/Trajectory.PNG)

For phase 4, we had to analyse this data: we wanted to see if there was any correlation between the area of land covered by vegetation and the surface area of lakes in the same region, or if we could implement a machine learning model - or anything similar in functionality - capable of taking satellite images (like we did with the [phase 2 program](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/tree/main/Phase_1-3)) and predicting the future variations of parameters linked to the environment and climate change, such as vegetation area, vegetation health, area covered by water, etc...
***
## The process
First of all, we analised the data we received, the `data.csv` file from our program that ran on the ISS. We used converted the file into *.xlsx* format and used Microsoft Excel to plot some graphs that could tell us about how the data collection went. For example, we noticed that the altitude of the ISS followed a periodic course, with the highest point (presumably the apogee) being at the highest latitudes and the lowest (perigee) around the equator:

![AltitudePlot](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Pictures/Altitude.PNG)

But then we moved on to what we were actually studying, water and vegetation. In short, what we needed to do was:
- Find an area that suits our research, based on the analysis we did on the CSV data in MS Excel
- Download a set of NIR satellite pictures from the internet and edit them to roughly simulate what we would get by running our [phase 2 program](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/tree/main/Phase_1-3) for a long period of time (years)
- Perform the necessary NDVI and NDWI calculations and masking to extract a dataset of relevant parameters from the images
- Use the dataset to:
	-  train a model and make predictions with it
	- find out if the vegetation area and the water area are correlated
	- see if we could measure the effects of climate change on lakes and coasts
## Method
We wanted to achieve all of this with an automatic process, with us writing our own code that would do everything, instead of using premade tools such as QGIS either manually (which would have been impossible) or automatically.\
Before starting to work on the image manipulation part of the program, the images that we downloaded had to be comparable and similar to the ones we got from the Astro Pi camera on the ISS, as we wanted to simulate our ISS program running for many years. In order to achieve this, we had to estimate the right focal length of the lens that was used on the ISS, so that we could use the formula that we derived: $realDistanceHeight=\frac{sensorHeight \cdot altitude}{focalLength}$ and, similarly, $realDistanceWidth=\frac{sensorWidth \cdot altitude}{focalLength}$\
Since we used the real distance on the Earth's surface to tell the API how big of an area to capture, we had to calculate this value as a function of the altitude of the ISS.\
With the altitude of one of the pictures and the size of the Astro Pi camera sensor:

| Altitude [m] | Sensor width [mm] | Sensor height [mm] |
|--|--|--|
| 416037 | 6.287 | 4.712 |

The resulting width and height of the area of land captured by the camera are:

| Focal length | Width [m] | Height [m] |
|--|--|--|
| 17.53 mm | 149209 | 111829 |
| 6 mm | 435937 | 326727 |
| 5 mm | 523125 | 392073 |

We measured some pictures with Google Earth and estimated their real width to be about *524460 m* and their height *392780 m*, therefore the right focal length was *5 mm*, as the values that we found matched almost perfectly with the ones that were calculated using *5 mm* for the focal length.\
Now it was time to start working towards our research goals.
This is the process we came up with:
- A program called [`createdataset.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/createdataset.py) calls the [*Google Earth Engine API*](https://earthengine.google.com/) to download satellite images in *OpenCV* format of a certain location at a determined interval of days between two dates. It takes each image and finds its NDVI, NDWI and the different masks that it then uses to estimate the **actual area** each mask corresponds to on the Earth's surface. At the end, it writes all of the data in a *CSV* file for analysis. The paramaters needed, such as the date boundaries, the equivalent altitude of the ISS for the picture and the coordinates, are loaded from specific files that can be copied to same folder as the program. If they are not present, default parameters defined in the source code are used.\
Initially, we wanted to use high resolution imagery from [Sentinel](https://developers.google.com/earth-engine/datasets/catalog/sentinel) and [Landsat](https://developers.google.com/earth-engine/datasets/catalog/landsat), but their images were too small to cover the field of view of the AstroPi camera. The script [`multiearth.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/multiearth.py) was supposed to use them to take as many pictures as possible within each time interval, with the reasonably lowest cloud coverage, and merge them together - with a process called mosaicing - in order fill up the entire area. Unfortunately, Sentinel and Landsat could not provide the degree of availability that we needed. Even collecting one month of pictures, the mosaic was mainly black when the cloud percentage threshold was low; and when we raised it, the images were completely covered by clouds in a different way in each segment of the total image. This meant that if we used these mosaics for our analysis, we would have gotten either way extremely inconsistent results.
For this reason, the final program `createdataset.py` takes the images between February 2000 and February 2023 from the [MODIS dataset](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD43A4), which has a much lower resolution but a wider area and a daily availability without clouds.
- At this point, there is a *CSV* file containing in each line the date, the water area, vegetation area and other data from each image. This is the dataset that will be used by the following programs.
- [`correlation.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/correlation.py) tries to establish if there is any correlation between any of the possible combinations in which two parameters from the dataset can be picked. This program extracts two columns from the *CSV* file and calculates the cross-correlation and the Kendall's τ of the two data series.
- The dataset is then used by [`sarima.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/sarima.py), which reads one of the columns, trains a SARIMA statistical model, makes predictions and calculates its root-mean-square error to evaluate the accuracy of the model.\
The hyperparameters of the SARIMA model are all set to 1 by default, but they can be optimised by running [`genetictraining.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/genetictraining.py), which takes the same dataset and uses a genetic algorithm to find the best hyperparameters and save them as a Numpy array file (`hyperparams.npy`). If `sarima.py` finds this file in its folder, it automatically retrieves the optimal hyperparameters from it.\
The individuals of the genetic algorithm represent a SARIMA model, with their properties being the hyperparameters of the model. The algorithm works by creating an initial generation with random parameters and then going through each generation by selecting and breeding the best individuals in order to get the following generation through mating and mutation. The fitness of each individual is determined by training its respective SARIMA and evaluating its root-mean-square error, which has to be as low as possible.\

___
We focused our attention on South Carolina, of which we had a good picture with many big lakes, such as Lake Marion and Lake Moultrie, and an interesting coastline:

![South carolina astropi camera](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Pictures/SouthCarolinaISS.jpg)

The previously described process was applied to this geographical area. `createdataset.py` downloaded 1190 images between 2000 and 2023 at a 7-day interval. The resulting dataset was converted into *.xlsx* format, and we used MS Excel to plot the data. These graphs, that show the evolution of vegetation and water area in *m<sup>2</sup>* and NDVI, are an example:

![Water-vegetation area](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Pictures/WaterVegetation.jpg)
![Water-NDVI](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Pictures/WaterNDVI.jpg)

At this point, we were still considering if it was better to use a recurrent LSTM (Long Short-Term Memory) neural network or a statistical model for the predictions; but the evident yearly seasonality, which we expected to see, pointed us towards a SARIMAX model (Seasonal Autoregressive Integrated Moving Average) as we thought it would be faster to implement than a properly optimised LSTM neural network.\
Eventually, we realised that the predictions of the SARIMA model were not accurate enough with the default hyperparameters set to 1, so we implemented a grid search to find better ones. But this solution required hundreds of iterations, of possible combinations to be tested. Since going back to the neural network would have pushed us beyond the deadline, this led us to the genetic algorithm, which is less consistent but grants some degree of optimisation in few iterations. And it worked out: with only two generations, the accuracy of the model increased by *4%*, and in the case of South Carolina, the root-mean-square error dropped to just *1.8%*.\

After that, we went on and evaluated the correlation between the data with [`correlation.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/correlation.py) and also examined more in depth the evolution of each parameter by analysing the dataset with Excel and Visual Basic to perform a regression analysis.
For example, we isolated the data in monthly groups, therefore eliminating the seasonality and just seeing the general trend of the mean NDVI for each month:

![mean NDVI](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Pictures/meanNDVI.jpg)

And NDWI:

![mean NDWI](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Pictures/meanNDWI.jpg)

---
## Issues
There were many outliers in our dataset: it can be seen in the spikes and peaks in the graphs. We found out that the some of the pictures that we were getting from the MODIS Google Earth Engine API dataset presented in seemingly random areas some black patches, groups of pixels that were set to 0. We were not able to explain the reason for this, as all three of the colour bands were there and we did not have the opportunity to study a possible relation of these black areas with particular features of the image.

---
## Findings
### Data analysis
We were able to detect changes in the vegetation and in the water area. The mean NDVI showed a *3%* increase over the course of 23 years in our regression analysis. Unfortunately, we could not see any relevant variation in the sea level, but this is very likely to be due to the fact that the rate of change is smaller than the resolution of the AstroPi camera at the altitude of the ISS (which equates to more than *130 m/px*).
### SARIMAx model
We managed to make predictions with a root-mean-square error of only 1.8% of the vegetation area of the part of South Carolina that we considered.
### Correlation
We found a weak but plausible correlation between the mean NDWI and the vegetation area, which is indicated by the results of `correlation.py`: it found a *Kendall's τ* of *0.3338717* and a *p-value* of *4.04⋅10<sup>-67</sup>*

---
## Conclusion
Despite these issues, we were able to accurately predict the evolution of the
considered areas using the SARIMA model and we found a possible correlation
between the NDWI and the area covered by vegetation. Therefore, we think we can consider our experiment a success, as we accomplished every goal that we had set beforehand.
