import math
from geopy.distance import geodesic
from shapely.geometry import Polygon, MultiPolygon, Point, mapping
import pymongo as pym
import requests

# utility function for making hexGrid

import pyproj
from shapely.ops import transform

from shapely.geometry.polygon import Polygon
from functools import partial


def area_geojson(geoJ):
    geom = Polygon(geoJ['coordinates'][0])
    geom_area = transform(
        partial(
            pyproj.transform,
            pyproj.Proj('EPSG:4326'),  # source coordinate system
            pyproj.Proj(proj='aea', lat_1=geom.bounds[1], lat_2=geom.bounds[3],
                        lat_0=geom.centroid.y, lon_0=geom.centroid.x)  # destination
        ),
        geom)

    return geom_area.area / 1.e6  # area in square kilometers


# Center should be [x, y]
cosines = []
sines = []
for i in range(0, 6):
    angle = 2. * math.pi/6. * i
    cosines.append(math.cos(angle))
    sines.append(math.sin(angle))


def myhexagon(center, rx, ry):
    vertices = []
    for i in range(0, 6):
        x = center[0] + rx * cosines[i]
        y = center[1] + ry * sines[i]
        vertices.append([x, y])

    # first and last vertex must be the same
    vertices.append(vertices[0])
    return Polygon(vertices)


def dist2Point(one, two):  # one=(lat,lon)
    # dist in meter
    return geodesic((one[1], one[0]), (two[1], two[0])).kilometers
    # return  great_circle(one, two).angle


def dist4PointType(one, two):  # one=(point,point)
    one = one['coordinates']
    two = two['coordinates']
    # dist in meter
    return geodesic((one[1], one[0]), (two[1], two[0])).kilometers


def hexagonal_grid_border(shapely_border, cell, city):
    bbox = shapely_border.bounds
    xFraction = cell / (dist2Point((bbox[0], bbox[1]), (bbox[2], bbox[1])))
    cellWidth = xFraction * (bbox[2] - bbox[0])
    yFraction = cell / (dist2Point((bbox[0], bbox[1]), (bbox[0], bbox[3])))
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
    if hasOffsetY:
        y_adjust -= hex_height/4.

    fc = []
    listPoint = []
    count_ins = 0
    for x in range(0, x_count):
        for y in range(0, y_count+1):
            isOdd = x % 2 == 1
            # print isOdd
            if y == 0 and isOdd:
                continue
            if y == 0 and hasOffsetY:
                continue

            center_x = x * x_interval + bbox[0] - x_adjust
            center_y = y * y_interval + bbox[1] + y_adjust

            if isOdd:
                center_y -= hex_height/2

            lonLatStart = [center_x, center_y]

            myhex = myhexagon([center_x, center_y],
                              cellWidth / 2., cellHeight / 2.)

            ccc = shapely_border.contains(Point(center_x, center_y))
            if ccc:
                listPoint.append({"point": {"type": "Point", "coordinates": [center_x, center_y]},
                                  'hex': mapping(myhex),
                                  'city': city,
                                  'pos': count_ins,
                                  })
                fc.append(myhex)
                count_ins += 1
            if count_ins % 10 == 0:
                print('\r {0:.1f}%, tot = {1}, inserted = {2}'.format(
                    100.*(float(x*y_count)+float(y))/(x_count*y_count), (float(x*y_count)+float(y)), count_ins), end="")

    return MultiPolygon(fc), listPoint


def hexagonal_grid(bbox, cell, city):

    xFraction = cell / (dist2Point((bbox[0], bbox[1]), (bbox[2], bbox[1])))
    cellWidth = xFraction * (bbox[2] - bbox[0])
    yFraction = cell / (dist2Point((bbox[0], bbox[1]), (bbox[0], bbox[3])))
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
    if hasOffsetY:
        y_adjust -= hex_height/4.

    fc = []
    listPoint = []
    count_ins = 0
    for x in range(0, x_count):
        for y in range(0, y_count+1):
            isOdd = x % 2 == 1
            # print isOdd
            if y == 0 and isOdd:
                continue
            if y == 0 and hasOffsetY:
                continue

            center_x = x * x_interval + bbox[0] - x_adjust
            center_y = y * y_interval + bbox[1] + y_adjust

            if isOdd:
                center_y -= hex_height/2

            lonLatStart = [center_x, center_y]

            myhex = myhexagon([center_x, center_y],
                              cellWidth / 2., cellHeight / 2.)
            listPoint.append({"point": {"type": "Point", "coordinates": [center_x, center_y]},
                              'hex': mapping(myhex),
                              'city': city,
                              'pos': count_ins,
                              })
            fc.append(myhex)
            count_ins += 1
            if count_ins % 10 == 0:
                print('\r {0:.1f}%, tot = {1}, inserted = {2}'.format(
                    100.*(float(x*y_count)+float(y))/(x_count*y_count), (float(x*y_count)+float(y)), count_ins), end="")

    return MultiPolygon(fc), listPoint


