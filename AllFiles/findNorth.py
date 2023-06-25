import csv
import math
from geographiclib.geodesic import Geodesic
from geographiclib.geomagnet import Geomagnet

def calculate_magnetic_declination(latitude, longitude):
    geomagnet = Geomagnet.WMM2020()
    result = geomagnet(latitude, longitude)
    return result['declination']

def calculate_azimuth(mx, my, mz, declination):
    azimuth = math.degrees(math.atan2(my, mx)) + declination
    if azimuth < 0:
        azimuth += 360
    return azimuth

def main():
        lat = 13.80134278212
        lon = -62.425268567292
        mx = -15.923366546631
        my = 13.958372116089
        mz = 21.240356445312
        declination = calculate_magnetic_declination(lat, lon)
        azimuth = calculate_azimuth(mx, my, mz, declination)
        print(f"Lat: {lat}, Lon: {lon}, Azimuth: {azimuth}")

if __name__ == "__main__":
    main()