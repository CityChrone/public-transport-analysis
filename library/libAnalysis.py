import numpy as np

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

def expon(xx, a, b):
    return a * np.exp(-b*xx)

def gauss(xx, a, b):
    return a * np.exp(-b*xx**2)

def giveVarExpon(maxValue):
    def varExpon(xx, a, b):
        return maxValue * np.exp(-b*xx**a)
    return varExpon


def fitIt(x,y, funct, p0, nameFunc = "exponential"):
    from scipy.optimize import curve_fit
    import numpy as np

    xx=np.array(x)
    yy=np.array(y)
    
    popt, pcov = curve_fit(funct, xx, yy, p0 = p0)
    yAvg = np.array(sum(yy)/len(yy))
    SStot = sum((yy-yAvg)**2)
    SSreg = sum((yy-funct(xx, *popt))**2)
    R2 = 1 - (SSreg/SStot)
    stringtoPrint = "r2 = {0}".format(R2)
    stringtoPrint += "\na = {0:.2f}".format(popt[0])
    stringtoPrint +="\nb = {0:.2f}".format(popt[1])
    #print(stringtoPrint)
    return (popt, R2)

def fitAndPlot(quantity, timeDist, gtfsDB, city, funct, p0 = [1,1], nameFunc = "exponential"):
    import matplotlib.pyplot as plt
    import matplotlib
    import sys
    import seaborn as sns
    import math
    import numpy as np
    from libAnalysis import fitIt
    sns.set_style("ticks")
    sns.set_context("paper", font_scale=2)
    fig = plt.figure(figsize=(17, 9))


    x = []
    y = []
    for p in gtfsDB['points'].find({'city':city},{quantity:1,timeDist:1}).sort([('pos',1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])
    x=np.array(x)
    y=np.array(y)
    xfine = np.linspace(0., 15000., 15000) 
    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)

    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])

    plt.subplot(3,2,1)
    plt.plot(x, y, '.')
    (popt, R2) = fitIt(x,y,funct, p0)
    stringtoPrint = "exponential"
    stringtoPrint += "r2 = {0:.4f}".format(R2)
    stringtoPrint += "\na = {0:.2E}".format(popt[0])
    stringtoPrint +="\nb = {0:.2E}".format(popt[1])
    fitLine = plt.plot(xfine, funct(xfine, *popt), '-', linewidth=3, label=stringtoPrint)
    plt.legend()

    plt.subplot(3,2,2)
    (popt_hist, R2_hist) = fitIt(fitHistX,fitHistY, funct, p0)
    stringtoPrint = "r2 = {0:.4f}".format(R2_hist)
    stringtoPrint += "\na = {0:.2E}".format(popt_hist[0])
    stringtoPrint +="\nb = {0:.2E}".format(popt_hist[1])
    plt.plot(xfine, funct(xfine, *popt_hist), '-', linewidth=3, label=stringtoPrint)
    plt.plot(fitHistX, fitHistY, 'g-', label="histogram")
    plt.legend()

    plt.show()
    return {'hist':{'R2':R2_hist, 'popt': popt_hist}, 'points':{'R2':R2, 'popt': popt}}


def allTimeDist(quantity,timeDist, gtfsDB, city):
    import matplotlib.pyplot as plt
    import matplotlib
    import sys
    import seaborn as sns
    import math
    import numpy as np
    sns.set_style("ticks")
    sns.set_context("paper", font_scale=2)
    
    fig,ax = plt.subplots(ncols=3, nrows=3, figsize=(15,20))

    
    x = []
    y = []
    for p in gtfsDB['points'].find({'city':city},{quantity:1,timeDist:1}).sort([('pos',1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])
    
    ax = fig.add_subplot()
    ax.plot(x, y, '.')
    sns.jointplot(x=np.array(x), y=np.array(y), kind="hex");
    
    x=np.array(x)
    y=np.array(y)

    def expon(xx, a, b):
        return a * np.exp(-b*xx)
    
    popt, R2 = fitIt(x,y,expon, [1,0.001])
    
    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)
        
    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])
        
    fitIt(fitHistX,fitHistY, expon, [1,0.001])
    
    xfine = np.linspace(0., 15000., 15000) 
    ax.plot(x, y,'.', markersize=4)
    ax.plot(xfine, expon(xfine, *popt), '-', linewidth=3)
    ax.plot(fitHistX, fitHistY, 'g-')
    
    return {'plt':plt};


