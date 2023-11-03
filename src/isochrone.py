import datetime
import numpy as np
import icsa
import accessibilities
import torch
from multiprocessing import Pool, Manager, cpu_count


def hex_isochrone(start_hex, start_time, wp, conn_list):
    wp_hh_pos = wp["wp_hh_pos"]
    wp_hh_time = wp["wp_hh_time"]
    wp_hs_pos = wp["wp_hs_pos"]
    wp_hs_time = wp["wp_hs_time"]
    wp_ss_pos = wp["wp_ss_pos"]
    wp_ss_time = wp["wp_ss_time"]

    arrival_stops_times = np.full(
        wp_ss_pos.shape[0], 100000000, dtype=np.int64)
    arrival_hexs_times = np.full(wp_hh_pos.shape[0], 100000000, dtype=np.int64)
    arrival_hexs_times[start_hex] = start_time

    hex_n = wp_hh_pos[start_hex]
    # loop in the hexs near to the selected hexs
    for n_i, n in enumerate(hex_n[hex_n != -2]):
        arrival_hexs_times[n] = wp_hh_time[start_hex][n_i] + start_time

    stops_n = wp_hs_pos[start_hex]
    for n_i, n in enumerate(stops_n[stops_n != -2]):
        # loop in the stops near to the selected hexs
        arrival_stops_times[n] = wp_hs_time[start_hex][n_i] + start_time

    arrival_stops_times = icsa.coreICSA(arrival_stops_times,
                                        conn_list,
                                        wp_ss_pos, wp_ss_time)
    arrival_hexs_times = icsa.computePointTime(arrival_hexs_times,
                                               arrival_stops_times,
                                               wp_hs_pos,
                                               wp_hs_time)

    arrival_hexs_times = arrival_hexs_times - start_time
    return arrival_hexs_times


def stop_isochrone(start_stop, start_time, wp, conn_list):
    wp_hh_pos = wp["wp_hh_pos"]
    wp_hh_time = wp["wp_hh_time"]
    wp_hs_pos = wp["wp_hs_pos"]
    wp_hs_time = wp["wp_hs_time"]
    wp_ss_pos = wp["wp_ss_pos"]
    wp_ss_time = wp["wp_ss_time"]

    arrival_stops_times = np.full(
        wp_ss_pos.shape[0], 100000000, dtype=np.int64)
    arrival_hexs_times = np.full(wp_hh_pos.shape[0], 100000000, dtype=np.int64)
    arrival_stops_times[start_stop] = start_time

    arrival_stops_times = icsa.coreICSA(arrival_stops_times,
                                        conn_list,
                                        wp_ss_pos, wp_ss_time)
    arrival_hexs_times = icsa.computePointTime(arrival_hexs_times,
                                               arrival_stops_times,
                                               wp_hs_pos,
                                               wp_hs_time)

    arrival_hexs_times = arrival_hexs_times - start_time
    return arrival_hexs_times


def compute_isochrone(list_hexs, start_hex, start_time, wp,
                      conn_list, array_pop,
                      area_hex,
                      sociality_func=accessibilities.ListFunctionAccessibility["socialityScore"],
                      velocity_func=accessibilities.ListFunctionAccessibility["velocityScore"]):

    while start_hex+n_parallel <= len(list_hexs):
        arrival_hexs_times = hex_isochrone(
            start_hex, start_time, wp, conn_list)
        soc = sociality_func(arrival_hexs_times, array_pop)
        vel = velocity_func(arrival_hexs_times, area_hex)
        list_temp = []
        list_temp = list_hexs[start_hex]
        list_temp["vel_score"] = vel
        list_temp["soc_score"] = soc
        list_hexs[start_hex] = list_temp
        start_hex += n_parallel


def loop_isochrone(start_hex, start_time, wp, conn_list, list_hexs, array_pop, area_hex, velocity_func, sociality_func):
    arrival_hexs_times = hex_isochrone(start_hex, start_time, wp, conn_list)
    # print(arrival_hexs_times, array_pop)

    # Ensure the inputs are numpy arrays of the correct type
    arrival_hexs_times_array = np.array(arrival_hexs_times, dtype=np.int64)
    array_pop_array = np.array(array_pop, dtype=np.int64)

    # Call the sociality function with the correctly typed arrays
    soc = sociality_func(arrival_hexs_times_array, array_pop_array)

    vel = velocity_func(arrival_hexs_times, area_hex)
    list_hexs[start_hex]["vel_score"] = vel
    list_hexs[start_hex]["soc_score"] = soc


def compute_all_isochrone(list_hexs, start_time, wp,
                          conn_list, array_pop,
                          area_hex,
                          sociality_func=accessibilities.ListFunctionAccessibility["socialityScore"],
                          velocity_func=accessibilities.ListFunctionAccessibility["velocityScore"]
                          ):
    for start_hex in range(len(list_hexs)):
        loop_isochrone(start_hex, start_time, wp, conn_list, list_hexs,
                       array_pop, area_hex, velocity_func, sociality_func)
        # print(soc, vel)

    return list_hexs


def compute_time_dist(dist_time_init, start_time, new_stops, wp, conn_list, delta_time=2*3600):
    num_hexs = len(dist_time_init)
    dist_time_stop = dist_time_init.clone().detach()
    for new_stop in new_stops:
        # print(new_stop)
        stop2hex = torch.tensor(stop_isochrone(
            new_stop, start_time, wp, conn_list), dtype=torch.int64)
        stop2hex = stop2hex.repeat(num_hexs, 1)
        dist_time_stop_temp = stop2hex + stop2hex.t()
        dist_time_stop_temp[dist_time_stop_temp > delta_time] = 100000000
        dist_time_stop = torch.min(dist_time_stop, dist_time_stop_temp)
    return dist_time_stop


def torch_accessibilities(time_dist, list_hex_torch, array_pop, area_hex,
                          # sociality_func = fast_compute_soc,
                          # velocity_func = fast_compute_vel,
                          # ):
                          velocity_func=accessibilities.ListFunctionAccessibility['velocityScore'],
                          sociality_func=accessibilities.ListFunctionAccessibility['socialityScore'],):

    time_dist = time_dist.numpy()
    socs = [sociality_func(time_dist[h], array_pop)
            for h in range(len(time_dist))]
    vels = [velocity_func(time_dist[h], area_hex)
            for h in range(len(time_dist))]
    # print(soc, soc, list_hex_torch[h]["vel_score"], soc == list_hex_torch[h]["vel_score"])

    for h in range(len(time_dist)):
        list_hex_torch[h]["vel_score"] = vels[h]
        list_hex_torch[h]["soc_score"] = socs[h]

    return list_hex_torch


def compute_all_isochrone_fast(list_hex_torch,
                               start_time,
                               wp,
                               conn_list,
                               array_pop,
                               area_hex,
                               dist_time_init,
                               new_stops,
                               delta_time=2*3600):

    dist_time_stop = compute_time_dist(dist_time_init,
                                       start_time,
                                       new_stops,
                                       wp,
                                       conn_list,
                                       delta_time=2*3600)
    res = torch_accessibilities(
        dist_time_stop, list_hex_torch, array_pop, area_hex)
    return res
