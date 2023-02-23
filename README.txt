**************************************************************************************************************
* Parsec-AstroPi                                                                                             *
* 2022-2023                                                                                                  *
* Team name: Parsec                                                                                          *
* School: Liceo Scientifico "Leonardo da Vinci", Gallarate (VA), IT                                          *
* Mentor: Lucia Polidori                                                                                     *
* Members: Daniele Nicolia, Davide Pascu, Matteo Saporiti, Leonardo Simonetti, Federico Sozzi, Jad Taljabini *
*                                                                                                            *
**************************************************************************************************************

______________________________________________________________________________________
THE FULL DOCUMENTATION IS ON GitHub: https://github.com/Federi0411-0684/Parsec-AstroPi
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯

Our project
Abstract
Our project aims to determine whether and how much drainage basins, rivers, lakes, glaciers, and coasts have changed in the last decades due to climate change.
The parameters we are going to focus on are the area covered by water, the shape of the water stream, and possibly, the amount of water provided to the surrounding land; this last aspect, which will be estimated considering vegetation health (that is an effect of the quantity of water received) will allow us to understand also how much water the stream supplies to the surrounding environment and consequently how the evolution of the water stream modifies the environment itself.
The final destination of our research is to use the collected data to study possible links with climate change and predict how the observed sites will change in the future, considering possible effects on the landscape and the local population.
Our program makes use of computer vision techniques combined with NDVI and NDWI to recognise whether the ISS is passing over a relevant landscape and save as many useful images as possible during the three hours on the ISS.

Future Plans for Phase 4
Our plan after Phase 3, assuming we get flight status, is to use the pictures that we collect on the ISS and the NIR satellite image datasets that can be found on the Internet to train a machine learning model capable of predicting the future water and vegetation coverage of a certain area, based on the past and current images of that area, taking into account seasonal variations and other factors.

__________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________

The software
The main function of our program is to take pictures of the Earth's surface as frequently as possible, only saving to memory the relevant ones.
We have made extensive use of try-except statements to make sure that the program will not stop before it is needed, and we have implemented an intricate logging system that, in case anything goes wrong, will tell us the cause of the problem.
We tried to follow good coding practices, writing the code as readable as possible, and especially ensuring to keep a certain level of optimisation and safety during runtime.
The most significant features of our program are:

- NDVI and NDWI calculation.
- Algorithmic image segmentation to detect vegetation and land in the image and only save the pictures that contain land, excluding those that are all ocean or clouds.
  Note: we initially wanted to use machine learning to perform image segmentation, we had also implemented a U-Net convolutional neural network, but we did not find any datasets for the segmentation of NIR satellite images.
  To train it we would have had to make our own dataset of segmented images, which meant painting hundreds or thousands of NIR satellite images by hand. We concluded that it would take us much less time to make an algorithm that does the same job, which is what we did, and it works just fine.
- Image cropping to save storage.