def hexagonal_grid_stops_filter(bbox, cell, gtfsDBStops, distanceS, city):

    cosines = []
    sines = []
    for i in range(0, 6):
        angle = 2. * math.pi/6. * i
        cosines.append(math.cos(angle))
        sines.append(math.sin(angle))

    xFraction = cell / (dist2Point((bbox[0], bbox[1]), (bbox[2], bbox[1])))
    cellWidth = xFraction * (bbox[2] - bbox[0])
    yFraction = cell / (dist2Point((bbox[0], bbox[1]), (bbox[0], bbox[3])))
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
    if hasOffsetY:
        y_adjust -= hex_height/4.

    fc = []
    listPoint = []
    count_ins = 0
    for x in range(0, x_count):
        for y in range(0, y_count+1):
            isOdd = x % 2 == 1
            # print isOdd
            if y == 0 and isOdd:
                continue
            if y == 0 and hasOffsetY:
                continue

            center_x = x * x_interval + bbox[0] - x_adjust
            center_y = y * y_interval + bbox[1] + y_adjust

            if isOdd:
                center_y -= hex_height/2

            lonLatStart = [center_x, center_y]

            searchNear = {
                'city': city,
                'point': {'$near': {
                    '$geometry': {
                        'type': "Point",
                        'coordinates': lonLatStart
                    },
                    '$maxDistance': distanceS,
                    '$minDistance': 0
                }},
            }
            StopsCount = gtfsDBStops.find(searchNear).count()

            # print tempUrl[:-1] + '?sources=0'
            if (StopsCount > 0):
                myhex = myhexagon([center_x, center_y],
                                  cellWidth / 2., cellHeight / 2.)
                listPoint.append({"point": {"type": "Point", "coordinates": [center_x, center_y]},
                                  'hex': mapping(myhex),
                                  'city': city,
                                  'served': True,
                                  'pos': count_ins,
                                  })
                fc.append(myhex)
                count_ins += 1
            if count_ins % 10 == 0:
                print('{0:.1f}%, tot = {1}, inserted = {2}'.format(100.*(float(x*y_count) +
                      float(y))/(x_count*y_count), (float(x*y_count)+float(y)), count_ins), end="\r")

    return MultiPolygon(fc), listPoint


def insertPoints(pointBin, city, gtfsDB):
    gtfsDB['points'].delete_many({'city': city})
    gtfsDB['points'].insert_many(pointBin)
    gtfsDB['points'].create_index([("point", pym.GEOSPHERE)])
    gtfsDB['points'].create_index([("served", pym.ASCENDING)])
    gtfsDB['points'].create_index([("city", pym.ASCENDING)])


