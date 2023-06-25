from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error
from itertools import product
from datetime import datetime
from pandas import read_csv
from pathlib import Path
from math import sqrt
import pandas as pd
import numpy as np
import os

# get parent folder
baseFolder = Path(__file__).parent.resolve()

# parameters
interval = 7 # average number of days between data
fileName = "dataset.csv" # path to the CSV dataset
column = 6 # select the column of the dependent variable that will be analysed:
# 2 = area covered by water
# 3 = lakes surface area
# 4 = sea surface area
# 5 = vegetation surface area
# 6 = mean NDWI
# 7 = mean NDWI for lakes
# 8 = mean NDWI for the sea/ocean
# 9 = mean NDVI
# 10 = percentage of vegetation

def main():
    # make sure that the parameters are correctly considered global
    global interval
    global fileName
    global column

    try:
        # get the data from the csv file
        # index_col = 0 sets the date as the independent variable
        data = read_csv(str(baseFolder) + "/" + fileName, header = 0, index_col = 0, parse_dates = True)
        n = len(data)

        # if the dataset is not empty
        if (n > 0):
            print("CSV file read successfully")

            # select the entire column with the wanted index
            data = data.iloc[:, column]

            # correct anomalies in the dataset by replacing outliers
            data = correct(data)

            # split the dataset into two different datasets
            n = len(data)
            train = data.iloc[:int(n * 0.75)] # isolate the initial 75% for training
            test = data.iloc[int(n * 0.75):] # select the final 25% for testing

            # define the default SARIMA (Seasonal AutoRegressive Integrated Moving Average) parameters
            # sarimaModel = SARIMAX(trainingData, (p, d, q), (P, D, Q, S)); where:
            # trainingData: training dataset
            p = 1 # trend autoregression order
            d = 1 # trend difference order
            q = 1 # trend moving average order
            P = 1 # seasonal autoregressive order
            D = 1 # seasonal difference order
            Q = 1 # seasonal moving average order
            # S: the repetition frequency of seasonal variations (calculated later)
            hyperparams = np.array([p, d, q, P, D, Q])

            # load the hyperparameters from a file if possible, presumably from the grid search program or the genetic algorithm
            listPath = "hyperparams.npy"
            # check if the file exists
            if os.path.exists(listPath):
                # load the array from the file
                loadedArray = np.load(listPath)
                # check if the array is 6 long
                if (len(loadedArray) == 6):
                    # assign the values loaded to the hyperparameters array
                    hyperparams = loadedArray
                    print("Hyperparameters successfully loaded from file")
                else:
                    print("An array of invalid length was loaded. Using default hyperparameters instead")
            else:
                print("Hyperparameters file not found. Using default hyperparameters instead")
            
            # define the SARIMA (Seasonal AutoRegressive Integrated Moving Average) model
            # sarimaModel = SARIMAX(trainingData, (p, d, q), (P, D, Q, S))
            S = int(365 / interval) # S is 365 / interval as the seasonal cycle of the data we are working with is yearly (365 days)
            model = SARIMAX(train, order = (hyperparams[0], hyperparams[1], hyperparams[2]), seasonal_order = (hyperparams[3], hyperparams[4], hyperparams[5], S))

            # fit the model on the data and show the output
            fitModel = model.fit(disp = True)

            # make predictions with the testing dataset to evaluate the goodness of the model
            predictions = fitModel.predict(start = len(train), end = len(train) + len(test) - 1)

            # calculate the root mean square deviation
            rmse = sqrt(mean_squared_error(test, predictions))
            print("RMSE:", rmse)
        else:
            print("The selected dataset was empty")
            return -1
    except Exception as e:
        print("An error occurred:", str(e))
        return -1
    return 0

# identifies the outliers by their interquartile range and replaces them
def correct(data):
    # find the first and the third quartile and the interquartile range
    q1 = data.quantile(0.75)
    q3 = data.quantile(0.25)
    iqr = q3 - q1

    # set the bounds as 1.75 times the interquartile range above and under the first and third quartiles
    lower = q1 - (iqr * 1.75)
    upper = q3 + (iqr * 1.75)

    # replace the outliers by capping
    # if the value is beyond the bounds, replace it with the value of the bound itself, otherwise keep it unchanged
    correctedData = np.where(data < lower, lower, data)
    correctedData = np.where(correctedData > upper, upper, correctedData)
    
    # make a new DataFrame with the corrected data
    data = pd.Series(correctedData, index = data.index)
    return data

if __name__ == "__main__":
    main()