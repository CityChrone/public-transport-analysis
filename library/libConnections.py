import os
import zipfile
import pandas as pd
import pymongo as pym
import time
from datetime import datetime
import numpy as np
infty = 1000000

def printGtfsDate(directoryGTFS):
    print("interval of validity of the gtfs files")
    for filename in os.listdir(directoryGTFS):
        if filename.endswith(".zip"):

            archive = zipfile.ZipFile(directoryGTFS + filename, 'r')
            for fileTxt in archive.filelist:
                if fileTxt.filename =="calendar.txt":
                    lines = archive.open("calendar.txt", mode='r')
                    res = pd.read_csv(lines,encoding = 'utf-8-sig', dtype=str)

                    timePrint = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(os.path.getmtime(directoryGTFS + filename)))
                    print("{0} file\n calendar.txt -> start_date:{1}, end_date:{2} (first row)".format(filename, res['start_date'][0],res['end_date'][0] ))
                if fileTxt.filename =="calendar_dates.txt":
                    lines = archive.open("calendar_dates.txt", mode='r')
                    res = pd.read_csv(lines,encoding = 'utf-8-sig', dtype=str)

                    timePrint = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(os.path.getmtime(directoryGTFS + filename)))
                    print("{0} file\n calendar_dates.txt -> date:{1} (first row)".format(filename, res['date'][0]))

def file_len(fname):
    with archive.open(nameCSVFile, mode='rU') as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def readConnections(gtfsDB, city, directoryGTFS, day, dayName):
    services_id = readValidityDateGtfs(gtfsDB, day, dayName, city)
    
    tripID2Route = {}
    count = 0   
    for trip in gtfsDB['trips'].find({'city':city}):
        try:
            tripID2Route[trip['file']][str(trip['trip_id'])] = str(trip['route_id'])
        except:
            tripID2Route[trip['file']] = {str(trip['trip_id']) : str(trip['route_id'])}
        if count % 1000 == 0:
            #clear_output()
            print('number of trips {0}'.format(count), end="\r")
        count += 1

    listOfFile = ['stop_times.txt']

    if('connections' in gtfsDB.collection_names()):
        gtfsDB['connections'].delete_many({'city':city})

    count = 0
    stopsTimes = {}  
    for filename in reversed(list(os.listdir(directoryGTFS))):
        if filename.endswith(".zip"):
            stopsTimes = {}
            archive = zipfile.ZipFile(directoryGTFS + filename, 'r')
            print('\n', filename)
            for nameCSVFile in listOfFile:
                collGtfs = gtfsDB[nameCSVFile[:-4]]
                if nameCSVFile in archive.namelist(): 
                    count = 0
                    #try:
                    lines = archive.open(nameCSVFile, mode='r')
                    print("reading stop_times.txt...")
                    res = pd.read_csv(lines,encoding = 'utf-8-sig', dtype=str)
                    print("readed... converting to a list")
                    res["city"] = city
                    res["file"] = filename
                    res = list(v for v in res.to_dict("index").values())
                    print("converted...")
                    tot = len(res)
                    for i, elem in enumerate(res): #.iterrows():
                        print('{0}, {1}'.format(count, tot), end="\r")
                        count += 1
                        #elem['posStop'] = stopsId2Pos[filename][str(elem['stop_id'])]
                        elem['posStop'] = str(elem['stop_id'])
                        elem['route'] = tripID2Route[filename][str(elem['trip_id'])]
                        try:
                            stopsTimes[elem['trip_id']].append(elem)
                        except:
                            stopsTimes[elem['trip_id']]= [elem]
                    res = []
                    fillConnections(gtfsDB, stopsTimes, services_id[filename], city, filename, archive)
    indexConnections(gtfsDB)
    
