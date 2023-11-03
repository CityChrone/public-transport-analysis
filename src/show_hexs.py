import math 
from geopy.distance import geodesic,great_circle
from shapely.geometry import Polygon, MultiPolygon, Point, mapping
import pymongo as pym
import requests
import seaborn as sns
import folium
import numpy as np

#utility function fro making hexGrid

#Center should be [x, y]
def myhexagon(center, rx, ry):
    vertices = []
    for i in range(0,6):
        x = center[0] + rx * cosines[i]
        y = center[1] + ry * sines[i]
        vertices.append([x,y])
                        
    #first and last vertex must be the same
    vertices.append(vertices[0])
    return Polygon(vertices)

def dist2Point(one, two): #one=(lat,lon)
    return geodesic((one[1],one[0]),(two[1], two[0])).kilometers #dist in meter 
    #return  great_circle(one, two).angle
def dist4Point(one, two): #one=(point,point)
    one = one['coordinates']
    two = two['coordinates']
    return geodesic((one[1],one[0]),(two[1], two[0])).kilometers #dist in meter 


cosines = []
sines = []
for i in range(0, 6):
    angle = 2. * math.pi/6. * i
    cosines.append(math.cos(angle))
    sines.append(math.sin(angle));
 
  
def find_extreme_plot(list_hexs, pos = 0):
    vals = [x["point"]["coordinates"][pos] for x in list_hexs]
    return min(vals)*(1.-1e-2), max(vals)*(1.+1e-2)
def give_x_y_points(list_stops):
    x = []
    y = []
    for s in list_stops:
        x.append(s["point"]["coordinates"][0])
        y.append(s["point"]["coordinates"][1])
    return x, y

def show_stops_map(new_list_stops, list_hexs, 
                   show_hex=False, diff=False):
    lons = [x["point"]["coordinates"][0] for x in new_list_stops]
    lats = [x["point"]["coordinates"][1] for x in new_list_stops]
    loc = [np.mean(lats), np.mean(lons)]
    color = {}
    if show_hex:
        if diff:
            for h in list_hexs:
                h["diff"] = h["vel_score"] - h["vel0"]
                if h["diff"] < 0:
                    print("error negative diff {0}".format(h["diff"]))
            shell = np.arange(0,3,0.2);
            color = list(reversed(sns.color_palette("GnBu_d", n_colors=len(shell)+1).as_hex()))
            [FeatureCollection, map_osm] = reduceGeojsonInShell(
                    list_hexs, "diff", shell=shell, color=color,  )
        else:
            color = ['#993404', "#f16913", "#fdae6b", '#74c476', '#31a354', '#006d2c', "#6baed6", "#4292c6", "#2171b5", '#08519c', '#f768a1', '#dd3497', '#ae017e', '#49006a'];
            shell = [0., 2., 4., 5, 6., 7, 8., 9, 10., 11, 12., 13, 15, 17.];
            [FeatureCollection, map_osm] = reduceGeojsonInShell(
            list_hexs, "vel_score", shell=shell, color=color)
    else:
        map_osm = folium.Map(
        location = loc,
        zoom_start = 11)
    polyline_ = []
    map_osm.zoom_start = 11
    map_osm.location = loc
    for s in new_list_stops:
        l = list(reversed(s["point"]["coordinates"]))
        polyline_.append(l)
        folium.Marker(location=l).add_to(map_osm)
    folium.PolyLine(locations=polyline_).add_to(map_osm)
    return map_osm, color


#show ehxs 
def showHexs(gtfsDB, city, zoom_start = 9):
    lonlat = gtfsDB['points'].find_one({'served':True, 'city':city})['point']['coordinates']
    latlon = [lonlat[1], lonlat[0]]
    map_osm = folium.Map(location=latlon, zoom_start=zoom_start)
    listHex = []
    for point in gtfsDB['points'].find({'served':True, 'city':city}, {'pointN':0, 'stopN':0}):
        listHex.append(point)
    res = unionHexs(listHex)
    map_osm.choropleth(res, fill_color='red',fill_opacity=0.6, line_color='null',line_weight=2, line_opacity=0)
    return map_osm

