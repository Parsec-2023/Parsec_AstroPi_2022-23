from statsmodels.tsa.statespace.sarimax import SARIMAX
from deap import base, creator, tools, algorithms
from sklearn.metrics import mean_squared_error
from datetime import datetime
from pandas import read_csv
from pathlib import Path
from math import sqrt
import pandas as pd
import numpy as np
import random

# get parent folder
baseFolder = Path(__file__).parent.resolve()

# parameters
interval = 7 # average number of days between data
fileName = "dataset.csv" # path to the CSV dataset
initialPopulation = 25 # initial population of the genetic algorithm
generations = 5 # number of generations for the genetic algorithm
matingProb = 0.5 # probability of mating between individuals
mutationProb = 0.25 # probability of mutation of each generation
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
    # make sure that all parameters are correctly considered global
    global fileName
    global initialPopulation
    global generations
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

            # define the SARIMA (Seasonal AutoRegressive Integrated Moving Average) model
            # sarimaModel = SARIMAX(trainingData, (p, d, q), (P, D, Q, S)); where:
            # trainingData: training dataset
            # p: trend autoregression order
            # d: trend difference order
            # q: trend moving average order
            # P: seasonal autoregressive order
            # D: seasonal difference order
            # Q: seasonal moving average order
            # S: the repetition frequency of seasonal variations

            # genetic optimisation
            # take the parameters of the best individual of a genetic algorithm with given starting population and generations
            p, d, q, P, D, Q = geneticSARIMA(train, test, initialPopulation, generations)

            # save the hyperparameters array to a file
            np.save("hyperparams.npy", np.array([p, d, q, P, D, Q]))
            print("p:", p, "d:", d, "q:", q, "P:", P, "D:", D, "Q:", Q)
        else:
            print("The selected dataset was empty")
            return -1
    except Exception as e:
        print("An error occurred:", str(e))
        return -1
    return 0


def geneticSARIMA(train, test, pop0, gens):
    # make sure that all parameters are correctly considered global
    global matingProb
    global mutationProb

    # define the problem as the minimisation of a function (the root mean square deviation of the model predictions in this case)
    creator.create("FitnessMin", base.Fitness, weights = (-1.0,))
    creator.create("Individual", list, fitness = creator.FitnessMin)
    # generate random hyperparameter attributes in range(0, 3)
    toolbox = base.Toolbox()
    toolbox.register("p", random.randint, 0, 2)
    toolbox.register("d", random.randint, 0, 2)
    toolbox.register("q", random.randint, 0, 2)
    toolbox.register("P", random.randint, 0, 2)
    toolbox.register("D", random.randint, 0, 2)
    toolbox.register("Q", random.randint, 0, 2)
    # set up the individual with its parameters and the population
    # each individual is a SARIMA model
    toolbox.register("individual", tools.initCycle, creator.Individual, (toolbox.p, toolbox.d, toolbox.q, toolbox.P, toolbox.D, toolbox.Q), n = 1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    # give the toolbox the datasets to use for the evaluation function
    toolbox.register("evaluate", evaluateModel, train = train, test = test)
    toolbox.register("mate", tools.cxTwoPoint)
    # the mutation has to be within the range(0, 3) with a probability of 0.25
    toolbox.register("mutate", tools.mutUniformInt, low = 0, up = 2, indpb = 0.25)
    toolbox.register("select", tools.selTournament, tournsize = 3)
    # set the starting population
    population = toolbox.population(pop0)
    # the hall of fame will contain the best model of each generation
    hof = tools.HallOfFame(1)
    # set the statistical evaluation of the fitness
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", np.min)
            
    # run the algorithm with certain mating probability, mutation probability and number of generations
    population, _ = algorithms.eaSimple(population, toolbox, cxpb = matingProb, mutpb = mutationProb, ngen = gens, stats = stats, halloffame = hof, verbose = True)

    # return the best individual
    print("Best individual: ", hof[0], hof[0].fitness)
    return hof[0]

def evaluateModel(individual, train, test):
    global interval

    # extract the hyperparameters
    p, d, q, P, D, Q = individual
    S = int(360 / interval) # calculate the seasonality
    try:
        # define the model
        model = SARIMAX(train, order = (p, d, q), seasonal_order = (P, D, Q, S))
        # train the model
        fitModel = model.fit(disp = False)
        # make predictions and calculate the root mean square deviation as a method of evaluating this particular model
        predictions = fitModel.predict(start = len(train), end = len(train) + len(test) - 1)
        rmse = sqrt(mean_squared_error(test, predictions))
        return (rmse,)
    except:
        # return an infinite root mean square deviation if anything goes wrong
        return (np.inf,)

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