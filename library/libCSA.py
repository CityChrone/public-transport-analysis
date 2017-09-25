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
    
def myhexgrid2(bbox, cell,gtfsDBStops, distanceS, city):
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
                    
            print ('\r {0}%, tot = {1}, inserted = {2}'.format((float(x*y_count)+float(y))/(x_count*y_count),(float(x*y_count)+float(y)) , count_ins),end="\r")
    
    return MultiPolygon(fc), listPoint

def myhexgrid(bbox, cell):
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
            myhex = myhexagon([center_x, center_y], cellWidth / 2., cellHeight / 2.)
            listPoint.append({ "point" : {"type": "Point", "coordinates": [center_x, center_y]},
                               'hex' : mapping(myhex)
                             })
            fc.append(myhex)
                    
            print ('\r {0}%, tot = {1}, inserted = {2}'.format((float(x*y_count)+float(y))/(x_count*y_count),(float(x*y_count)+float(y)) , count_ins),end="\r")
    
    return MultiPolygon(fc), listPoint

#Utility function for isochrone generation 
import folium
shellIso = [-1, 0, 900, 1800, 2700, 3600,4500, 5400, 6300,7200, 1000000000]
colorIso = list(reversed(['#a50026','#d73027','#f46d43','#fdae61','#fee090','#e0f3f8','#abd9e9','#74add1','#4575b4','#313695']));

def reduceHexsInShell(hexs,field, color = colorIso, shell = shellIso):
    latlngCenter = [hexs[0]['hex']['coordinates'][0][0][1], hexs[0]['hex']['coordinates'][0][0][0]]
    tile = r'http://{s}.tile.thunderforest.com/transport/{z}/{x}/{y}.png'
    attribution = '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    map_osm = folium.Map(location=latlngCenter, zoom_start=9, tiles=tile, attr = attribution)
    FeatureCollection = {'type':'FeatureCollection', 'features':[]};
    
    for i, lim in enumerate(shell[:-1]):
        listPol = []
        #print '\r i : {0}, lim : {1}'.format(i, lim),
        find = [p for p in hexs if (p[field] > shell[i] and p[field] <= shell[i+1])]
        print (len(find), shell[i],shell[i+1])
        if len(find) > 0:
            #print '\r hex : {0}, i : {1}, lim : {2}, color {3}'.format(len(find), i, lim,color[i]),
            geojson = unionHexs(find)
            geojson['properties'] =  {field: (lim + shell[i+1])/2.}
            FeatureCollection['features'].append(geojson)
            map_osm.choropleth(geo_str=geojson, fill_color=color[i],fill_opacity=0.6, line_color=color[i],line_weight=2, line_opacity=0,)
            
    return [FeatureCollection, map_osm]

def reduceGeojsonInShell(hexs,field, color = colorIso, shell = shellIso):
    latlngCenter = [hexs[0]['hex']['coordinates'][0][0][1], hexs[0]['hex']['coordinates'][0][0][0]]
    tile = r'http://{s}.tile.thunderforest.com/transport/{z}/{x}/{y}.png'
    attribution = '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    map_osm = folium.Map(location=latlngCenter, zoom_start=9, tiles=tile, attr = attribution)
    FeatureCollection = {'type':'FeatureCollection', 'features':[]};
    
    for i, lim in enumerate(shell[:-1]):
        listPol = []
        #print '\r i : {0}, lim : {1}'.format(i, lim),
        find = [p['hex'] for p in hexs if (p[field] > shell[i] and p[field] <= shell[i+1])]
        print ('shell', len(find), shell[i],shell[i+1])
        if len(find) > 0:
            #print '\r hex : {0}, i : {1}, lim : {2}, color {3}'.format(len(find), i, lim,color[i]),
            geojson = unionHexsLow(find)
            geojson['properties'] =  {field: (lim + shell[i+1])/2.}
            FeatureCollection['features'].append(geojson)
            map_osm.choropleth(geo_str=geojson, fill_color=color[i],fill_opacity=0.6, line_color=color[i],line_weight=2, line_opacity=0,)
            
    return [FeatureCollection, map_osm]

