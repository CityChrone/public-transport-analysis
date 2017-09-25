import libAccessibility
import libCSA
from libAccessibility import arrayTimeCompute, areaTimeCompute,functionComputeVel
from libAccessibility import popMean, areaMean, tMean,popMeanHalf, areaMeanHalf, tMeanHalf
from libAccessibility import computeVel,computeVelHalf, computeVelGall
from libCSA import myhexgrid, dist2Point, reduceHexsInShell, reduceHexsInShellFast, area_geojson
import math
import time

inf = 10000000

def computeVelOnePoint(point, startTime, timeS, timeP, P2PTime, P2PPos, P2SPos, P2STime):
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

    timeS = tree(timeS,startTime)
    timeP = computePointTime(timeP, timeS)
    return timeP

def computeVel(startTime, timeS, timeP, P2PTime, P2PPos, P2SPos, P2STime, gtfsDB, computeIsochrone, first):
    maxVel = 0
    totTime = 0.
    avgT = 0 
    tot = gtfsDB['points'].find({'city':city}).count()
    
    count = 0
    for point in gtfsDB['points'].find({'city':city},{'pointN':0, 'stopN':0}).sort([('pos',1)]):

        timeStart0 = time.time()

        #Inizialize the time of stop and point 
        
        timeP = computeVelOnePoint(point, startTime, timeS, timeP, P2PTime, P2PPos, P2SPos, P2STime)

        timePReached = timeP - startTime    
        
        valuesVel = ['vel','velHalf','velGall','areaMean','areaMeanHalf']
        valuesPop = ['popMean','popMeanHalf']
        valuesTime = ['tMean','tMeanHalf']
        
        areasTime = areaTimeCompute(timePReached)
        popsTime = arrayTimeCompute(timePReached, popArray)
        
        
        toUpdate = {}
        timeStartStr = str(startTime)
        for field in valuesVel:
            #print field
            if first:
                #print first
                toUpdate[field] = {}
            else:
                if field in point:
                    toUpdate[field] = point[field]
            
            if field in toUpdate:
                #print toUpdate
                toUpdate[field][timeStartStr] = functionComputeVel[field](areasTime, areaHex)
            else:
                #print 'else'
                toUpdate[field] = {timeStartStr : functionComputeVel[field](areasTime, areaHex)}
        
        for field in valuesPop:
            if first:
                toUpdate[field] = {}
            else:
                if field in point:
                    toUpdate[field] = point[field]
            if field in toUpdate:
                toUpdate[field][timeStartStr] = functionComputeVel[field](popsTime)
            else:
                toUpdate[field] = {timeStartStr : functionComputeVel[field](popsTime)}

        for field in valuesTime:
            if first:
                toUpdate[field] = {}
            else:
                if field in point:
                    toUpdate[field] = point[field]
            if field in toUpdate:
                toUpdate[field][timeStartStr] = functionComputeVel[field](areasTime)
            else:
                toUpdate[field] = {timeStartStr : functionComputeVel[field](areasTime)}            
        #print toUpdate

        '''vel = computeVel
        velHalf = computeVelHalf(areasTime,areaHex)
        vAvgGall = computeVelGall(areasTime, areaHex)
        popMeanVal = popMean(popsTime)
        areaMeanVal = areaMean(areasTime, areaHex)
        popMeanValHalf = popMeanHalf(popsTime)
        areaMeanValHalf = areaMeanHalf(areasTime, areaHex)
        tMeanVal =  tMean(areasTime)
        tMeanValHalf =  tMeanHalf(areasTime)'''

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
        maxVel = max(maxVel,toUpdate['velHalf'][timeStartStr])
        print ('\r {0}, vel : {1:.1f}, velHalf : {2:.1f} popMean {3:.2f}, maxVelHalf {6:.1f}, Preached :{7:.1f}% \
        Rem : {4:.1f}h, {5:.1f} m'.format(count, toUpdate['vel'][timeStartStr],
                                          toUpdate['velHalf'][timeStartStr],
                                          toUpdate['popMean'][timeStartStr], 
                                          h,m,maxVel, 100.*len(timeP[timeP < inf])/len(timeP)),end="\r")


    print ('\n \n \n', totTime / count, totTime)