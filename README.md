
# [Parsec-AstroPi](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23)
**2022-2023**  
Team name: Parsec  
School: *[Liceo Scientifico "Leonardo da Vinci", Gallarate (VA), IT](https://goo.gl/maps/iJFNK38aVivM7PgVA)*  
Mentor: Lucia Polidori  
Members: Daniele Nicolia, Davide Pascu, Matteo Saporiti, Leonardo Simonetti, Federico Sozzi, Jad Taljabini  
***
# PHASE 4
During the three hour period on the ISS, [our program](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/tree/Phases_1-3) collected 605 pictures and 2272 lines of data in a CSV file.\
Of course, for half of the time we could not take pictures, as the ISS has a day cycle of 1.5 hours and it stays in the darkness of the night for this amount of time. We were quite lucky it passed over the USA, Porto Rico, Suriname and part of  on one "ISS-day" and over Canada and South Africa on the other.

![ISS trajectory](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/blob/3f93436504f8ce1ca5792ef3d068ba0a12a871b9/Trajectory.PNG)

For phase 4, we had to analyse this data: we wanted to see if there was any correlation between the area of land covered by vegetation and the surface area of lakes in the same region, or if we could implement a machine learning model - or anything similar in functionality - capable of taking satellite images (like we did with the [phase 2 program](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/tree/Phases_1-3)) and predicting the future variations of parameters linked to the environment and climate change, such as vegetation area, vegetation health, area covered by water, etc...\
***
## The process
In short, what we needed to do was:
- Find an area that suits our research, based on the analysis we did on the CSV data in MS Excel
- Download a set of NIR satellite pictures from the internet and edit them to roughly simulate what we would get by running our [phase 2 program](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23/tree/Phases_1-3) for a long period of time (years)
- Perform the necessary NDVI and NDWI calculations and masking to extract a dataset of relevant parameters from the images
- Use the dataset to:
	-  train a model and make predictions with it
	- find out if the vegetation area and the water area are correlated
	- see if we could measure the effects of climate change on lakes and coasts

And we wanted to achieve all of this with an automatic process, with us writing our own code that would do everything, instead of using premade tools such as QGIS either manually (which would have been impossible) or automatically.\
This is the process we came up with:
- A program called `createdataset.py` 

made a program that uses Google Earth Engine API to get photos of the most relevant areas from phase 3 from the MODIS dataset between 2000 and 2023 and then generates a CSV file that contains parameters like the area covered by water and vegetation and the mean NDVI and NDWI values throughout each image. This file is then used by a SARIMA statistical model to make predictions of the evolution of such parameters.
The grid search technique proved computationally too expensive, thus the SARIMA model was optimised by running another program that employs a genetic algorithm to find the best hyperparameters for each specific dataset.