def indexConnections(gtfsDB):
    gtfsDB['connections'].create_index([("pStart", pym.ASCENDING),("city", pym.ASCENDING)])
    gtfsDB['connections'].create_index([("pEnd", pym.ASCENDING),("city", pym.ASCENDING)])
    gtfsDB['connections'].create_index([("tStart", pym.ASCENDING),("tEnd", pym.ASCENDING),("city", pym.ASCENDING)])
    gtfsDB['connections'].create_index([("tEnd", pym.ASCENDING)])
    gtfsDB['connections'].create_index([("city", pym.ASCENDING)])
    gtfsDB['connections'].create_index([("trip_id", pym.ASCENDING)])
    gtfsDB['connections'].create_index([("route_id", pym.ASCENDING)])
    gtfsDB['connections'].create_index([("file", pym.ASCENDING)])
    gtfsDB['connections'].create_index([("city", pym.ASCENDING)])

def checkNumberOfGtfs(gtfsDB, city):
    namefiles={}
    for name in gtfsDB['calendar'].distinct('file', filter={'city': city} ):
        try:
            namefiles[name] += 1
        except:
            namefiles[name] = 1
    for name in gtfsDB['calendar_dates'].distinct('file', filter={'city': city} ):
        try:
            namefiles[name] += 1
        except:
            namefiles[name] = 1
    #print namefiles

    print ('number of file in calendar+calendar_dates: {0}\nin stops: {1}'.format(len(namefiles), len(gtfsDB['stops'].distinct('file', filter={'city': city}))))
    return namefiles

def readValidityDateGtfs(gtfsDB, day, dayName, city):
    namefiles = checkNumberOfGtfs(gtfsDB, city)
    services_id = {}
    print("\nChecking the number of services active in the date selected:")
    for serv in gtfsDB['calendar'].find({dayName : '1','city':city}):
        #print serv['end_date'], serv
        try:
            services_id[serv['file']].append(serv['service_id'])
        except:
            services_id[serv['file']] = [serv['service_id']]

    for name in namefiles:
        try:
            services_id[name]
            print( 'file: {0} \t total number of active service (in calendar.txt): {1}'.format(name, len(services_id[name])))
        except KeyError:
            print( 'file: {0} \t total number of active service (in calendar.txt): {1}'.format(name, 'Serv NOT FOUND!!'))


    print( 'number of different service_id:', len(services_id))
    print ('\n')

    for exp in  gtfsDB['calendar_dates'].find({'date':day,'city':city}):
        if(exp['exception_type'] == '1' or exp['exception_type'] == 1):
            try:
                services_id[exp['file']].append(exp['service_id'])
            except:
                services_id[exp['file']] = [exp['service_id']]
        else:
            if exp['service_id'] in services_id[exp['file']] : services_id[exp['file']].remove(exp['service_id']) 
    tot = 0
    for name in  namefiles:
        try:
            tot += len(services_id[name])
            print ('file: {0} \t total number of active service (in calendar_dates.txt): {1}'.format(name, len(services_id[name])))
        except KeyError:
            print( 'file: {0} \t total number of active service (in calendar_dates.txt): {1}'.format(name, 'Serv NOT FOUND!!'))
    print( 'number of different service_id:', len(services_id), 'total number of active services found:', tot)
    return services_id

    
def findSec(hour):
    hour = str(hour)
    if(len(hour)>3):
        if(len(hour) == 8):
            if(int(hour[0:2]) >= 24):
                hourInt = int(hour[0:2]);
                diffInt = int(hour[0:2]) - 24;
                timeToCompute = str(diffInt) + hour[2:]
                #print timeToCompute;
                pic = datetime.strptime(timeToCompute, "%H:%M:%S")
                #print timeToCompute, hourInt*3600 + pic.hour*3600 + pic.minute*60 + pic.second
                return hourInt*3600 + pic.hour*3600 + pic.minute*60 + pic.second
            else:
                if(hour[0] == ' '): hour = hour[1:]
                pic = datetime.strptime(hour, "%H:%M:%S")
                return pic.hour*3600 + pic.minute*60 + pic.second
        else:
            #print len(hour)
            pic = datetime.strptime(hour, "%H:%M:%S")
            return pic.hour*3600 + pic.minute*60 + pic.second
    else:
        return infty;

