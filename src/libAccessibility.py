from numba import jit, int32, float64
import math
import numpy as np

totNumTime = 4*3600


@jit()
def tDistrScore(t):
    t /= 30.
    a = 0.2; #0.12 0.15 0.19
    b = 0.7;#0.77 0.74 0.69
    N= 2.5;#1.89 2.11 2.52
    TBus = 67.;#73.3*60  73.5*60 75.3*60
    if(t == 0): return 0.
    return N * math.exp(-((a*TBus)/t) - t/(b*TBus))
normtDistrScore = sum([tDistrScore(t_i) for t_i in range(totNumTime)])

@jit()
def tDistrScoreGall(t):
    t /= 60.
    c = 36.
    b = 9.3
    return math.exp(c/b) * (1. - math.exp(-t/c)) * math.exp( -t/b - c * math.exp(-t/c) / b ) / b
normtDistrScoreGall = sum([tDistrScoreGall(t_i) for t_i in range(totNumTime)])

@jit()
def tDistrScore1h(t):
    if(t < 3600):
        return 1./3600.
    else:
        return 0
    return 0
normtDistrScore1h = sum([tDistrScore1h(t_i) for t_i in range(totNumTime)])

@jit()
def normed_tDistrScore(t):
    global normtDistrScore
    return tDistrScore(t) / normtDistrScore

@jit()
def normed_tDistrScoreGall(t):
    global normtDistrScoreGall
    return tDistrScoreGall(t) / normtDistrScoreGall

@jit()
def normed_tDistrScore1h(t):
    global normtDistrScore1h
    return tDistrScore1h(t) / normtDistrScore1h



@jit()
def areaTimeCompute(timePR):
    aTime = np.full(totNumTime, 0., dtype = np.float64)
    for t in timePR:
        if t < totNumTime:
            aTime[int(t)] += 1
        else:
            pass
    return aTime

@jit()
def arrayTimeCompute(timePR, arrayW):
    aTime = np.full(totNumTime, 0., dtype = np.float64)
    for i, t in enumerate(timePR):
        if t < totNumTime:
            aTime[t] += arrayW[i]           
        else:
            pass
    return aTime


def computeVelocityScore(distr):
    @jit()
    def computeVel(timePReached, data):
        areaHex = data['areaHex']
        area_new = 0
        vAvg = 0
        integralWindTime = 0
        areasTime = areaTimeCompute(timePReached)
        for time_i in range(len(areasTime)):
            area_new += areasTime[time_i]*areaHex;
            if time_i > 0:
                vAvg += distr(time_i) * (1./time_i)*(math.sqrt(area_new/math.pi));
                integralWindTime += distr(time_i);
        vAvg /= integralWindTime;
        vAvg *= 3600.;
        return vAvg
    return computeVel


def computeSocialityScore(distr):
    @jit()
    def computeSoc(timePReached, data):
        arrayW = data['arrayPop']
        popComul = 0
        popMean = 0
        popsTime = arrayTimeCompute(timePReached, arrayW)
        for time_i in range(len(popsTime)):
            popComul += popsTime[time_i];
            popMean += distr(time_i) * popComul;
        return popMean
    return computeSoc

@jit()
def timeVelocity(timePReached, data):
    timeListToSave = data["timeListToSave"]
    areaHex = data['areaHex']
    areasTime = areaTimeCompute(timePReached)
    res = {'timeList':timeListToSave, 'velocity':[]}
    for time2Save in timeListToSave:
        area = sum(areasTime[0:time2Save]) * areaHex
        res["velocity"].append((3600./time2Save)*(math.sqrt(area/math.pi)))
    return res

@jit()
def timeSociality(timePReached, data):
    timeListToSave = data["timeListToSave"]
    arrayW = data['arrayPop']
    popsTime = arrayTimeCompute(timePReached, arrayW)
    res = {'timeList':timeListToSave, 'sociality':[]}
    for time2Save in timeListToSave:
        pop = sum(popsTime[0:time2Save])
        res["sociality"].append(pop)
    return res

                              
ListFunctionAccessibility = {
    'velocityScore' : computeVelocityScore(normed_tDistrScore),
    'socialityScore': computeSocialityScore(normed_tDistrScore),
    'velocityScoreGall' : computeVelocityScore(normed_tDistrScoreGall),
    'socialityScoreGall': computeSocialityScore(normed_tDistrScoreGall),
    'velocityScore1h' : computeVelocityScore(normed_tDistrScore1h),
    'socialityScore1h': computeSocialityScore(normed_tDistrScore1h),
    'timeVelocity' : timeVelocity,
    'timeSociality': timeSociality
};
