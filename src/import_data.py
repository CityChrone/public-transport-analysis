import zipfile
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
import pickle
import bz2

def name2pos(stops_info, y):
    if y in stops_info["name2pos"]:
        return stops_info["name2pos"][y]
    else:
        return "not found"

def read_connections(stops_info, name_city="adelaide", path_dir = "./data/", time_zone='Australia/Adelaide'):
    name_file = path_dir + name_city + ".zip"
    archive = zipfile.ZipFile(name_file, 'r')
    archive.namelist()
    row_data = archive.open(name_city+"/network_temporal_day.csv", mode='r')
    res = pd.read_csv(row_data, sep=";")
    res = res.sort_values('dep_time_ut')
    res['from_stop_pos'] = res.apply(lambda row: name2pos(stops_info, row['from_stop_I']), axis=1)
    res['to_stop_pos'] = res.apply(lambda row: name2pos(stops_info, row['to_stop_I']), axis=1)
    time_epoch = res['dep_time_ut'].min()
    tz = pytz.timezone(time_zone)
    dt = datetime.fromtimestamp(time_epoch, tz)
    to_sub = time_epoch -(dt.hour*3600 + dt.minute*60 + dt.second)
    dt_see = datetime.fromtimestamp(to_sub, tz)
    res['dep_time'] = res['dep_time_ut'] - to_sub
    res['arr_time'] = res['arr_time_ut'] - to_sub
    return res

def read_wp(stops_info, name_city="adelaide", path_dir = "./data/"):
    walking_speed = 1.4 #m/s
    name_file = path_dir + name_city + ".zip"
    archive = zipfile.ZipFile(name_file, 'r')
    row_data = archive.open(name_city+"/network_walk.csv", mode='r')
    res = pd.read_csv(row_data, sep=";")
    res["walk_time"] = res.d_walk / walking_speed
    res = res.astype(int)
    res['from_stop_pos'] = res.apply(lambda row: name2pos(stops_info, row['from_stop_I']), axis=1)
    res['to_stop_pos'] = res.apply(lambda row: name2pos(stops_info, row['to_stop_I']), axis=1)
    res = res[res.from_stop_pos != "not found"]
    res = res[res.to_stop_pos != "not found"]
    num_stops = len(stops_info["pos2name"])
    max_number_neigh = max(res['from_stop_pos'].value_counts())
    wp_stops = np.full((num_stops, max_number_neigh), -2, dtype = np.int64)
    wp_times = np.full((num_stops, max_number_neigh), -2,dtype = np.int64)
    group_stop = res.groupby('from_stop_pos')['to_stop_pos'].apply(list)
    group_stop_time = res.groupby('from_stop_pos')['walk_time'].apply(list)
    for stop_pos in group_stop.keys():
        neigh = group_stop[stop_pos]
        for i_n, n in enumerate(neigh):
            wp_stops[stop_pos][i_n] = neigh[i_n]
            wp_times[stop_pos][i_n] = group_stop_time[stop_pos][i_n]
    return res, wp_stops, wp_times

def read_stop(name_city="adelaide", path_dir = "./data/"):
    name_file = path_dir + name_city + ".zip"
    archive = zipfile.ZipFile(name_file, 'r')
    row_data = archive.open(name_city+"/network_nodes.csv", mode='r')
    stops_df = pd.read_csv(row_data, sep=";")
    stops_pos_name = {}
    stops_name_pos = {}
    for pos in stops_df["stop_I"].keys():
        stops_pos_name[pos] = stops_df["stop_I"][pos]
        stops_name_pos[stops_df["stop_I"][pos]] = pos    
    return {"stops_info":stops_df, "pos2name":stops_pos_name, "name2pos":stops_name_pos}



def save_pickle_zip(filename, myobj):
    """
    save object to file using pickle
    
    @param filename: name of destination file
    @type filename: str
    @param myobj: object to save (has to be pickleable)
    @type myobj: obj
    """

    f = bz2.BZ2File(filename, 'wb')

    pickle.dump(myobj, f, protocol=2)
    f.close()



def load_pickle_zip(filename):
    """
    Load from filename using pickle
    
    @param filename: name of file to load from
    @type filename: str
    """

    f = bz2.BZ2File(filename, 'rb')

    myobj = pickle.load(f)
    f.close()
    return myobj
