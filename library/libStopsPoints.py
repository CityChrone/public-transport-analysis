import pymongo as pym
import time
import requests
import os
import zipfile
import pandas as pd
import folium
import numpy as np
import math

def loadGtfsFile(gtfsDB, directoryGTFS, city, listOfFile):
    for nameC in listOfFile:
        #pass
        #gtfsDB.drop_collection(nameC[:-4])
        if(nameC[:-4] in gtfsDB.collection_names()): gtfsDB[nameC[:-4]].delete_many({'city':city})
        print('removing', nameC[:-4], ' of ', city)

    stopsListInit = []
    for filename in os.listdir(directoryGTFS):
        if filename.endswith(".zip"):
            archive = zipfile.ZipFile(directoryGTFS + filename, 'r')
            print(filename)
            for nameCSVFile in listOfFile:
                collGtfs = gtfsDB[nameCSVFile[:-4]]
                if nameCSVFile in archive.namelist(): 
                    #try:
                    lines = archive.open(nameCSVFile, mode='r')
                    res = pd.read_csv(lines,encoding = 'utf-8-sig', dtype=str)
                    res["city"] = city
                    res["file"] = filename
                    res = list(v for v in res.to_dict("index").values())               
                    if len(res) != 0:
                        collGtfs.insert_many(res)                
                    print('{2} -> ({0},{1})'.format(len(res),collGtfs.find({'city':city}).count(),nameCSVFile))
    for name in listOfFile:
        gtfsDB[name[:-4]].create_index([("city", pym.ASCENDING)])
    if 'trips.txt' in listOfFile:
        gtfsDB['trips'].create_index([("trip_id", pym.ASCENDING)])
        gtfsDB['trips'].create_index([("service_id", pym.ASCENDING)])
        gtfsDB['trips'].create_index([("city", pym.ASCENDING)])

def removingStopsNoConnections(gtfsDB, city):
    count_rem = {}
    count = 0
    for stop in gtfsDB['stops'].find({'city':city}).sort([('_id', pym.ASCENDING)]):
        countPStart = gtfsDB['connections'].find({'city':city,'file':stop['file'],'pStart':stop['stop_id']}).count()
        countPEnd = gtfsDB['connections'].find({'city':city,'file':stop['file'],'pEnd':stop['stop_id']}).count()
        if countPStart == 0 and countPEnd == 0:
            gtfsDB['stops'].delete_one({'_id':stop['_id']})
            if stop['file'] in count_rem:
                count_rem[stop['file']] += 1
            else:
                count_rem[stop['file']] = 1

        print( '{0}-removed stops{1}'.format(count, count_rem),end="\r")
        count += 1


def setPosField(gtfsDB, city):
    pos = 0
    for stop in gtfsDB['stops'].find({'city':city}).sort([('_id', pym.ASCENDING)]):
        gtfsDB['stops'].update_one({'_id':stop['_id']},
                                   {'$set':
                                       {
                                        'pos':pos,
                                        'point':
                                        { 'type': "Point" , 'coordinates': [float(stop['stop_lon']), float(stop['stop_lat'])]}
                                       }
                                   });
        pos += 1
        print ('{0}'.format(pos),end="\r")
    gtfsDB['stops'].create_index([("pos", pym.ASCENDING)])
    gtfsDB['stops'].create_index([("point", pym.GEOSPHERE)])

def returnStopsList(gtfsDB, city):
    stopsList = []
    count_err = 0
    for stop in gtfsDB['stops'].find({'city':city}):
        #if('stop_id' not in stop.keys()): print stop
        try: 
            stopsList.append([stop['stop_id'], float(stop['stop_lat']), float(stop['stop_lon']), stop['file']])
        except KeyError:
            count_err += 1
            print (stop)
            break
    print ('tot stop', len(stopsList),' stop error :', count_err)
    return stopsList