def reduceGeojsonInShellSubField(hexs,field1,field2, color = colorIso, shell = shellIso):
    latlngCenter = [hexs[0]['hex']['coordinates'][0][0][1], hexs[0]['hex']['coordinates'][0][0][0]]
    tile = r'http://{s}.tile.thunderforest.com/transport/{z}/{x}/{y}.png'
    attribution = '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    map_osm = folium.Map(location=latlngCenter, zoom_start=9, tiles=tile, attr = attribution)
    FeatureCollection = {'type':'FeatureCollection', 'features':[]};
    shell
    for i, lim in enumerate(shell[:-1]):
        listPol = []
        #print '\r i : {0}, lim : {1}'.format(i, lim),
        find = [p for p in hexs if (p[field1][field2] >= shell[i] and p[field1][field2] < shell[i+1])]
        print ('shell', len(find), shell[i],shell[i+1],field1, field2, hexs[0][field1][field2])
        if len(find) > 0:
            #print '\r hex : {0}, i : {1}, lim : {2}, color {3}'.format(len(find), i, lim,color[i]),
            geojson = unionHexs(find)
            geojson['properties'] =  {field1+'.'+field2: (lim + shell[i+1])/2.}
            FeatureCollection['features'].append(geojson)
            map_osm.choropleth(geo_str=geojson, fill_color=color[i],fill_opacity=0.6, line_color=color[i],line_weight=2, line_opacity=0,)
            
    return [FeatureCollection, map_osm]



import numpy
def unionHexsLow(hexs):
    listPol = []
    for value in hexs:
        #print value
        
        if value['type'] == 'Polygon':
            for icoor2,coor2 in enumerate(value['coordinates'][0]):
            #print coor2, type(coor2[0])
                try:
                    value['coordinates'][0][icoor2] = [round(coor2[0],10), round( coor2[1],10) ]
                except:
                    break
            temp = shapely.geometry.Polygon(value['coordinates'][0])
            listPol.append(temp)
        elif value['type'] == 'MultiPolygon':
            #aa = []
            for i,pol in enumerate(value['coordinates']):
                for icoor2,coor2 in enumerate(pol[0]):
                    #print coor2, type(coor2[0])
                    try:
                        pol[0][icoor2] = [round(coor2[0],10), round( coor2[1],10) ]
                    except:
                        break
                temp = shapely.geometry.Polygon(pol[0])
                listPol.append(temp)
                #aa.append([])
                #aa[i].append(pol[0])
                #holes = []
                #for i_hole in numpy.arange(1, len(pol)):
                #    holes.append(pol[i_hole])
                #aa[i].append(holes)
                #MultiPol = aa
                #shapely.geometry.MultiPolygon(MultiPol)
    polyg = cascaded_union(shapely.geometry.MultiPolygon(listPol))
    return Feature(geometry=mapping(polyg))

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

def reduceHexsInShellFast(hexs, field, color = colorIso, shell = shellIso):
    listFeature = [];
    
    for i, lim in enumerate(shell[:-1]):
        listPol = []
        #print '\r i : {0}, lim : {1}'.format(i, lim),
        find = [p['hex'] for p in hexs if (p['t'] >= shell[i] and p['t'] < shell[i+1])]
        if find.count > 0:
            #print '\r hex : {0}, i : {1}, lim : {2}, color {3}'.format(len(find), i, lim,color[i]),
            step = 100;
            start = 0;
            end = (start + step) if (start + step < len(find)) else len(find);
            while end <= len(find):
                #print start, end, step, len(find)
                listPol = []
                for value in find[start:end]:
                    #print value
                    for icoor2,coor2 in enumerate(value['coordinates'][0]):
                        #print coor2, type(coor2[0])
                        value['coordinates'][0][icoor2] = [round(coor2[0],10), round( coor2[1],10) ]
                    temp = shapely.geometry.Polygon(value['coordinates'][0])
                    listPol.append(temp)
                polyg = cascaded_union(shapely.geometry.MultiPolygon(listPol))
                listFeature.append(Feature(geometry=mapping(polyg), properties={field: (lim + shell[i+1])/2.}))
                start = end;
                if start != len(find):
                    end = (start + step) if (start + step < len(find)) else len(find)
                else:
                    end = len(find) + 1
            #map_osm.choropleth(geo_str=geojson, fill_color=color[i],fill_opacity=0.6, line_color=color[i],line_weight=2, line_opacity=0,)
    result = FeatureCollection(listFeature)
    return result


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

