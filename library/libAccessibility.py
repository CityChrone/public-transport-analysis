from numba import jit, int32, float64
import math
import numpy as np

@jit()
def tDistrVelocityScore(t):
    t /= 30.
    a = 0.2; #0.12 0.15 0.19
    b = 0.7;#0.77 0.74 0.69
    N= 2.5;#1.89 2.11 2.52
    TBus = 67.;#73.3*60  73.5*60 75.3*60
    if(t == 0): return 0.
    return N * math.exp(-((a*TBus)/t) - t/(b*TBus))


totNumTime = 24*3600
normVelocityScore = sum([tDistrVelocityScore(t_i) for t_i in range(totNumTime)])

@jit()
def tDistrNVelocityScore(t):
    global normVelocityScore
    return tDistrVelocityScore(t) / normVelocityScore


@jit()
def computeVelocityScore(timePReached, areaHex):
    area_new = 0
    vAvg = 0
    integralWindTime = 0
    areasTime = areaTimeCompute(timePReached)
    for time_i in range(len(areasTime)):
        area_new += areasTime[time_i]*areaHex;
        if time_i > 0:
            vAvg += tDistrNVelocityScore(time_i) * (1./time_i)*(math.sqrt(area_new/math.pi));
            integralWindTime += tDistrNVelocityScore(time_i);
    vAvg /= integralWindTime;
    vAvg *= 3600.;
    return vAvg


@jit()
def areaTimeCompute(timePR):
    totNumTime = 10000
    aTime = np.full(totNumTime, 0., dtype = np.float64)
    for t in timePR:
        if t < totNumTime:
            aTime[int(t)] += 1
        else:
            pass
    return aTime

@jit()
def arrayTimeCompute(timePR, arrayW):
    totNumTime = 10000
    aTime = np.full(totNumTime, 0., dtype = np.float64)
    for i, t in enumerate(timePR):
        if t < totNumTime:
            aTime[t] += arrayW[i]           
        else:
            pass
    return aTime

ListFunctionAccessibility = {
    'velocityScore' : computeVelocityScore,
};
