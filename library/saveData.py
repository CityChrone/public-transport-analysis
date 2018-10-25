import json
import zipfile
from libHex import area_geojson
from libConnections import makeArrayConnections
import os

def listOfNeighbor(gtfsDB, city, limit_walking_time = 900):
    S2SPos = []
    S2STime = []
    P2PPos = []
    P2PTime = []
    P2SPos = []
    P2STime = []
    count_error = 0
    for stop in gtfsDB['stops'].find({'city':city}).sort([('pos',1)]):       
        S2SPos.append([])
        S2STime.append([])
        for i,stopN in enumerate(stop['stopN']):
            time_walk = round(stop['stopN'][i]['time'])
            if time_walk <= limit_walking_time:
                S2SPos[stop['pos']].append(stop['stopN'][i]['pos'])
                S2STime[stop['pos']].append(stop['stopN'][i]['time'])
        print ('fill stop neighbors {0}'.format(stop['pos']),end="\r")

    for point in gtfsDB['points'].find({'city':city}).sort([('pos',1)]):        
        P2SPos.append([0]*len(point['stopN']))
        P2STime.append([0]*len(point['stopN']))
        P2PPos.append([0]*len(point['pointN']))
        P2PTime.append([0]*len(point['pointN']))
        for i,stopN in enumerate(point['stopN']):
            P2SPos[point['pos']][i] = point['stopN'][i]['pos']
            P2STime[point['pos']][i] = round(point['stopN'][i]['time'])
        for i,pointN in enumerate(point['pointN']):
            P2PPos[point['pos']][i] = point['pointN'][i]['pos']
            P2PTime[point['pos']][i] = round(point['pointN'][i]['time'])
        print ('fill point neighbors {0}'.format(point['pos']),end="\r")
        
    return {
        'S2SPos' : S2SPos, 
        'S2STime' : S2STime , 
        'P2PPos': P2PPos,
        'P2PTime' : P2PTime,
        'P2SPos' : P2SPos, 
        'P2STime' : P2STime}


def makeZipCitychrone(city, gtfsDB, arrayCC = [], path_main = './saved/', newScenario = False, budget = 5000, costTubeKm = 30, costMetroStop=100, metroLines = [], urlServerOsrm = 'localhost:5000', limit_walking_time = 900):
    path = path_main + city + "/"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    a  = zipfile.ZipFile(path_main+city+'_citychrone.zip',  mode = 'w', compression=zipfile.ZIP_DEFLATED)

    if len(arrayCC) == 0:
        arrayCC = makeArrayConnections(gtfsDB, 7*3600, city)
    
    arrayCCList = []
    for c in arrayCC.tolist():
        arrayCCList.extend((c[2],c[3],c[0],c[1]))

    with open(path + 'connections.txt', 'w') as conFile:
        jsonStr = json.dumps(arrayCCList)
        conFile.write(jsonStr)
        conFile.close()
        a.write(path+'connections.txt', 'connections.txt')
    os.remove(path+'connections.txt')

    listN = listOfNeighbor(gtfsDB, city, limit_walking_time)
    for name in listN:
        with open(path + name + '.txt', 'w') as nFile:
            jsonStr = json.dumps(listN[name])
            nFile.write(jsonStr)
            nFile.close()
            a.write(path + name + '.txt', name + '.txt')
        os.remove(path + name + '.txt')

    points = []
    for p in gtfsDB['points'].find({'city':city}, sort = [('pos',1)]):
        coor = p['point']['coordinates']
        pos = p['pos']
        pop = p['pop']
        city = p['city']
        points.append({'coor':coor, 'pos':pos, 'pop':pop, 'city':city})

    with open(path + 'listPoints.txt', 'w') as pointFile:
        jsonStr = json.dumps(points)
        pointFile.write(jsonStr)
        pointFile.close()
        a.write(path + 'listPoints.txt', 'listPoints.txt')
    os.remove(path + 'listPoints.txt')
    
    stops = []
    for s in gtfsDB['stops'].find({'city':city}, sort = [('pos',1)]):
        pos = s['pos']
        point = s['point']
        city = s['city']
        stops.append({'pos':pos, 'point':point, 'city':city})

    with open(path + 'listStops.txt', 'w') as stopsFile:
        jsonStr = json.dumps(stops)
        stopsFile.write(jsonStr)
        stopsFile.close()
        a.write(path + 'listStops.txt', 'listStops.txt')
    os.remove(path + 'listStops.txt')

    dataCity = {}
    centerCityPoint = gtfsDB['points'].find_one({'city':city}, sort=[('socialityScore.avg',-1)])
    dataCity['centerCity'] = centerCityPoint['point']['coordinates']
    dataCity['areaHex'] =  area_geojson(centerCityPoint['hex'])
    dataCity['hex'] = centerCityPoint['hex']
    dataCity['newScenario'] = newScenario
    dataCity['city'] = centerCityPoint['city']
    dataCity['budget'] = {
        'budget':budget,
        'costTubeKm':costTubeKm,
        'costMetroStop':costMetroStop
    }
    dataCity['metroLines'] = metroLines
    dataCity['serverOSRM'] = urlServerOsrm
    with open(path + 'cityData.txt', 'w') as dataCityFile:
        jsonStr = json.dumps(dataCity)
        dataCityFile.write(jsonStr)
        dataCityFile.close()
        a.write(path + 'cityData.txt', 'cityData.txt')
    os.remove(path + 'cityData.txt')
    a.close()
    os.rmdir(os.path.dirname(path))