#Utility function for isochrone generation 

import folium
shellIso = [-1, 0, 900, 1800, 2700, 3600,4500, 5400, 6300,7200, 1000000000]
colorIso = list(reversed(['#a50026','#d73027','#f46d43','#fdae61','#fee090','#e0f3f8','#abd9e9','#74add1','#4575b4','#313695']));


def reduceGeojsonInShell(hexs, field, color = colorIso, shell = shellIso):
    num_h = len(hexs)
    num_c = int(num_h/2)
    latlngCenter = [hexs[num_c]['hex']['coordinates'][0][0][1], hexs[num_c]['hex']['coordinates'][0][0][0]]
    map_osm = folium.Map(location=latlngCenter, zoom_start=11)
    FeatureCollection = {'type':'FeatureCollection', 'features':[]};
    
    for i, lim in enumerate(shell[:-1]):
        listPol = []
        find = [p for p in hexs if (p[field] > shell[i] and p[field] <= shell[i+1])]
        if len(find) > 0:
            geojson = unionHexs(find)
            geojson['properties'] =  {field: (lim + shell[i+1])/2.}
            FeatureCollection['features'].append(geojson)
            map_osm.choropleth(geojson, fill_color=color[i],fill_opacity=0.6, line_color=color[i],line_weight=2, line_opacity=0,)
            
    return [FeatureCollection, map_osm]

def reduceGeojsonInShellSubField(hexs,field1,field2, color = colorIso, shell = shellIso):
    latlngCenter = [hexs[0]['hex']['coordinates'][0][0][1], hexs[0]['hex']['coordinates'][0][0][0]]
    map_osm = folium.Map(location=latlngCenter, zoom_start=9)
    FeatureCollection = {'type':'FeatureCollection', 'features':[]};
    for i, lim in enumerate(shell[:-1]):
        listPol = []
        find = [p for p in hexs if (p[field1][field2] >= shell[i] and p[field1][field2] < shell[i+1])]
        if len(find) > 0:
            geojson = unionHexs(find)
            geojson['properties'] =  {field1+'.'+field2: (lim + shell[i+1])/2.}
            print('shell {0}-{1} -> {2} hexs'.format(shell[i],shell[i+1],len(find)))
            FeatureCollection['features'].append(geojson)
            map_osm.choropleth(geojson, fill_color=color[i],fill_opacity=0.6, line_color=color[i],line_weight=2, line_opacity=0,)
            
    return [FeatureCollection, map_osm]



import numpy

limNum = 8 
def seg2str(seg,rev=False):
    seg = [[round(seg[0][0],limNum),round(seg[0][1],limNum)],[round(seg[1][0],limNum),round(seg[1][1],limNum)]]
    if  (seg[0][0]+seg[0][1] < seg[1][0]+seg[1][1]):
        if rev:
            seg = [seg[1],seg[0]]
    else:
        if not rev:
            seg = [seg[1],seg[0]]
    return str(seg)

def p2str(seg):
    seg = [round(seg[0],limNum),round(seg[1],limNum)]
    return str(seg)

def segRound(seg):
    seg = [[round(seg[0][0],limNum),round(seg[0][1],limNum)],[round(seg[1][0],limNum),round(seg[1][1],limNum)]]
    return seg

from numba import jit, int32