def fillConnections(gtfsDB, stopsTimes, services_id, city, filename, archive):
    count=0
    count_err = 0
    count_err_start = 0
    count_err_start_after = 0
    tot = gtfsDB['trips'].find({'service_id':{'$in':services_id},'city':city, 'file':filename}).count()
    listTrip = list(gtfsDB['trips'].find({'service_id':{'$in':services_id},'city':city, 'file':filename}))
    listToInsert = []
    listOfFreqTrip = {}
    #print archive.namelist()
    if 'frequencies.txt' in archive.namelist(): 
        lines = archive.open('frequencies.txt', mode='r')
        res = pd.read_csv(lines,encoding = 'utf-8-sig', dtype=str)
        res["city"] = city
        res["file"] = filename
        res = list(v for v in res.to_dict("index").values())
        for freq in res:
            try:
                listOfFreqTrip[freq['trip_id']].append(freq)
            except KeyError:
                listOfFreqTrip[freq['trip_id']] = [freq]
        if len(res)> 0:
            print( "found freq for # of trips", len(res))
        #print listOfFreqTrip
   
    for trip in listTrip:
        if(trip['trip_id'] in stopsTimes):
            resNotSorted = stopsTimes[trip['trip_id']]
            res = sorted(resNotSorted, key=lambda k: int(k['stop_sequence'])) 
            if trip['trip_id'] in listOfFreqTrip:
                for freq in listOfFreqTrip[trip['trip_id']]:
                    startTime = findSec(freq['start_time'])
                    endTime = findSec(freq['end_time'])
                    currentTime = startTime
                    startTrip = startTime
                    count = 0
                    if len(res) > 0:
                        while True:                
                            for i,stop in enumerate(res[:-1]):
                                #print stop['departure_time'],  stop['arrival_time'], stop
                                #print len(res[i]['departure_time'])
                                diff = findSec(res[i+1]['arrival_time']) - findSec(res[i]['departure_time'])

                                objToInsert = {
                                    'pStart':res[i]['posStop'],
                                    'pEnd':res[i+1]['posStop'],
                                    'tStart' : currentTime,
                                    'tEnd' : currentTime + diff,
                                    'trip_id' : res[i]['trip_id'],
                                    'route_id' : res[i]['route'],
                                    'seq' : res[i]['stop_sequence'],
                                    'file' : res[i]['file'],
                                    'city':city
                                }
                                if(objToInsert['tStart'] > objToInsert['tEnd']): 
                                    count_err += 1
                                    #print( 'error', i, res[i]['file'])
                                else:
                                    #gtfsDB['connections'].insert_one(objToInsert)
                                    listToInsert.append(objToInsert)
                                    pass
                                currentTime += diff
                            startTrip += int(freq['headway_secs'])
                            currentTime = startTrip
                            if(startTrip > endTime):
                                break
                            #print '\r freq added {0}'.format(count),
                            count += 1

            else:            
                if len(res) > 1:
                   
                    startStop = res[0]
                    endStop = res[len(res)-1]
                    startTime = findSec(startStop['departure_time'])
                    endTime = findSec(endStop['arrival_time'])
                    if(startTime == infty or endTime == infty):
                        count_err_start += 1
                    else:
                        tentativeTime = []
                        stepTime = (endTime - startTime)/(len(res)-1);
                        #beforeTime = findSec(res[0]['departure_time'])
                        stepTime = 0
                        for i,stop in enumerate(res[:-1]):
                            
                            
                            res[i]['departure_time'] =  res[i-1]['departure_time'] if findSec(res[i]['departure_time']) == infty else res[i]['departure_time'];
                            res[i]['arrival_time'] =  res[i-1]['arrival_time'] if findSec(res[i]['arrival_time']) == infty else res[i]['arrival_time'];
                            tEnd = findSec(res[i]['arrival_time']) if findSec(res[i+1]['arrival_time']) == infty else findSec(res[i+1]['arrival_time'])
                            if(findSec(res[i+1]['arrival_time']) == infty):
                                #print('failed', res[i]['departure_time'], res[i]['arrival_time'], findSec(res[i]['departure_time']), findSec(res[i-1]['departure_time']), tEnd)
                                count_err_start_after+=1
                                #break
                            

                            objToInsert = {
                                'pStart':res[i]['posStop'],
                                'pEnd':res[i+1]['posStop'],
                                'tStart' : findSec(res[i]['departure_time']),
                                'tEnd' : tEnd,
                                'trip_id' : res[i]['trip_id'],
                                'route_id' : res[i]['route'],
                                'seq' : res[i]['stop_sequence'],
                                'file' : res[i]['file'],
                                'city':city
                            }
                            if(findSec(res[i]['departure_time']) > tEnd): 
                                count_err += 1
                                #print('error', i, res[i]['file'])
                            else:
                                #gtfsDB['connections'].insert_one(objToInsert)
                                listToInsert.append(objToInsert)
                                pass
                else:
                    pass
                    #print( 'error')
        else:
            pass
            #count_err += 1
            #print('error', i, res[i]['file'])
        print('count {0}, tot {1}, err {2}, err_start {3}, err_start_after {4}'.format(count, tot, count_err, count_err_start, count_err_start_after), end="\r")
        count += 1
    if(len(listToInsert)>0):
        print('inserting to DB....')
        gtfsDB['connections'].insert_many(listToInsert)
    print ('tot connections', len(listToInsert))
    
    
