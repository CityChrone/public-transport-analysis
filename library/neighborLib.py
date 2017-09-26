import pymongo as pym
import time
import requests
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