def pointsServed(gtfsDB, stopsList, urlServerOsrm, distanceS, tS, city):
    hexTemp = gtfsDB['points']
    tot = len(stopsList)
    count = 0
    url = urlServerOsrm + "table/v1/foot/"
    hexTemp.update_many({'city': city}, {'$set': {'served': False}})
    updatedPoints = 0
    for stop in stopsList:
        lonLatStart = [float(stop[2]), float(stop[1])]
        latLonStart = [float(stop[1]), float(stop[2])]
        tempUrl = url + str(latLonStart[1]) + ','+str(latLonStart[0]) + ';'
        searchNear = {
            'city': city,
            'served': False,
            'point': {'$near': {
                '$geometry': {
                    'type': "Point",
                    'coordinates': lonLatStart
                },
                '$maxDistance': distanceS,
                '$minDistance': 0
            }},
        }
        listPoint = []
        for point in hexTemp.find(searchNear):
            lonLatEnd = point['point']['coordinates']
            tempUrl += str(lonLatEnd[0]) + ','+str(lonLatEnd[1]) + ';'
            listPoint.append(point['_id'])
        # print tempUrl[:-1] + '?sources=0'
        if (len(listPoint) > 0):
            result = requests.get(tempUrl[:-1] + '?sources=0')
            countStopNear = 0
            # print result, tempUrl[:-1] + '?sources=0'
            if 'durations' in result.json():
                for i, t in enumerate(result.json()['durations'][0][1:]):
                    if t:
                        if t < tS:
                            hexTemp.update_one({'_id': listPoint[i]}, {
                                               '$set': {'served': True}})
                            updatedPoints += 1
        print('\r tot {0}, {1:.2f}%, updated {2}'.format(
            tot, 100.*count/tot, updatedPoints), end="\r")
        count += 1

    tot = hexTemp.find({'served': True, 'city': city}).count()
    count = 0
    coorHex = hexTemp.find_one({'city': city, 'served': True})[
        'hex']['coordinates']
    distMax = 1.1 * 1000. * dist2Point(coorHex[0][0], coorHex[0][1])
    urlBase = urlServerOsrm + 'nearest/v1/foot/'
    listServedTrue = list(hexTemp.find({'served': True, 'city': city}))
    CountOut = 0
    for hexP in hexTemp.find({'served': True, 'city': city}):
        coorP = hexP['point']['coordinates']
        url = urlBase + str(coorP[0]) + ',' + str(coorP[1])
        result = requests.get(url)
        if result.json()['waypoints'][0]['distance'] > distMax:
            # print result.json(), url
            CountOut += 1
            hexTemp.update_one({'_id': hexP['_id']}, {
                               '$set': {'served': False, 'out': True}})
        print('\r tot {1},{0:.0f}%, removed {2} '.format(
            100.*count/tot, count, CountOut), end="\r")
        count += 1
    gtfsDB['points'].delete_many({'served': False, 'city': city})


def settingHexsPos(gtfsDB, city):
    pos = 0
    for point in gtfsDB['points'].find({'served': True, 'city': city}).sort([('_id', pym.ASCENDING)]):
        gtfsDB['points'].update_one({'_id': point['_id']}, {
                                    '$set': {'pos': pos, 'inCityBorder': True}})
        pos += 1
        print('\r {0}'.format(pos), end="\r")
    gtfsDB['points'].create_index([("pos", pym.ASCENDING)])


def setHexsPop(gtfsDB, popCol, namePopField, city):

    tot = gtfsDB['points'].find({'city': city}).count()
    count = 0
    totPop = 0

    for hexagon in gtfsDB['points'].find({'city': city}):

        shapelyHex = Polygon(hexagon['hex']['coordinates'][0])
        hexagon['hex']['properties'] = {'pop': 0}
        findJson = {'geometry': {
            '$geoIntersects': {'$geometry': hexagon['hex']}}}
        for box in popCol.find(findJson):
            # box['geometry'] = {}
            # box['box']['properties']={'pop':box['pop2015']}
            shapelyBox = Polygon(box['geometry']['coordinates'][0])
            areaInter = shapelyBox.intersection(shapelyHex).area
            # print '\r{0}'.format(box['pop'])
            popHexBox = box['properties'][namePopField] * \
                areaInter/shapelyBox.area
            hexagon['hex']['properties']['pop'] += popHexBox
            # geoFolium = folium.GeoJson(box['box'],style_function=style,overlay=True)
            # map_stops.add_child(geoFolium)
        count += 1
        # hexFolium = folium.GeoJson( hex['hex'],style_function=style)
        # map_stops.add_child(hexFolium)
        totPop += hexagon['hex']['properties']['pop']
        gtfsDB['points'].update_one({'_id': hexagon['_id']}, {
                                    '$set': {'pop': hexagon['hex']['properties']['pop']}})
        print('{0:.1f}% , tot population: {1:.0f}, current hex: {2:.0f}'.format(
            100.*count/tot, totPop, hexagon['hex']['properties']['pop']), end="\r")