def boundingBoxStops(stopsList):
    minLat = +200
    minLon = +200
    maxLat = -200
    maxLon = -200
    for stop in stopsList:
        try:
            minLat = min(minLat, float(stop[1]))
            minLon = min(minLon, float(stop[2]))
            maxLat = max(maxLat, float(stop[1]))
            maxLon = max(maxLon, float(stop[2]))
        except:
            print (stop)
    return [minLon,maxLat,maxLon,minLat]

from math import cos
from folium.plugins import FastMarkerCluster
def mapStops(bbox, stopsList):
    minLat = bbox[3]
    minLon = bbox[0]
    maxLat = bbox[1]
    maxLon = bbox[2]
    listpoint =[[maxLat,minLon], [maxLat,maxLon],[minLat,maxLon],[minLat,minLon], [maxLat,minLon]]
    listpoint = [ [float(x[0]), float(x[1])] for x in listpoint]
    latlon = [(listpoint[0][0] + listpoint[2][0])/2, (listpoint[0][1] + listpoint[2][1])/2]
    map_stops = folium.Map(location = latlon, zoom_start=10)
    line = folium.PolyLine(listpoint)
    map_stops.add_child(line)
    markerList =[]
    for aa in stopsList:
        markerList.append([aa[1],aa[2]])
    points = FastMarkerCluster(markerList, None).add_to(map_stops)
    return map_stops