def MultyPolLabel(listCluster):
    geoJsonMultiPol = {'type':'MultiPolygon', 'coordinates' : []}
    for label in listCluster:
        listPol = []
        while len(listCluster[label]) != 0:
            pol = []
            cluster = listCluster[label]
            startPoint = next(iter(cluster.keys()))
            iterOverP = next(iter(cluster[startPoint].values()))
            pointFrom = iterOverP[0]
            pointTo = iterOverP[1]
            pol.append(pointFrom)
            #print 'while 1', cluster.keys()
            #del listCluster[label][startPoint]
            while True:
                if pointTo != pol[0]:
                    pol.append(pointTo)
                    startPoint = str(pointTo)
                    #print '\n from -> to', pointFrom, pointTo
                    #print 'pol',pol
                    for keyStr in cluster[startPoint]:               
                        if keyStr != str(pointFrom):
                            if cluster[startPoint][keyStr][0] != pointTo:
                                pointFrom = pointTo
                                pointTo = cluster[startPoint][keyStr][0] 
                            else:
                                pointFrom = pointTo
                                pointTo = cluster[startPoint][keyStr][1] 
                            break
                    del listCluster[label][startPoint]
                else:
                    #print listCluster[label]
                    del listCluster[label][str(pointTo)]
                    listPol.append(pol)
                    break
        maxLen = 0
        maxIndex = 0
        for i in range(len(listPol)):
            if maxLen < len(listPol[i]):
                maxLen = len(listPol[i])
                maxIndex = i
        listPol.insert(0, listPol.pop(maxIndex))
        geoJsonMultiPol['coordinates'].append(listPol)
    return geoJsonMultiPol
#print geoJsonMultiPol   

def unionHexs(hexs):
    listSeg = {} 
    listLabel = {}
    #print 'start erasing...'
    for p in hexs:
        label = p['pos']
        hexagon = p['hex']['coordinates'][0]
        #print label
        for i,coor in enumerate(hexagon[:-1]):
            seg = [hexagon[i],hexagon[i+1]]
            keySeg =seg2str(seg) 
           
            if keySeg in listSeg:
                newLabel = listSeg[keySeg]['label']
                if(newLabel != label):
                    #print "remove", label, newLabel

                    listLabel[newLabel].extend(listLabel[label])
                    for segInCluster in listLabel[label]:
                        try:
                            listSeg[segInCluster['keySeg']]['label'] = newLabel
                        except:
                            pass
                            #print 'except', newLabel
                    del listLabel[label]
                    label = newLabel
                del listSeg[keySeg]
            else:
                listSeg[keySeg] = {'label':label,'latlng':segRound(seg)}
                try:
                    listLabel[label].append({'keySeg':keySeg,'latlng':segRound(seg)})
                except:
                    listLabel[label] = [{'keySeg':keySeg,'latlng':segRound(seg)}]
    
    #print 'end erasing... start clustering'

    listCluster = {}
    listClusterRev = {}
    
    for keySeg in listSeg:
        seg = listSeg[keySeg]
        segKey = seg2str(seg['latlng'])
        segKeyRev = seg2str(seg['latlng'], rev=True)
        latlng = seg['latlng']
        try:
            listCluster[seg['label']][p2str(latlng[0])][p2str(latlng[1])] = latlng
        except:
            try:
                listCluster[seg['label']][p2str(latlng[0])] = {p2str(latlng[1])  : latlng}
            except:
                listCluster[seg['label']] = {p2str(latlng[0]) : {p2str(latlng[1])  : latlng}}                   
        try:
            listCluster[seg['label']][p2str(latlng[1])][p2str(latlng[0])] = latlng
        except:
            try:
                listCluster[seg['label']][p2str(latlng[1])] = {p2str(latlng[0])  : latlng}
            except:
                listCluster[seg['label']] = {p2str(latlng[1]) : {p2str(latlng[0])  : latlng}}
    
    #print 'end clustering... start polygonizing'
       
    return MultyPolLabel(listCluster)


import pyproj    
import shapely
import shapely.ops as ops
from shapely.geometry.polygon import Polygon
from functools import partial

def area_geojson(geoJ):
    if(geoJ['type'] == 'Polygon'):
        geom = Polygon(geoJ['coordinates'][0])
        geom_area = ops.transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init='EPSG:4326'),
                pyproj.Proj(
                    proj='aea',
                    lat1=geom.bounds[1],
                    lat2=geom.bounds[3])),
            geom)

    # Print the area in m^2
    return geom_area.area  / 1.e6

