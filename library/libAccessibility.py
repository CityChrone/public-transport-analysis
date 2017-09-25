from numba import jit, int32, float64
import math
import numpy as np
#startTime = 7*3600
#endTime = 24*3600

@jit()
def tDistrGall(t):
    t /= 60.
    c = 36.
    b = 9.3
    return math.exp(c/b) * (1. - math.exp(-t/c)) * math.exp( -t/b - c * math.exp(-t/c) / b ) / b

@jit()
def tDistrHalf(t):
    t /= 30.
    a = 0.2; #0.12 0.15 0.19
    b = 0.7;#0.77 0.74 0.69
    N= 2.5;#1.89 2.11 2.52
    TBus = 67.;#73.3*60  73.5*60 75.3*60
    if(t == 0): return 0.
    return N * math.exp(-((a*TBus)/t) - t/(b*TBus))

@jit()
def tDistr(t):
    t /= 60.
    a = 0.2; #0.12 0.15 0.19
    b = 0.7;#0.77 0.74 0.69
    N= 2.5;#1.89 2.11 2.52
    TBus = 67.;#73.3*60  73.5*60 75.3*60
    if(t == 0): return 0.
    return N * math.exp(-((a*TBus)/t) - t/(b*TBus))


totNumTime = 24*3600
normGall = sum([tDistrGall(t_i) for t_i in range(totNumTime)])
normHalf = sum([tDistrHalf(t_i) for t_i in range(totNumTime)])
norm = sum([tDistr(t_i) for t_i in range(totNumTime)])

@jit()
def tDistrN(t):
    global norm
    return tDistr(t) / norm

@jit()
def tDistrNHalf(t):
    global normHalf
    return tDistrHalf(t) / normHalf 

@jit()
def tDistrGallN(t):
    global normGall
    return tDistrGall(t) / normGall 

@jit()
def computeVel(areasTime, areaHex):
    area_new = 0
    vAvg = 0
    integralWindTime = 0
    for time_i in range(len(areasTime)):
        area_new += areasTime[time_i]*areaHex;
        if time_i > 0:
            vAvg += tDistrN(time_i) * (1./time_i)*(math.sqrt(area_new/math.pi));
            integralWindTime += tDistrN(time_i);
    vAvg /= integralWindTime;
    vAvg *= 3600.;
    return vAvg


@jit()
def computeVelHalf(areasTime, areaHex):
    area_new = 0
    vAvg = 0
    integralWindTime = 0
    for time_i in range(len(areasTime)):
        area_new += areasTime[time_i]*areaHex;
        if time_i > 0:
            vAvg += tDistrNHalf(time_i) * (1./time_i)*(math.sqrt(area_new/math.pi));
            integralWindTime += tDistrNHalf(time_i);
    vAvg /= integralWindTime;
    vAvg *= 3600.;
    return vAvg

@jit()
def computeVelGall(areasTime, areaHex):
    area_new = 0
    vAvg = 0
    integralWindTime = 0
    for time_i in range(len(areasTime)):
        area_new += areasTime[time_i]*areaHex;
        if time_i > 0:
            vAvg += tDistrGallN(time_i) * (1./time_i)*(math.sqrt(area_new/math.pi));
            integralWindTime += tDistrGallN(time_i);
    vAvg /= integralWindTime;
    vAvg *= 3600.;
    return vAvg

@jit()
def popMean(popsTime):
    popComul = 0
    popMean = 0
    for time_i in range(len(popsTime)):
        popComul += popsTime[time_i];
        popMean += tDistrN(time_i) * popComul;
    return popMean

@jit()
def pop1h(popsTime):
    lim = 3600
    popComul = 0
    for time_i in range(len(popsTime)):
        if time_i <= lim: 
            popComul += popsTime[time_i];
    return popComul


@jit()
def pop2h(popsTime):
    lim = 7200
    popComul = 0
    for time_i in range(len(popsTime)):
        if time_i <= lim: 
            popComul += popsTime[time_i];
    return popComul


@jit()
def popMeanHalf(popsTime):
    popComul = 0
    popMean = 0
    for time_i in range(len(popsTime)):
        popComul += popsTime[time_i];
        popMean += tDistrNHalf(time_i) * popComul;
    return popMean

@jit()
def areaMean(areasTime, areaHex):
    areaComul = 0
    areaMean = 0
    for time_i in range(len(areasTime)):
        areaComul += areasTime[time_i]*areaHex;
        areaMean += tDistrN(time_i) * areaComul;
    return areaMean


