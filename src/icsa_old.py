from numba import jit, int32, int64
from libAccessibility import arrayTimeCompute, ListFunctionAccessibility
from hex_grid import area_geojson

import math
import time
import numpy

inf = 10000000


@jit(int32[:](int32[:], int32[:], int32[:, :], int32[:, :]), nopython=True)
def computePointTime(timePP, timeSS, P2SPos, P2STime):
    # global P2SPos
    # global P2STime
    maxRow = len(P2SPos[0])
    for p_i in range(len(timePP)):
        ListNeighP_i = P2SPos[p_i]
        for stop_i in range(maxRow):
            stop = int(ListNeighP_i[stop_i])
            if stop == -2:
                break
            else:
                timePP[p_i] = min(
                    timePP[p_i], timeSS[stop] + P2STime[p_i][stop_i])
    return timePP


@jit(int32[:](int32[:], int32, int64[:, :], int32[:, :], int32[:, :]), nopython=True)
def coreICSA(timesValues, timeStart, arrayCC, S2SPos, S2STime):
    # print 'inter'
    # global arrayCC
    # arrayCC = CC
    # global S2SPos
    # global S2STime
    count = 0
    timesValuesN = numpy.copy(timesValues)
    for c_i in range(len(arrayCC)):
        c = arrayCC[c_i]
        Pstart_i = c[2]
        if timesValues[Pstart_i] <= c[0] or timesValuesN[Pstart_i] <= c[0]:
            count += 1
            Parr_i = c[3]
            if timesValues[Parr_i] > c[1]:
                timesValues[Parr_i] = c[1]
                for neigh_i in range(len(S2SPos[Parr_i])):
                    if S2SPos[Parr_i][neigh_i] != -2:
                        neigh = S2SPos[Parr_i][neigh_i]
                        neighTime = timesValuesN[neigh]
                        if neighTime > c[1] + S2STime[Parr_i][neigh_i]:
                            timesValuesN[neigh] = c[1] + \
                                S2STime[Parr_i][neigh_i]
                    else:
                        break

    for i, t in enumerate(timesValues):
        if t > timesValuesN[i]:
            timesValues[i] = timesValuesN[i]
            # print('less!!')
    return timesValues


def coumputeAvgTimeDistance(point, startTimeList, arrayCC, arraySP, gtfsDB, city):

    timeS = arraySP['timeS']
    timeP = arraySP['timeP']
    S2SPos = arraySP['S2SPos']
    S2STime = arraySP['S2STime']
    P2PPos = arraySP['P2PPos']
    P2PTime = arraySP['P2PTime']
    P2SPos = arraySP['P2SPos']
    P2STime = arraySP['P2STime']
    averageTime = numpy.full(len(timeP), 0, dtype=numpy.float64)
    maxTime = 24*3600
    for startTime in startTimeList:
        timeP = coumputeTimeOnePoint(
            point, startTime, timeS, timeP, arrayCC, P2PPos, P2PTime, P2SPos, P2STime, S2SPos, S2STime)
        timePReached = timeP - startTime
        for i, t in enumerate(timePReached):
            if t > maxTime:
                timePReached[i] = maxTime
        averageTime += timePReached
    averageTime /= len(startTimeList)
    return averageTime


def coumputeTimeOnePoint(point, startTime, timeS, timeP, arrayCC, P2PPos, P2PTime,  P2SPos, P2STime, S2SPos, S2STime):
    timeS.fill(inf)  # Inizialize the time of stop
    timeP.fill(inf)
    posPoint = point['pos']  # position of the point in the arrays
    timeP[posPoint] = startTime  # initialize the starting time of the point

    # loop in the point near to the selected point
    for neigh_i, neigh in enumerate(P2PPos[posPoint][P2PPos[posPoint] != -2]):
        neigh = neigh
        # initialize to startingTime + WalkingTime all near point
        timeP[neigh] = P2PTime[posPoint][neigh_i] + startTime

    # loop in the stops near to the selected point
    for neigh_i, neigh in enumerate(P2SPos[posPoint][P2SPos[posPoint] != -2]):
        neigh = neigh
        # initialize to startingTime + WalkingTime all near stops
        timeS[neigh] = P2STime[posPoint][neigh_i] + startTime

    # timeSInit = timeS.copy()

    # print("timeS {0},startTime {1},arrayCC {2}, S2SPos {3}, S2STime {4}".format(timeS,startTime,arrayCC, S2SPos, S2STime))
    # print("setted the initial timeS time... starting core CSA")
    timeS = coreICSA(timeS, startTime, arrayCC, S2SPos, S2STime)
    # print("ends core CSA... start updating points time")

    timeP = computePointTime(timeP, timeS, P2SPos, P2STime)
    # print("ends points time")
    return timeP


