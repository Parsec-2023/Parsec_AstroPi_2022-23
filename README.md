# [Parsec-AstroPi](https://github.com/Parsec2k23/Parsec_AstroPi_2022-23)
**2022-2023**  
Team name: Parsec  
School: *[Liceo Scientifico "Leonardo da Vinci", Gallarate (VA), IT](https://goo.gl/maps/iJFNK38aVivM7PgVA)*  
Mentor: Lucia Polidori  
Members: Daniele Nicolia, Davide Pascu, Matteo Saporiti, Leonardo Simonetti, Federico Sozzi, Jad Taljabini  
***
# PHASE 4
For phase 4, we made a program that uses Google Earth Engine API to get photos of the most relevant areas from phase 3 from the MODIS dataset between 2000 and 2023 and then generates a CSV file that contains parameters like the area covered by water and vegetation and the mean NDVI and NDWI values throughout each image. This file is then used by a SARIMA statistical model to make predictions of the evolution of such parameters.
The grid search technique proved computationally too expensive, thus the SARIMA model was optimised by running another program that employs a genetic algorithm to find the best hyperparameters for each specific dataset.

