
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
In short, what we needed to do was:
- Find an area that suits our research, based on the analysis we did on the CSV data in MS Excel
- Download a set of NIR satellite pictures from the internet and edit them to roughly simulate what we would get by running our [phase 2 program](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/tree/main/Phase_1-3) for a long period of time (years)
- Perform the necessary NDVI and NDWI calculations and masking to extract a dataset of relevant parameters from the images
- Use the dataset to:
	-  train a model and make predictions with it
	- find out if the vegetation area and the water area are correlated
	- see if we could measure the effects of climate change on lakes and coasts

And we wanted to achieve all of this with an automatic process, with us writing our own code that would do everything, instead of using premade tools such as QGIS either manually (which would have been impossible) or automatically.\
This is the process we came up with:
- A program called [`createdataset.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/createdataset.py) calls the [*Google Earth Engine API*](https://earthengine.google.com/) to download satellite images in *OpenCV* format of a certain location at a determined interval of days between two dates. It takes each image and finds its NDVI, NDWI and the different masks that it then uses to estimate the **actual area** each mask corresponds to on the Earth's surface. At the end, it writes all of the data in a *CSV* file for analysis. The paramaters needed, such as the date boundaries, the equivalent altitude of the ISS for the picture and the coordinates, are loaded from specific files that can be copied to same folder as the program. If they are not present, default parameters defined in the source code are used.\
Initially, we wanted to use high resolution imagery from [Sentinel](https://developers.google.com/earth-engine/datasets/catalog/sentinel) and [Landsat](https://developers.google.com/earth-engine/datasets/catalog/landsat), but their images were too small to cover the field of view of the AstroPi camera. The script [`multiearth.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/multiearth.py) was supposed to use them to take as many pictures as possible within each time interval, with the reasonably lowest cloud coverage, and merge them together - with a process called mosaicing - in order fill up the entire area. Unfortunately, Sentinel and Landsat could not provide the degree of availability that we needed. Even collecting one month of pictures, the mosaic was mainly black when the cloud percentage threshold was low; and when we raised it, the images were completely covered by clouds in a different way in each segment of the total image. This meant that if we used these mosaics for our analysis, we would have gotten either way extremely inconsistent results.
For this reason, the final program `createdataset.py` takes the images between February 2000 and February 2023 from the [MODIS dataset](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD43A4), which has a much lower resolution but a wider area and a daily availability without clouds.
- At this point, there is a *CSV* file containing in each line the date, the water area, vegetation area and other data from each image. This is the dataset that will be used by the following programs.
- [`correlation.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/correlation.py) tries to establish if there is any correlation between any of the possible combinations in which two parameters from the dataset can be picked. This program extracts two columns from the *CSV* file and calculates the cross-correlation and the Kendall's τ of the two data series.
- The dataset is then used by [`sarima.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/sarima.py), which reads one of the columns, trains a SARIMA statistical model, makes predictions and calculates its root-mean-square error to evaluate the accuracy of the model.\
The hyperparameters of the SARIMA model are all set to 1 by default, but they can be optimised by running [`genetictraining.py`](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/main/Phase_4/genetictraining.py), which takes the same dataset and uses a genetic algorithm to find the best hyperparameters and save them as a Numpy array file (`hyperparams.npy`). If `sarima.py` finds this file in its folder, it automatically retrieves the optimal hyperparameters from it.\
The individuals of the genetic algorithm represent a SARIMA model with their properties being the hyperparameters of the model. The algorithm works by creating an initial generation with random parameters and then going through each generation by selecting and breeding the best individuals in order to get the following generation through mating and mutation. The fitness of each individual is determined by training their respective SARIMA and evaluating its root-mean-square error, which has to be as low as possible.