def updateConnectionsStopName(gtfsDB, city):
    tot = gtfsDB['stops'].find({'city':city}).count()
    count = 0
    totC = gtfsDB['connections'].find({'city':city}).count()
    c1 = 0
    c2 = 0
    for stop in gtfsDB['stops'].find({'city':city}):
        res1 = gtfsDB['connections'].update_many({'pStart':stop['stop_id'],'file':stop['file']},{"$set":{'pStart':stop['pos'],"updated":True}})
        res2 = gtfsDB['connections'].update_many({'pEnd':stop['stop_id'],'file':stop['file']},{"$set":{'pEnd':stop['pos'],"updated":True}})
        c1 += res1.modified_count
        c2 += res2.modified_count
        print ('\r{0},{1}-- pStart {2} pEnd {3}, totC {4}'.format(count,tot,c1,c2, totC),end="\r")
        count += 1
    print("connections deleted",gtfsDB['connections'].delete_many({'city':city, 'updated':{"$exists":False}}).deleted_count)
    
def makeArrayConnections(gtfsDB, hStart, city):
    fields = {'tStart':1,'tEnd':1, 'pStart':1, 'pEnd':1, '_id':0 }
    pipeline = [
        {'$match':{'city': city,'tStart':{'$gte':hStart}}},
        {'$sort':{'tStart':1}},
        {'$project':{'_id':"$_id", "c":['$tStart', '$tEnd','$pStart','$pEnd']}},
    ]
    allCC = gtfsDB['connections'].aggregate(pipeline)
    arrayCC = np.full((gtfsDB['connections'].find({"city":city,'tStart':{'$gte':hStart}}).count(),4),1.,dtype = np.int)
    countC = 0
    tot = gtfsDB['connections'].find({'tStart':{'$gte':hStart},'city':city}).count()
    for cc in allCC:
        #if round(cc['tStart']) <=  round(cc['tEnd']) and isinstance(cc['pStart'] , int ) and isinstance(cc['pEnd'] , int ):
        print(' {0}, {1}, {2}'.format(countC, tot, cc['c']),end="\r");
        #try:
        cc['c'] = [round(int(c)) for c in cc['c']]
        arrayCC[countC] = cc['c'] 
        countC += 1
        #except:
            #print('error')
    print( 'Num of connection', len(arrayCC))
    return arrayCC
