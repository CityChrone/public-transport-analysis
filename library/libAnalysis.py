def distBin(Col, match, field, binStep):
    result = Col.aggregate([{
        '$match':match
        },
        {'$project':{field:{'$divide': ['$'+field,binStep]}}},
        {'$project':{field:{'$floor':'$'+field}}},
        {'$project':{field:{'$multiply': ['$'+field,binStep]}}},
        {'$group':{
            '_id':'$'+field,
            'res' : {'$sum' :1},
        }}])
    valList = {}
    for p in result:
        valList[p['_id']] = {field : p['res']}
    x = []
    y = []
    std_y = []
    for p in sorted(valList.keys()):
        x.append(p)
        y.append(valList[p][field])
    return (x,y)
