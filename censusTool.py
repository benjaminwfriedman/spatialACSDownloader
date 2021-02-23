import pandas as pd
import numpy as np
import geopandas as gpd
import requests
import json

lookup = pd.read_csv("./county_fips_master.csv", encoding='gbk')
def getStateCode(state_abr, county_name):
    state_df = lookup[lookup['state_abbr'] == state_abr]
    county_df = state_df[state_df['county_name'] == county_name]
    stateCode_raw = county_df['state'].values
    print(stateCode_raw)
    if stateCode_raw < 2:
        stateCode = "0" + str(int(stateCode_raw))
    else:
        stateCode = str(int(stateCode_raw))
    print(stateCode)
    return stateCode

def getCountyCode(state_abr, county_name):
    state_df = lookup[lookup['state_abbr'] == state_abr]
    county_df = state_df[state_df['county_name'] == county_name]
    countyCode_raw = county_df['county'].values
    countyCode = "0" + str(int(countyCode_raw))
    if len(countyCode) < 3:
        countyCode = "0" + countyCode
    return countyCode

print('Welcome to the county level Census GIS extractor for ACS data')
print('This system was built by Benny Friedman')


print('What state would you like to pull data for?')
state_abr = input('Examples: CA, NY, CT --> ')

state_subset = lookup[lookup['state_abbr'] == state_abr]
examples_counties = state_subset.head(3)['county_name'].tolist()
examples_counties_string = ", ".join(examples_counties)
print('What county would you like to pull data for?')
county_name = input("Examples: {} --> ".format(examples_counties_string))

print("What years data are you interested in?")
year = input('Examples: 2015, 2016, 2017, 2018, ect. --> ')

print("What variables would you like to pull?")
print(" ")
print("For a list of variables visit https://api.census.gov/data/2015/acs/acs5/profile/variables.html")
variables_entered = input('Type a list of variables you would like separated by a space --> ')

print("Where would you like to save the shapefile to?")
save_folder = input("Example: F:\Projects\censusTool --> ")


variables = variables_entered.split()
variables.insert(0, "NAME")


variables_str = ",".join(variables)
state = getStateCode(state_abr, county_name)
county = getCountyCode(state_abr, county_name)
url = "https://api.census.gov/data/{}/acs/acs5/profile?get={}&for=tract:*&in=state:{}&in=county:{}".format(year, variables_str, state, county)
print(url)

print('Pulling the Census Data Now ........')
r = requests.get(url)
try:
    data = r.json()
except:
    print(r.text)
data_no_head = data[1:]
data_df = pd.DataFrame(data_no_head, columns=data[0])
data_df.rename(columns = {'tract':'TRACT'}, inplace = True)

for var in variables_entered.split():
    data_df[var] = data_df[var].astype(float)

geo_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/10/query?where=STATE+%3D+%27{}%27+AND+COUNTY+%3D+%27{}%27&text=&objectIds=&time=&geometry=&geometryType=esriGeometryPolygon&inSR=&spatialRel=esriSpatialRelIntersects&relationParam=&outFields=TRACT&returnGeometry=true&returnTrueCurves=false&maxAllowableOffset=&geometryPrecision=&outSR=&returnIdsOnly=false&returnCountOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&gdbVersion=&returnDistinctValues=false&resultOffset=&resultRecordCount=&queryByDistance=&returnExtentsOnly=false&datumTransformation=&parameterValues=&rangeValues=&f=pjson".format(state, county)
print("")
print("Pulling spatial data ........")
try:
    geor = requests.get(geo_url)
except:
    print("Looks like the gis server failed to connect")
    print("")
    print("This happens sometimes. Please re run the tool.")
print("")
print("Data found --- Creating Shapefile ........")
print("This may take a second ........")
print("---Alchemizing spatialized data")
geodata = geor.json()
print("---Saving recipe")
with open('./gisData.geojson', 'w') as f:
    json.dump(geodata, f)
print('---Regenerating')
geo_df = gpd.read_file('./gisData.geojson')
print('---Combination initialized')
final_df = pd.merge(geo_df, data_df, how='left', on='TRACT')
input_path = save_folder + "/ACSData{}{}{}_{}.shp".format(year, state_abr, county_name.replace(" ", "_"), "__".join(variables))
print("Saving file to {}".format(input_path))
final_df.to_file(driver = 'ESRI Shapefile', filename = input_path)

print("Process Finished")
