import math 
from geopy.distance import vincenty,great_circle
from shapely.geometry import Polygon, MultiPolygon, Point, mapping

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
    return vincenty((one[1],one[0]),(two[1], two[0])).kilometers #dist in meter 
    #return  great_circle(one, two).angle
def dist4Point(one, two): #one=(point,point)
    one = one['coordinates']
    two = two['coordinates']
    return vincenty((one[1],one[0]),(two[1], two[0])).kilometers #dist in meter 

cosines = []
sines = []
for i in range(0, 6):
    angle = 2. * math.pi/6. * i
    cosines.append(math.cos(angle))
    sines.append(math.sin(angle))
    
def hexagonalGrid(bbox, cell,gtfsDBStops, distanceS, city):
    xFraction = cell / (dist2Point( (bbox[0], bbox[1]), (bbox[2], bbox[1]) ))
    cellWidth = xFraction * (bbox[2] - bbox[0])
    yFraction = cell / (dist2Point( (bbox[0], bbox[1]), (bbox[0], bbox[3]) ))
    cellHeight = yFraction * (bbox[3] - bbox[1])
    radius = cellWidth / 2.

    hex_width = radius * 2.
    hex_height = math.sqrt(3.)/2. * cellHeight

    box_width = bbox[2] - bbox[0]
    box_height = bbox[3] - bbox[1]

    x_interval = 3./4. * hex_width
    y_interval = hex_height

    x_span = box_width / (hex_width - radius/2.)
    x_count = int(math.ceil(x_span))
    if round(x_span) == x_count: 
        x_count += 1
  

    x_adjust = ((x_count * x_interval - radius/2.) - box_width)/2. - radius/2.

    y_count = int(math.ceil(box_height / hex_height))

    y_adjust = (box_height - y_count * hex_height)/2.

    hasOffsetY = y_count * hex_height - box_height > hex_height/2.
    #print hasOffsetY
    if hasOffsetY: 
        y_adjust -= hex_height/4.

    fc = []
    listPoint = []
    print( x_count, y_count, x_count*y_count)
    count_ins = 0
    for x in range(0, x_count):
        for y in range(0,y_count+1):
            isOdd = x % 2 == 1
            #print isOdd
            if y == 0 and isOdd:
                continue
            if y == 0 and hasOffsetY:
                continue

            center_x = x * x_interval + bbox[0] - x_adjust
            center_y = y * y_interval + bbox[1] + y_adjust

            if isOdd:
                center_y -= hex_height/2
                
        
            lonLatStart = [center_x, center_y]
            
            searchNear ={
                'city' : city,
                'point' : {'$near': {
                 '$geometry': {
                    'type': "Point" ,
                    'coordinates': lonLatStart
                 },
                 '$maxDistance': distanceS,
                 '$minDistance': 0
              }},
                    }
            StopsCount =  gtfsDBStops.find(searchNear).count()

            #print tempUrl[:-1] + '?sources=0'
            if(StopsCount>0):           
                myhex = myhexagon([center_x, center_y], cellWidth / 2., cellHeight / 2.)
                listPoint.append({ "point" : {"type": "Point", "coordinates": [center_x, center_y]},
                                   'hex' : mapping(myhex),
                                  'city': city,
                                  'served':True,
                                  'pos' : count_ins,
                                 })
                fc.append(myhex)
                count_ins+=1
                    
            print ('{0}%, tot = {1}, inserted = {2}'.format((float(x*y_count)+float(y))/(x_count*y_count),(float(x*y_count)+float(y)) , count_ins),end="\r")
    
    return MultiPolygon(fc), listPoint

#Utility function for isochrone generation 
import folium
shellIso = [-1, 0, 900, 1800, 2700, 3600,4500, 5400, 6300,7200, 1000000000]
colorIso = list(reversed(['#a50026','#d73027','#f46d43','#fdae61','#fee090','#e0f3f8','#abd9e9','#74add1','#4575b4','#313695']));

def reduceGeojsonInShell(hexs,field, color = colorIso, shell = shellIso):
    latlngCenter = [hexs[0]['hex']['coordinates'][0][0][1], hexs[0]['hex']['coordinates'][0][0][0]]
    map_osm = folium.Map(location=latlngCenter, zoom_start=9)
    FeatureCollection = {'type':'FeatureCollection', 'features':[]};
    
    for i, lim in enumerate(shell[:-1]):
        listPol = []
        find = [p['hex'] for p in hexs if (p[field] > shell[i] and p[field] <= shell[i+1])]
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