def computeNeigh(gtfsDB, urlServerOsrm, distanceS, tS, city):
    
    hexTemp = gtfsDB['points']
    url = urlServerOsrm + "table/v1/foot/";
    avgNeightS = 0 
    avgNeightP = 0
    tot = gtfsDB['stops'].find({'stopN':{'$exists':False},'city':city}).count() + gtfsDB['points'].find({'stopN':{'$exists':False},'city':city}).count()
    #tot = gtfsDB['stops'].find({'city':city}).count() + gtfsDB['points'].find({'city':city}).count()
    count = 0
    avgT = 0
    for stop in gtfsDB['stops'].find({'stopN':{'$exists':False},'city':city}, no_cursor_timeout=True):
    #for stop in gtfsDB['stops'].find({'city':city}, no_cursor_timeout=True):
        timeStart0 = time.time()
        lonLatStart = stop['point']['coordinates'];
        searchNear ={'point' : {'$near': {
                 '$geometry': {
                    'type': "Point" ,
                    'coordinates': lonLatStart
                 },
                 '$maxDistance': distanceS,
                 '$minDistance': 0
                    }},
                    'city':city
                }         
        listStopsNPos = []
        tempUrl = url + '{0:.8f},{1:.8f};'.format(stop['point']['coordinates'][0],stop['point']['coordinates'][1]);
        for stopN in gtfsDB['stops'].find(searchNear):
            lonLatEnd = stopN['point']['coordinates']
            tempUrl += '{0:.8f},{1:.8f};'.format(lonLatEnd[0],lonLatEnd[1]);
            listStopsNPos.append(stopN['pos'])
        #print tempUrl[:-1] + '?sources=0'
        listStopsN = [];
        if(len(listStopsNPos)>0):
            result = requests.get(tempUrl[:-1] + '?sources=0')
            if 'durations' in result.json():
                for i,t in enumerate(result.json()['durations'][0][1:]):
                    if t:
                        if t > 0 and t < tS:
                            listStopsN.append({'pos' : listStopsNPos[i], 'time' : t})
        gtfsDB['stops'].update_one({'_id':stop['_id']},{'$set':{'stopN' : listStopsN}})

        listPointNPos = []
        tempUrl = url + '{0:.8f},{1:.8f};'.format(stop['point']['coordinates'][0],stop['point']['coordinates'][1]);
        for pointN in gtfsDB['points'].find(searchNear):
            lonLatEnd = pointN['point']['coordinates']
            tempUrl += '{0:.8f},{1:.8f};'.format(lonLatEnd[0],lonLatEnd[1]);
            listPointNPos.append(pointN['pos'])
        #print tempUrl[:-1] + '?sources=0'
        listPointN = [];
        if(len(listPointNPos)>0):
            result = requests.get(tempUrl[:-1] + '?sources=0')
            if 'durations' in result.json():
                for i,t in enumerate(result.json()['durations'][0][1:]):
                    if t:
                        if t > 0 and t < tS:
                            listPointN.append({'pos' : listPointNPos[i], 'time' : t})
        gtfsDB['stops'].update_one({'_id':stop['_id']},{'$set':{'pointN' : listPointN}})

        avgNeightS += len(listStopsN)
        avgNeightP += len(listPointN)
        count += 1
        totTime = time.time() - timeStart0
        avgT += totTime
        print ('\r totNumber {0}, computed {1:.2f}%, time to finish : {2:.0f} min'.format(tot-count,
                                  100.*count/tot,
                                 (tot- count)*avgT/(count*60.)), end="\r")

    for point in gtfsDB['points'].find({'pointN':{'$exists':False},'city':city}, no_cursor_timeout=True):
    #for point in gtfsDB['points'].find({'city':city}, no_cursor_timeout=True):
        timeStart0 = time.time()

        lonLatStart = point['point']['coordinates'];
        searchNear ={'point' : {'$near': {
                 '$geometry': {
                    'type': "Point" ,
                    'coordinates': lonLatStart
                 },
                 '$maxDistance': distanceS,
                 '$minDistance': 0
                    }},
                 'city':city
                }         
        listStopsNPos = []
        tempUrl = url + '{0:.8f},{1:.8f};'.format(point['point']['coordinates'][0],point['point']['coordinates'][1]);
        for stopN in gtfsDB['stops'].find(searchNear):
            lonLatEnd = stopN['point']['coordinates']
            tempUrl += '{0:.8f},{1:.8f};'.format(lonLatEnd[0],lonLatEnd[1]);
            listStopsNPos.append(stopN['pos'])
        #print( tempUrl[:-1] + '?sources=0')
        listStopsN = [];
        if(len(listStopsNPos)>0):
            result = requests.get(tempUrl[:-1] + '?sources=0')
            if 'durations' in result.json():
                for i,t in enumerate(result.json()['durations'][0][1:]):
                    if t:
                        if t > 0 and t < tS:
                            listStopsN.append({'pos' : listStopsNPos[i], 'time' : t})
        gtfsDB['points'].update_one({'_id':point['_id']},{'$set':{'stopN' : listStopsN}})

        listPointNPos = []
        tempUrl = url + '{0:.8f},{1:.8f};'.format(point['point']['coordinates'][0],point['point']['coordinates'][1]);
        for pointN in gtfsDB['points'].find(searchNear):
            lonLatEnd = pointN['point']['coordinates']
            tempUrl += str(lonLatEnd[0]) + ','+str(lonLatEnd[1]) + ';'
            listPointNPos.append(pointN['pos'])
        #print( tempUrl[:-1] + '?sources=0')
        listPointN = [];
        if(len(listPointNPos)>0):
            result = requests.get(tempUrl[:-1] + '?sources=0')
            if 'durations' in result.json():
                for i,t in enumerate(result.json()['durations'][0][1:]):
                    if t:
                        if t > 0 and t < tS:
                            listPointN.append({'pos' : listPointNPos[i], 'time' : t})
        gtfsDB['points'].update_one({'_id':point['_id']},{'$set':{'pointN' : listPointN}})

        avgNeightS += len(listStopsN)
        avgNeightP += len(listPointN)
        count += 1
        totTime = time.time() - timeStart0
        avgT += totTime
        print ('\r totNumber {0}, computed {1:.2f}%, time to finish : {2:.0f} min'.format(tot-count,
                                  100.*count/tot,
                                 (tot- count)*avgT/(count*60.)), end="\r")