def computeAccessibilities(city, startTime, arrayCC, arraySP, gtfsDB, computeIsochrone, first, listAccessibility=['velocityScore', 'socialityScore', 'velocityScoreGall', 'socialityScoreGall', 'velocityScore1h', 'socialityScore1h', 'timeVelocity', 'timeSociality']):
    timeS = arraySP['timeS']
    timeP = arraySP['timeP']
    S2SPos = arraySP['S2SPos']
    S2STime = arraySP['S2STime']
    P2PPos = arraySP['P2PPos']
    P2PTime = arraySP['P2PTime']
    P2SPos = arraySP['P2SPos']
    P2STime = arraySP['P2STime']

    maxVel = 0
    totTime = 0.
    avgT = 0
    tot = len(timeP)
    areaHex = area_geojson(gtfsDB['points'].find_one({'city': city})['hex'])
    count = 0

    countPop = 0
    arrayPop = numpy.full(len(timeP), -2, dtype=numpy.float64)
    for point in gtfsDB['points'].find({'city': city}, projection={'pointN': False, 'stopN': False}).sort([('pos', 1)]):
        arrayPop[countPop] = point['pop']
        countPop += 1
    # print("array pop made")
    for point in gtfsDB['points'].find({'city': city}, {'pointN': 0, 'stopN': 0}, no_cursor_timeout=True).sort([('pos', 1)]):

        timeStart0 = time.time()

        # Inizialize the time of stop and point
        # print("starting computation")
        timeP = coumputeTimeOnePoint(
            point, startTime, timeS, timeP, arrayCC, P2PPos, P2PTime, P2SPos, P2STime, S2SPos, S2STime)
        timePReached = timeP - startTime

        toUpdate = {}
        timeStartStr = str(startTime)

        timeListToSave = list(range(900, 3600*3+1, 900))
        data = {'areaHex': areaHex, 'arrayPop': arrayPop,
                'timeListToSave': timeListToSave}

        # print("starting accessibility quantitites computation")

        for field in listAccessibility:
            # print(field)
            if first:
                toUpdate[field] = {}
            else:
                if field in point:
                    toUpdate[field] = point[field]

            if field in toUpdate:
                toUpdate[field][timeStartStr] = ListFunctionAccessibility[field](
                    timePReached, data)
            else:
                # print 'else'
                toUpdate[field] = {
                    timeStartStr: ListFunctionAccessibility[field](timePReached, data)}

        # print toUpdate
        # (gtfsDB['isochrones'].find({'_id':point['_id']}).count() == 0):#
        if (computeIsochrone):
            geojson = {"type": "Feature", "geometry": {
                "type": "Polygon", "coordinates": []}}
            for i, t in enumerate(timeP):
                listHex[i]['t'] = t - startTime
            geojson = reduceHexsInShell(
                listHex, 'vAvg', shell=[-1, 0, 900, 1800, 2700, 3600, 4500, 5400, 6300, 7200, 9000])
            gtfsDB['isochrones'].replace_one({'_id': point['_id']}, {
                                             '_id': point['_id'], 'geojson': geojson, 'city': city}, upsert=True)

        # print("end access computaqtion starting updating point")
        gtfsDB['points'].update_one({'_id': point['_id']}, {'$set': toUpdate})

        totTime += time.time() - timeStart0
        avgT = float(totTime) / float(count+1)
        h = int((tot - count)*avgT/(60*60))
        m = (tot - count)*avgT/(60) - h * 60

        count += 1
        print('point: {0}, Velocity Score : {1:.1f}, Sociality Score : {2:.1f}, time to finish : {3:.1f}h, {4:.1f} m'.format(
            count, toUpdate['velocityScore'][timeStartStr], toUpdate['socialityScore'][timeStartStr], h, m), end="\r")
