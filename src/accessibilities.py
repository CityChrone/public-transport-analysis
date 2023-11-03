from numba import njit, int64, float64, prange
import math
import numpy as np

totNumTime = 2*3600

def plot_quantities(budget_path, vel_path, soc_path, fig,row = 1, row_tot = 2):
    row_mult = 3*(row-1)
    ax_budget = fig.add_subplot(row_tot, 3, 1+row_mult) 
    ax_vel = fig.add_subplot(row_tot, 3, 2+row_mult) 
    ax_soc = fig.add_subplot(row_tot, 3, 3+row_mult) 

    ax_budget.cla()
    ax_vel.cla()
    ax_soc.cla()
    
    ax_budget.set_title("cost [Milion euro]")
    ax_vel.set_title("velocity score")
    ax_soc.set_title("sociality score")

    ax_budget.plot(list(range(len(budget_path))), budget_path, "o-r")
    ax_vel.plot(list(range(len(vel_path))), vel_path, "o-b")
    ax_soc.plot(list(range(len(soc_path))), soc_path, "o-")

    return fig

@njit()
def tDistrScore(t):
    t /= 30.
    a = 0.2; #0.12 0.15 0.19
    b = 0.7;#0.77 0.74 0.69
    N= 2.5;#1.89 2.11 2.52
    TBus = 67.;#73.3*60  73.5*60 75.3*60
    if(t == 0): return 0.
    return N * math.exp(-((a*TBus)/t) - t/(b*TBus))

normtDistrScore = sum([tDistrScore(t_i) for t_i in range(totNumTime)])

#normtDistrScore_np = sum([tDistrScore(t_i) for t_i in range(100000)])

def tDistrScore_np(t):
    t = t/30.
    t[t == 0] = 1e-10
    a = 0.2; #0.12 0.15 0.19
    b = 0.7;#0.77 0.74 0.69
    N= 2.5;#1.89 2.11 2.52
    TBus = 67.;#73.3*60  73.5*60 75.3*60
    return N * np.exp(-((a*TBus)/t) - t/(b*TBus))

@njit()
def tDistrScoreGall(t):
    t /= 60.
    c = 36.
    b = 9.3
    return math.exp(c/b) * (1. - math.exp(-t/c)) * math.exp( -t/b - c * math.exp(-t/c) / b ) / b
normtDistrScoreGall = sum([tDistrScoreGall(t_i) for t_i in range(totNumTime)])

@njit()
def tDistrScore1h(t):
    if(t < 3600):
        return 1./3600.
    else:
        return 0
    return 0
normtDistrScore1h = sum([tDistrScore1h(t_i) for t_i in range(totNumTime)])

@njit()
def normed_tDistrScore(t):
    global normtDistrScore
    return tDistrScore(t) / normtDistrScore

@njit()
def normed_tDistrScoreGall(t):
    global normtDistrScoreGall
    return tDistrScoreGall(t) / normtDistrScoreGall

@njit()
def normed_tDistrScore1h(t):
    global normtDistrScore1h
    return tDistrScore1h(t) / normtDistrScore1h



@njit()
def areaTimeCompute(timePR):
    aTime = np.full(totNumTime, 0., dtype = np.float64)
    for i in range(len(timePR)):
        t = timePR[i]
        if t < totNumTime:
            aTime[int(t)] += 1
        else:
            pass
    return aTime

@njit(int64[:](int64[:],int64[:]))
def arrayTimeCompute(timePR, arrayW):
    aTime = np.full(totNumTime, 0., dtype = np.int64)
    for i in range(len(timePR)):
        t = timePR[i]
        if t < totNumTime:
            aTime[t] += arrayW[i]           
        else:
            pass
    return aTime


def computeVelocityScore(distr):
    @njit()
    def computeVel(timePReached, areaHex):
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
    @njit(float64(int64[:],int64[:]), parallel=True)
    def computeSoc(timePReached, arrayW):
        popComul = 0
        popMean = 0
        popsTime = arrayTimeCompute(timePReached, arrayW)
        for time_i in prange(len(popsTime)):
            popComul += popsTime[time_i];
            popMean += distr(time_i) * popComul;
        return popMean
    return computeSoc

@njit()
def timeVelocity(timePReached, data):
    timeListToSave = data["timeListToSave"]
    areaHex = data['areaHex']
    areasTime = areaTimeCompute(timePReached)
    res = {'timeList':timeListToSave, 'velocity':[]}
    for time2Save in timeListToSave:
        area = sum(areasTime[0:time2Save]) * areaHex
        res["velocity"].append((3600./time2Save)*(math.sqrt(area/math.pi)))
    return res

@njit()
def timeSociality(timePReached, data):
    timeListToSave = data["timeListToSave"]
    arrayW = data['arrayPop']
    popsTime = arrayTimeCompute(timePReached, arrayW)
    res = {'timeList':timeListToSave, 'sociality':[]}
    for time2Save in timeListToSave:
        pop = sum(popsTime[0:time2Save])
        res["sociality"].append(pop)
    return res

@njit()
def average_quantity(quantity, weight):
    avg = 0
    norm = 0
    for i_q, q in enumerate(quantity):
        avg += q * weight[i_q]
        norm += weight[i_q]
    return avg / norm
    
def average_vel_soc(list_hexs):
    vels = [x["vel_score"] for x in list_hexs]
    socs = [x["soc_score"] for x in list_hexs]
    w_vel = [1] * len(list_hexs)
    w_soc = [x["pop"] for x in list_hexs]
    avg_vel = average_quantity(vels, w_vel)
    avg_soc = average_quantity(socs, w_soc)
    return {"avg_vel":avg_vel, "avg_soc":avg_soc}


#********************************* NOT WORKING ***********************************

def fast_compute_vel(h_time, areaHex, distr = tDistrScore_np, bins = 4*3600):
    h_time_hist, _ = np.histogram(h_time, bins = bins, range=(0, bins))
    h_time_range = np.arange(bins)
    h_dist = distr(h_time_range)
    v_vec = h_dist / (h_time_range+ 1e-10)
    v_vec = v_vec * np.sqrt(h_time_hist.cumsum() * areaHex / np.pi)
    v_score = np.sum(v_vec) / np.sum(h_dist)
    v_score *= 3600
    return v_score

def fast_compute_vel2(h_time, areaHex, h_dist, h_time_range, bins = 4*3600):
    h_time = h_time[h_time < bins]
    h_time_range_short, h_time_hist_short = np.unique(h_time, return_counts = True)
    h_time_hist = np.zeros(bins)
    h_time_hist[h_time_range_short] = h_time_hist_short
    v_vec = h_dist / (h_time_range+ 1e-10)
    v_vec = v_vec * np.sqrt(h_time_hist.cumsum() * areaHex / np.pi)
    v_score = np.sum(v_vec) / np.sum(h_dist)
    v_score *= 3600
    return v_score


def fast_compute_soc(h_time, array_pop, distr = tDistrScore_np, bins = 4*3600):
    h_time_hist, _ = np.histogram(h_time, bins = bins, range=(0, bins), weights=array_pop)
    h_time_range = np.arange(bins)
    h_dist = distr(h_time_range)
    s_vec = h_time_hist.cumsum() * h_dist
    s_score = np.sum(s_vec) / np.sum(h_dist)
    return s_score



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


