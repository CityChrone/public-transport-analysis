from libAccessibility import arrayTimeCompute, ListFunctionAccessibility
from libCSA import area_geojson

import math
import time

inf = 10000000

from numba import jit, int32,int64

@jit(int32[:](int32[:],int32[:],int32[:,:],int32[:,:]), nopython = True)
def computePointTime(timePP, timeSS, P2SPos, P2STime ):
    #global P2SPos
    #global P2STime
    maxRow = len(P2SPos[0])
    for p_i in range(len(timePP)):
        ListNeighP_i = P2SPos[p_i]
        for stop_i in range(maxRow):
            stop = int(ListNeighP_i[stop_i])
            if stop == -2:
                break
            else:
                timePP[p_i] = min(timePP[p_i], timeSS[stop] + P2STime[p_i][stop_i])
    return timePP

@jit(int32[:](int32[:],int32,int64[:,:],int32[:,:],int32[:,:]), nopython = True)
def coreCSA(timesValues, timeStart, arrayCC, S2SPos, S2STime):
    #print 'inter'
    #global arrayCC
    #arrayCC = CC
    #global S2SPos
    #global S2STime
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
                            timesValuesN[neigh] = c[1] + S2STime[Parr_i][neigh_i]
                    else:
                         break
                      
    for i,t in enumerate(timesValues):
        if t > timesValuesN[i]:
            timesValues[i] = timesValuesN[i]
            #print('less!!')
    return timesValues


def computeVelOnePoint(point, startTime, timeS, timeP,arrayCC, P2PPos, P2PTime,  P2SPos, P2STime, S2SPos, S2STime):
    timeS.fill(inf)  #Inizialize the time of stop
    timeP.fill(inf)
    posPoint = point['pos'] #position of the point in the arrays
    timeP[posPoint] = startTime  #initialize the starting time of the point

    for neigh_i, neigh in enumerate(P2PPos[posPoint][P2PPos[posPoint] != -2]): #loop in the point near to the selected point
        neigh = neigh
        timeP[neigh] = P2PTime[posPoint][neigh_i] + startTime #initialize to startingTime + WalkingTime all near point

    #loop in the stops near to the selected point
    for neigh_i, neigh in enumerate(P2SPos[posPoint][P2SPos[posPoint] != -2]): 
        neigh = neigh
        timeS[neigh] = P2STime[posPoint][neigh_i] + startTime #initialize to startingTime + WalkingTime all near stops

    #timeSInit = timeS.copy()

    timeS = coreCSA(timeS,startTime,arrayCC, S2SPos, S2STime)
    timeP = computePointTime(timeP, timeS, P2SPos, P2STime)
    return timeP



def computeVel(city, startTime, timeS, timeP, arrayCC, P2PPos, P2PTime, P2SPos, P2STime, S2SPos, S2STime, gtfsDB, computeIsochrone, first):
    maxVel = 0
    totTime = 0.
    avgT = 0 
    tot = len(timeP)
    areaHex = area_geojson(gtfsDB['points'].find_one({'city':city})['hex'])
    count = 0
    for point in gtfsDB['points'].find({'city':city},{'pointN':0, 'stopN':0}).sort([('pos',1)]):

        timeStart0 = time.time()

        #Inizialize the time of stop and point 
        
        timeP = computeVelOnePoint(point, startTime, timeS, timeP, arrayCC, P2PPos,P2PTime, P2SPos, P2STime, S2SPos, S2STime)
        timePReached = timeP - startTime    
                        
        toUpdate = {}
        timeStartStr = str(startTime)  
        listAccessibility = ['velocityScore']
        for field in listAccessibility:
            if first:
                toUpdate[field] = {}
            else:
                if field in point:
                    toUpdate[field] = point[field]
            
            if field in toUpdate:
                toUpdate[field][timeStartStr] = ListFunctionAccessibility[field](timePReached, areaHex)
            else:
                #print 'else'
                toUpdate[field] = {timeStartStr : ListFunctionAccessibility[field](timePReached, areaHex)}
        
        #print toUpdate
        if (computeIsochrone):#(gtfsDB['isochrones'].find({'_id':point['_id']}).count() == 0):#
            geojson = {"type": "Feature", "geometry": {"type": "Polygon","coordinates": []}}
            for i, t in enumerate(timeP):
                listHex[i]['t'] = t - startTime
            geojson = reduceHexsInShell(listHex, 'vAvg', shell = [-1, 0, 900, 1800, 2700, 3600,4500, 5400, 6300,7200, 9000])
            gtfsDB['isochrones'].replace_one({'_id':point['_id']},{'_id':point['_id'],'geojson':geojson, 'city':city},upsert=True)

        gtfsDB['points'].update_one({'_id':point['_id']},{'$set':toUpdate})

        totTime += time.time() - timeStart0
        avgT = float(totTime) / float(count+1)
        h = int((tot- count)*avgT/(60*60))
        m = (tot - count)*avgT/(60) - h * 60

        count += 1
        print('point: {0}, Velocity Score : {1:.1f}, time to finish : {2:.1f}h, {3:.1f} m'.format(count, toUpdate['velocityScore'][timeStartStr], h, m), end="\r")
