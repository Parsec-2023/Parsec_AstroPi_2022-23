from statsmodels.tsa.stattools import ccf
from scipy.stats import kendalltau
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import pandas as pd

# get parent folder
baseFolder = Path(__file__).parent.resolve()

# parameters
interval = 7 # average number of days between data
fileName = "dataset.csv" # path to the CSV dataset
col0, col1 = 2, 9 # columns of interest
# 2 = area covered by water
# 3 = lakes surface area
# 4 = sea surface area
# 5 = vegetation surface area
# 6 = mean NDWI
# 7 = mean NDWI for lakes
# 8 = mean NDWI for the sea/ocean
# 9 = mean NDVI
# 10 = percentage of vegetation

# get the data from the csv file
# index_col = 0 sets the date as the independent variable
data = pd.read_csv(str(baseFolder) + "/" + fileName, header = 0, index_col = 0, parse_dates = True)

# extract the columns of interest
series1 = data.iloc[:, col0]
series2 = data.iloc[:, col1]

# calculate the cross correlation
crossCorrelation = ccf(series1, series2)

# calculate Kendall's tau
correlation, p = kendalltau(series1, series2)
print("Kendall correlation:", correlation)
print("p-value:", p)

# plot the cross correlation
fig, ax = plt.subplots(figsize=(10,6))
ax.plot(crossCorrelation)
ax.set_title('Cross-Correlation')
ax.set_xlabel('Lag')
ax.set_ylabel('Cross-Correlation')
plt.show()