def listPointsStopsN(gtfsDB, city):
    maxStop = gtfsDB['stops'].count({'city':city})
    maxPoint = gtfsDB['points'].count({'city':city})
    maxRow = -1
    for stop in gtfsDB['stops'].find({'city':city}).sort([('pos',1)]):
        #print stop
        maxRow = max(maxRow, len(stop['stopN']))
        maxRow = max(maxRow, len(stop['pointN']))
        print ('stops {0}'.format(stop['pos']),end="\r")
    for point in gtfsDB['points'].find({'city':city}).sort([('pos',1)]):
        #print stop
        maxRow = max(maxRow, len(point['stopN']))
        maxRow = max(maxRow, len(point['pointN']))
        print( 'points {0}'.format(point['pos']),end="\r")
    #maxRow += 2
    timeS = np.full(maxStop, -2, dtype = np.int32)
    timeP = np.full(maxPoint, -2, dtype = np.int32)
    S2SPos = np.full((maxStop, maxRow), -2, dtype = np.int32)
    S2STime = np.full((maxStop, maxRow), -2,dtype = np.int32)
    P2PPos = np.full((maxPoint, maxRow), -2,dtype = np.int32)
    P2PTime = np.full((maxPoint, maxRow), -2,dtype = np.int32)
    P2SPos = np.full((maxPoint, maxRow), -2,dtype = np.int32)
    P2STime = np.full((maxPoint, maxRow), -2,dtype = np.int32)
    count_error = 0
    for stop in gtfsDB['stops'].find({'city':city}).sort([('pos',1)]):
        for i,stopN in enumerate(stop['stopN']):
            if(stop['stopN'][i]['time'] >= 0):
                S2SPos[stop['pos']][i] = stop['stopN'][i]['pos']
                S2STime[stop['pos']][i] = round(stop['stopN'][i]['time'])
            else:
                count_error += 1
                print( 'error!!', count_error, stop['stopN'][i]['time'], i)
        print ('fill stop neighbors {0}'.format(stop['pos']),end="\r")


    for point in gtfsDB['points'].find({'city':city}).sort([('pos',1)]):
        for i,stopN in enumerate(point['stopN']):
            if(point['stopN'][i]['time'] >= 0):
                if(i >= maxRow): print( len(point['stopN']), point)
                P2SPos[point['pos']][i] = point['stopN'][i]['pos']
                P2STime[point['pos']][i] = round(point['stopN'][i]['time'])
        for i,pointN in enumerate(point['pointN']):
            if(point['pointN'][i]['time'] >= 0):
                P2PPos[point['pos']][i] = point['pointN'][i]['pos']
                P2PTime[point['pos']][i] = round(point['pointN'][i]['time'])
        print ('fill point neighbors {0}'.format(point['pos']),end="\r")
    return [timeS, timeP, S2SPos, S2STime , P2PPos, P2PTime, P2SPos, P2STime]

def computeAverage(valuesToAverage, gtfsDB, city):
    count = 0
    for point in gtfsDB['points'].find({'city':city}).sort([('city',1)]):
        newPoint = point
        for field in valuesToAverage:
            tot = 0.
            c = 0.
            for t in newPoint[field]:
                if t not in ['errStd', 'maxDiff', 'avg']:
                    tot += newPoint[field][t]
                    c += 1.
                    #print field, newPoint[field][t]
            newPoint[field]['avg'] = tot / c if c != 0 else 0

        for field in valuesToAverage:
            newPoint[field]['maxDiff'] = 0
            newPoint[field]['errStd'] = 0
            for t in newPoint[field]:
                if t not in ['errStd', 'maxDiff', 'avg']:
                    diff = math.fabs(newPoint[field][t] - newPoint[field]['avg'])
                    newPoint[field]['maxDiff'] = max(newPoint[field]['maxDiff'], diff)
                    newPoint[field]['errStd'] += math.pow(diff,2)
            n = len(newPoint[field])
            newPoint[field]['errStd'] = math.sqrt(newPoint[field]['errStd'] / (n * (n-1)))
            #print field
            #print newPoint[field]
        #break
        #print newPoint
        gtfsDB['points'].replace_one({'_id':point['_id']},newPoint)
        print ('\r {0} - {1}'.format(count,point['city'] ),end="\r")
        count += 1