# Parsec-AstroPi
**2022-2023**
Team name: Parsec
School: *[Liceo Scientifico "Leonardo da Vinci", Gallarate (VA), IT](https://goo.gl/maps/iJFNK38aVivM7PgVA)*
Mentor: Lucia Polidori
Members: Daniele Nicolia, Davide Pascu, Matteo Saporiti, Leonardo Simonetti, Federico Sozzi, Jad Taljabini
***
# Our project
## Abstract
Our project aims to determine whether and how much drainage **basins**, rivers, **lakes**, glaciers, and coasts have changed in the last decades due to **climate change**. The parameters we are going to focus on are the area covered by water, the shape of the water stream, and the amount of water provided to the surrounding land: the latter will be estimated considering vegetation health (which depends on the quantity of water received) and will allow us to understand how much water the stream supplies to the surrounding environment and consequently how the evolution of the water stream modifies the environment itself. The final destination of our research is to use the collected data to study possible links with climate change and **predict** how the observed sites will change in the future, considering possible effects on the landscape and on the local population.

# The software
The main function of our program is to take pictures of the Earth's surface as frequently as possible, only saving to memory the ones that are relevant. We have made extensive use of try-except statements to make sure that the program will not stop before it is needed, and we have implemented an intricated logging system that, in case anything goes wrong, will tell us the cause of the problem. We tried to follow a good coding practice, writing the code as readable as possible, and especially ensuring to keep a certain level of optimisation and safety during runtime.

## Structure
Our program is structured as follows:
- Initialise the first objects, such as the starting time of the program, the *Sense Hat*; get the path of the containing folder;
- Open the *log* file or create it if it does not exist;
- The header of the *csv* file is defined at the beginning of the main function;
- The *csv* file for saving the data collected by the *Sense Hat* is opened or created if it does not exist;
- A folder to contain the pictures, `...\Pictures`, is created if it does not exist;
- The *csv writer* and the *PiCamera* are initialised;
- Create some variables that will be needed later;
- Start a *while* loop that cycles continuously for 2 hours, 57 minutes and 30 seconds *(2:57:30)* `now < (startTime + timedelta(hours = 2, minutes = 57, seconds = 30))`;
	- Enter an if statement every 3 seconds or more, depending on how much free memory out of the 3GB is left and how much time remains. This time interval will be calculated at the end of the loop;
		- Check if the ISS is over a sunlit area (`ISS.at(load.timescale().now()).is_sunlit(ephemeris)`): if not, only data will be collected and no picture will be taken;
		- Set EXIF data of the next picture according to the current location of the ISS;
		- Take a picture with the *PiCamera*, saving it to a temporary path, overwriting the old one;
		- Open this picture as an *OpenCV* image and scale it down in order to make the following operations faster;
		- Use a computer vision algorithm that we have developed (which is implemented in the function `segmentation(image)` to get a **segmented** image from the picture that has just been taken;
		- This allows us to choose whether this picture should be permanently saved, by calculating a score that is based on the percentage of green and red pixels (respectively representing vegetation and generic landmass) in the segmented image;
			- If the score is high enough, the picture is **cropped** around the edge of the window of the ISS to save as much storage space as possible. This operation is performed by another *cv* algorithm - of which we are quite proud - that isolates the bright circle of the window, finds the border, and crops the image accordingly;
			- The cropped image is saved;
			- The EXIF data that was previously saved in the temporary image by *PiCamera* is copied to the newly saved final image, completing this long process of segmenting and cropping the picture;
			- Calculate a new time interval to wait before taking the next picture. This value is estimated by keeping track of the occupated storage space and the remaining time:
				> - The remaining space is the total allowed space minus the current space taken up by the '...\Pictures' folder: $maxSpace - currentSpace = 2975000000 - picFolderSize$
				> - The remaining time is the time the program is expected to end minus the current time: `remaining_time = end_time - now = start_time + program_time - current_time`