@jit()
def areaMeanHalf(areasTime, areaHex):
    areaComul = 0
    areaMean = 0
    for time_i in range(len(areasTime)):
        areaComul += areasTime[time_i] * areaHex;
        areaMean += tDistrNHalf(time_i) * areaComul;
    return areaMean

@jit()
def tMean(areasTime):
    timeComul = 0
    timeMean = 0
    for time_i in range(len(areasTime)):
        timeComul += areasTime[time_i]*time_i;
        timeMean += tDistrN(time_i) * timeComul;
    return timeMean


@jit()
def tMeanHalf(areasTime):
    timeComul = 0
    timeMean = 0
    for time_i in range(len(areasTime)):
        timeComul += areasTime[time_i]*time_i;
        timeMean += tDistrNHalf(time_i) * timeComul;
    return timeMean

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

functionComputeVel = {
    'vel' : computeVel,
    'velHalf':computeVelHalf,
    'velGall':computeVelGall,
    'popMean':popMean,
    'areaMean':areaMean,
    'popMeanHalf':popMeanHalf,
    'areaMeanHalf':areaMeanHalf,
    'tMean':tMean,
    'tMeanHalf':tMeanHalf,
    'pop1h': pop1h,
    'pop2h': pop2h
};


'''
@jit()
def computeVelOldHalf(areasTime, areaHex):
    area_new = 0
    area_old = 0    
    vAvg = 0
    integralWindTime = 0
    for time_i in range(len(areasTime)):
        area_new += areasTime[time_i]*areaHex;
        vAvg += tDistrNewNHalf(time_i) * (math.sqrt(area_new/math.pi) - math.sqrt(area_old/math.pi));
        area_old = area_new;
        integralWindTime += tDistrNewNHalf(time_i);
    vAvg /= integralWindTime;
    vAvg *= 3600.;
    return vAvg

@jit()
def computeVelAll(areasTime, areaHex):
    area_new = 0
    area_old = 0    
    vAvg = 0
    integralWindTime = 0
    lastIndex = 0
    for i,t in enumerate(areasTime):
        if t > 0:
            lastIndex = i
    for time_i in range(lastIndex+1):
        area_new += areasTime[time_i]*areaHex;
        if time_i > 0:
            vAvg += (1./time_i)*(math.sqrt(area_new/math.pi));
            area_old = area_new;
            integralWindTime += 1;
    if(integralWindTime == 0):
        return 0.
    else:
        vAvg /= integralWindTime;
        vAvg *= 3600.;
        return vAvg


@jit()
def computeVelOldGall(areasTime, areaHex):
    area_new = 0
    area_old = 0    
    vAvg = 0
    integralWindTime = 0
    for time_i in range(len(areasTime)):
        area_new += areasTime[time_i]*areaHex;
        vAvg += tDistrGallN(time_i) * (math.sqrt(area_new/math.pi) - math.sqrt(area_old/math.pi));
        area_old = area_new;
        integralWindTime += tDistrGallN(time_i);
    vAvg /= integralWindTime;
    vAvg *= 3600.;
    return vAvg

comulOld = np.full(totNumTime, 0, dtype = np.float64)
comulNew = np.full(totNumTime, 0, dtype = np.float64)
comulNewHalf = np.full(totNumTime, 0, dtype = np.float64)
comulGall = np.full(totNumTime, 0, dtype = np.float64)

comulOld[0] = tDistrOldN(0)
comulNew[0] = tDistrNewN(0)
comulNewHalf[0] = tDistrNewNHalf(0)
comulGall[0] = tDistrGallN(0)

for t in range(totNumTime - 1):
    comulOld[t+1] = (comulOld[t] + tDistrOldN(t+1))
    comulNew[t+1] = (comulNew[t] + tDistrNewN(t+1))
    comulNewHalf[t+1] = (comulNewHalf[t] + tDistrNewNHalf(t+1))
    comulGall[t+1] = (comulGall[t] + tDistrGallN(t+1))

tDistrComul = comulNewHalf
'''
'''
@jit()
def computeVelNewComul(areasTime, areaHex):
    area_new = 0
    area_old = 0    
    vAvg = 0
    integralWindTime = 0
    for time_i in range(len(areasTime)):
        p_t =  (1-tDistrComul[time_i])
        area_new += areasTime[time_i]*areaHex;
        vAvg += p_t * (math.sqrt(area_new/math.pi) - math.sqrt(area_old/math.pi));
        area_old = area_new;
        integralWindTime += p_t;
    vAvg /= integralWindTime;
    vAvg *= 3600.;
    return vAvg
'''
