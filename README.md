# public-transport-analysis
Urban Public transport analysis.
This repository contains a jupyter notebook and all the related libraries to perform some of the analisys shown in the <a href="https://www.authorea.com/199720/EQyHdOQnAA9722V0RLA35A" target="_blank">article</a> and in the <a href="http://citychrone.org" target="_blank">CityChrone platform</a>.

Take a look at the <a href="http://nbviewer.jupyter.org/github/ocadni/public-transport-analysis/blob/master/public-transport-city.ipynb" target="_blank">demo</a> of the notebook for the city of Budapest.

![budapest image](./budapest.png)

## Prerequisites
1. [python 3.x](https://www.python.org/download/releases/3.0/)
1. [jupyter](http://jupyter.org/)
1. [MongoDB](https://www.mongodb.com/download-center#community) with the privileges to create and modified a database.
1. An [osrm-backend](https://github.com/Project-OSRM/osrm-backend) server for computing the walking path.
1. All the python library needed, listed at the beginning of the notebook.

## installation
1. clone the repository.
1. Download [openstreetmap](openstreetmap.org) extract (the .pbf file) of the city/region of interest. ->[repository of osm extract: [geofabrik](http://download.geofabrik.de/) -- [mapzen](https://mapzen.com/data/metro-extracts/]).
1. Save the extract in the folder "osrm" of the current repository. Run on the terminal in osrm folder (Compile the street graph and run the osrm backend):
	1. ```osrm-extract -p ./profiles/foot.lua budapest_hungary.osm.pbf```
	1. ```osrm-contract budapest_hungary.osm.pbf```
	1. ```osrm-routed budapest_hungary.osrm --port 5000```
5. run ```jupyter-notebook``` and open the public-transport-analysis notebook.
6. Set the variable listed at the start of the notebook:
	1. ```city = 'Budapest' # name of the city```
	2. ```urlMongoDb = "mongodb://localhost:27017/"; # url of the mongodb database```
	3. ```directoryGTFS = './gtfs/'+ city+ '/' # directory of the gtfs files.```
	4. ```day = "20170607" #hhhhmmdd [date validity of gtfs files]```
	5. ```dayName = "wednesday" #name of the corresponding day```
	6. ```urlServerOsrm = 'http://localhost:5000/'; #url of the osrm server of the city```
7. run until the end the notebook.




