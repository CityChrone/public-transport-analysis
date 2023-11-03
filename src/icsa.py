from numba import jit, int32, int64
import math
import time
import numpy as np

inf = 10000000


@jit(int64[:](int64[:], int64[:], int64[:, :], int64[:, :]), nopython=True)
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


@jit(int64[:](int64[:], int64[:, :], int64[:, :], int64[:, :]), nopython=True)
def coreICSA(arrival_times, connections, wp_stops, wp_time):
    count = 0
    arrival_times_wp = np.copy(arrival_times)
    for c_i in range(len(connections)):
        c = connections[c_i]
        s_start = c[2]
        if arrival_times[s_start] <= c[0] or arrival_times_wp[s_start] <= c[0]:
            count += 1
            s_arr = c[3]
            if arrival_times[s_arr] > c[1]:
                arrival_times[s_arr] = c[1]
                for neigh_i, neigh in enumerate(wp_stops[s_arr]):
                    if neigh != -2:
                        arrival_times_wp[neigh] = min(
                            arrival_times_wp[neigh], c[1] + wp_time[s_arr][neigh_i])
                    else:
                        break

    for i, t in enumerate(arrival_times):
        if t > arrival_times_wp[i]:
            arrival_times[i] = arrival_times_wp[i]
    return arrival_times


@jit(int64[:](int64[:], int64[:, :], int64[:, :], int64[:, :]), nopython=True)
def coreCSA(arrival_times, connections, wp_stops, wp_time):
    count = 0
    for c_i in range(len(connections)):
        c = connections[c_i]
        s_start = c[2]
        if arrival_times[s_start] <= c[0]:
            count += 1
            s_arr = c[3]
            if arrival_times[s_arr] > c[1]:
                arrival_times[s_arr] = c[1]
                for neigh_i, neigh in enumerate(wp_stops[s_arr]):
                    if neigh != -2:
                        arrival_times[neigh] = min(
                            arrival_times[neigh], c[1] + wp_time[s_arr][neigh_i])
                    else:
                        break
    return arrival_times


def ICSA(start_stop, conn, wp_stops, wp_times, start_time=3600*8):
    conn_list = conn[["dep_time", "arr_time",
                      "from_stop_pos", "to_stop_pos"]].values
    arrival_times = np.full(len(wp_stops), 100000000, dtype=np.int64)
    arrival_times[start_stop] = start_time
    return coreICSA(arrival_times, conn_list, wp_stops, wp_times)


def ICSA(start_stop, conn, wp_stops, wp_times, start_time=3600*8):
    conn_list = conn[["dep_time", "arr_time",
                      "from_stop_pos", "to_stop_pos"]].values
    arrival_times = np.full(len(wp_stops), 100000000, dtype=np.int64)
    arrival_times[start_stop] = start_time
    return coreICSA(arrival_times, conn_list, wp_stops, wp_times)


def CSA(start_stop, conn, wp_stops, wp_times, start_time=3600*8):
    conn_list = conn[["dep_time", "arr_time",
                      "from_stop_pos", "to_stop_pos"]].values
    arrival_times = np.full(len(wp_stops), 100000000, dtype=np.int64)
    arrival_times[start_stop] = start_time
    return coreCSA(arrival_times, conn_list, wp_stops, wp_times)


def coreICSA_no_numba(arrival_times, connections, wp_stops,
                      wp_time, limit_walking_path):
    count = 0
    arrival_times_wp = np.copy(arrival_times)
    sum_wp = np.full(len(arrival_times), 0, dtype=np.int64)
    for c_i in range(len(connections)):
        c = connections[c_i]
        s_start = c[2]
        if arrival_times[s_start] <= c[0] or arrival_times_wp[s_start] <= c[0]:
            count += 1
            s_arr = c[3]
            if arrival_times[s_arr] > c[1]:
                arrival_times[s_arr] = c[1]
                for neigh_i, neigh in enumerate(wp_stops[s_arr]):
                    if neigh != -2:
                        wp_temp = wp_time[s_arr][neigh_i]
                        arr_t = arrival_times_wp[neigh]
                        if wp_temp + sum_wp[s_arr] <= limit_walking_path:
                            arrival_times_wp[neigh] = min(
                                arr_t, c[1] + wp_temp)
                            sum_wp[neigh] = wp_temp + sum_wp[s_arr]
                    else:
                        break
    arrival_time_stop = arrival_times.copy()
    print(np.mean(sum_wp))

    for i, t in enumerate(arrival_times):
        if t > arrival_times_wp[i]:
            arrival_times[i] = arrival_times_wp[i]
    return arrival_times


def ICSA_no_numba(start_stop, conn, wp_stops, wp_times, start_time=3600*8, limit_walking_path=1e100):
    conn_list = conn[["dep_time", "arr_time",
                      "from_stop_pos", "to_stop_pos"]].values
    arrival_times = np.full(len(wp_stops), 100000000, dtype=np.int64)
    arrival_times[start_stop] = start_time
    return coreICSA_no_numba(arrival_times, conn_list, wp_stops, wp_times, limit_walking_path)