def expDecayTimeDist(quantity,timeDist, gtfsDB, city):
    import matplotlib.pyplot as plt
    import matplotlib
    import sys
    import seaborn as sns
    import math
    import numpy as np

    sns.set_style("ticks")
    sns.set_context("paper", font_scale=2)

    x = []
    y = []
    for p in gtfsDB['points'].find({'city':city},{quantity:1,timeDist:1}).sort([('pos',1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])
    fig = plt.figure()
    #matplotlib.rcParams['figure.figsize'] = (20, 14)
    ax = fig.add_subplot(111)
    ax.plot(x, y,  'bo')
    sns.jointplot(x=np.array(x), y=np.array(y), kind="hex");


    sns.set_style("ticks")
    sns.set_context("paper", font_scale=3)
    #sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

    #plt.rc('text', usetex=True)
    fig,ax=plt.subplots(ncols=1, nrows=1, figsize=(10,7))


    x=np.array(x)
    y=np.array(y)

    #def expon(xx, a, b,c):
    #    return a * np.exp(-b*xx)+c

    def expon(xx, a, b):
        return a * np.exp(-b*xx)
    
    (popt, R2) = fitIt(x,y,expon, [1,0.001])
    
    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)
        
    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])
        
    fitIt(fitHistX,fitHistY, expon, [1,0.001])
    
    xfine = np.linspace(0., 15000., 15000) 
    ax.plot(x, y,'.', markersize=4)
    ax.plot(xfine, expon(xfine, *popt), '-', linewidth=3)
    ax.plot(fitHistX, fitHistY, 'g-')
    
    return {'plt':plt};

def gaussDecayTimeDist(quantity,timeDist, gtfsDB, city):
    import matplotlib.pyplot as plt
    import matplotlib
    import sys
    import seaborn as sns
    import math
    import numpy as np

    sns.set_style("ticks")
    sns.set_context("paper", font_scale=2)

    x = []
    y = []
    for p in gtfsDB['points'].find({'city':city},{quantity:1,timeDist:1}).sort([('pos',1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])
    fig = plt.figure()
    #matplotlib.rcParams['figure.figsize'] = (20, 14)
    ax = fig.add_subplot(111)
    ax.plot(x, y,  'bo')
    sns.jointplot(x=np.array(x), y=np.array(y), kind="hex");


    sns.set_style("ticks")
    sns.set_context("paper", font_scale=3)
    #sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

    #plt.rc('text', usetex=True)
    fig,ax=plt.subplots(ncols=1, nrows=1, figsize=(10,7))


    x=np.array(x)
    y=np.array(y)

    #def expon(xx, a, b,c):
    #    return a * np.exp(-b*xx)+c

    def expon(xx, a, b):
        return a * np.exp(-b*xx**1.5)
    p0 = [100000,0.000001]
    (popt, R2) = fitIt(x,y,expon, p0)
    
    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)
        
    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])
        
    fitIt(fitHistX,fitHistY, expon, p0)
    
    xfine = np.linspace(0., 15000., 15000) 
    ax.plot(x, y,'.', markersize=4)
    ax.plot(xfine, expon(xfine, *popt), '-', linewidth=3)
    ax.plot(fitHistX, fitHistY, 'g-')
    
    return {'plt':plt};

def expVarDecayTimeDist(quantity,timeDist, gtfsDB, city):
    import matplotlib.pyplot as plt
    import matplotlib
    import sys
    import seaborn as sns
    import math
    import numpy as np

    sns.set_style("ticks")
    sns.set_context("paper", font_scale=2)

    x = []
    y = []
    for p in gtfsDB['points'].find({'city':city},{quantity:1,timeDist:1}).sort([('pos',1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])
    fig = plt.figure()
    #matplotlib.rcParams['figure.figsize'] = (20, 14)
    ax = fig.add_subplot(111)
    ax.plot(x, y,  'bo')
    sns.jointplot(x=np.array(x), y=np.array(y), kind="hex");


    sns.set_style("ticks")
    sns.set_context("paper", font_scale=3)
    #sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

    #plt.rc('text', usetex=True)
    fig,ax=plt.subplots(ncols=1, nrows=1, figsize=(10,7))


    x=np.array(x)
    y=np.array(y)

    #def expon(xx, a, b,c):
    #    return a * np.exp(-b*xx)+c
    
    maxValue = y.max()
    
    def expon(xx, a, b):
        return maxValue * np.exp(-b*xx**a)
    
    p0 = [1,0.0001]
    popt = fitIt(x,y,expon, p0)
    
    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)
        
    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])
        
    fitIt(fitHistX,fitHistY, expon, p0)
    
    xfine = np.linspace(0., 15000., 15000) 
    ax.plot(x, y,'.', markersize=4)
    ax.plot(xfine, expon(xfine, *popt), '-', linewidth=3)
    ax.plot(fitHistX, fitHistY, 'g-')
    
    return {'plt':plt};