from numba import jit, int32,int64

@jit(int32[:](int32[:],int32,int64[:,:],int32[:,:],int32[:,:]), nopython = True)
def tree(timesValues, timeStart, arrayCC, S2SPos, S2STime):
    #print 'inter'
    #global arrayCC
    #arrayCC = CC
    #global S2SPos
    #global S2STime
    count = 0
    for c_i in range(len(arrayCC)):
        c = arrayCC[c_i]
        if c[0] >= timeStart:
            Pstart_i = c[2]
            if timesValues[Pstart_i] <= c[0]:
                count += 1
                Parr_i = c[3]
                if timesValues[Parr_i] > c[1]:
                    timesValues[Parr_i] = c[1]
                    for neigh_i in range(len(S2SPos[Parr_i])):
                        if S2SPos[Parr_i][neigh_i] != -2:
                            neigh = S2SPos[Parr_i][neigh_i]
                            neighTime = timesValues[neigh]
                            if neighTime > c[1] + S2STime[Parr_i][neigh_i]:
                                timesValues[neigh] = c[1] + S2STime[Parr_i][neigh_i]
                        else:
                            break
                        
    timeSres = timesValues
    return timeSres
    print ('value changed {0}'.format(count))

@jit(int32[:](int32[:],int32[:],int32[:,:],int32[:,:]), nopython = True)
def computePointTime(timePP, timeSS, P2SPos, P2STime ):
    #global P2SPos
    #global P2STime
    maxRow = len(P2SPos[0])
    for p_i in range(len(timePP)):
        ListNeighP_i = P2SPos[p_i]
        for stop_i in range(maxRow):
            stop = int(ListNeighP_i[stop_i])
            if stop == -2:
                break
            else:
                timePP[p_i] = min(timePP[p_i], timeSS[stop] + P2STime[p_i][stop_i])
    return timePP

@jit(int32[:](int32[:],int32,int64[:,:],int32[:,:],int32[:,:]), nopython = True)
def treeNew(timesValues, timeStart, arrayCC, S2SPos, S2STime):
    #print 'inter'
    #global arrayCC
    #arrayCC = CC
    #global S2SPos
    #global S2STime
    count = 0
    timesValuesN = numpy.copy(timesValues)
    for c_i in range(len(arrayCC)):
        c = arrayCC[c_i]
        Pstart_i = c[2]
        if timesValues[Pstart_i] <= c[0] or timesValuesN[Pstart_i] <= c[0]:
            count += 1
            Parr_i = c[3]
            if timesValues[Parr_i] > c[1]:
                timesValues[Parr_i] = c[1]
                for neigh_i in range(len(S2SPos[Parr_i])):
                    if S2SPos[Parr_i][neigh_i] != -2:
                        neigh = S2SPos[Parr_i][neigh_i]
                        neighTime = timesValuesN[neigh]
                        if neighTime > c[1] + S2STime[Parr_i][neigh_i]:
                            timesValuesN[neigh] = c[1] + S2STime[Parr_i][neigh_i]
                    else:
                         break
                      
    for i,t in enumerate(timesValues):
        if t > timesValuesN[i]:
            timesValues[i] = timesValuesN[i]
            #print('less!!')
    return timesValues

