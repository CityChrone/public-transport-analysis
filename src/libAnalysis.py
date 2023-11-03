import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import sys
import seaborn as sns
import math
import numpy as np
from scipy.optimize import curve_fit
import numpy as np


def distBin(Col, match, field, binStep):
    result = Col.aggregate([{
        '$match': match
    },
        {'$project': {field: {'$divide': ['$'+field, binStep]}}},
        {'$project': {field: {'$floor': '$'+field}}},
        {'$project': {field: {'$multiply': ['$'+field, binStep]}}},
        {'$group': {
            '_id': '$'+field,
            'res': {'$sum': 1},
        }}])
    valList = {}
    for p in result:
        valList[p['_id']] = {field: p['res']}
    x = []
    y = []
    std_y = []
    for p in sorted(valList.keys()):
        x.append(p)
        y.append(valList[p][field])
    return (x, y)


def expon(xx, tau):
    return np.exp(-xx/tau)


def expon_two_params(xx, tau, y0):
    return y0*np.exp(-xx/tau)


def gauss(xx, a, b):
    return a * np.exp(-b*xx**2)


def giveVarExpon(maxValue):
    def varExpon(xx, a, b):
        return maxValue * np.exp(-b*xx**a)
    return varExpon


def giveVarExponOneVar(maxValue, sigma):
    def varExpon(xx, a):
        return maxValue * np.exp(-sigma*xx**a)
    return varExpon


def giveVarExponShift(maxValue, sigma):
    def varExpon(xx, a, b):
        return maxValue * np.exp(-sigma*(xx)**a) + b
    return varExpon


def giveVarExponShift3(maxValue):
    def varExpon(xx, a, b, sigma):
        return maxValue * np.exp(-sigma*(xx)**a) + b
    return varExpon


def stretExp(xx, beta, tau):
    return np.exp(-(xx / tau)**beta)


def expon3Var(xx, a, b, c):
    return c * np.exp(-b*(xx)**a)


def powLaw(xx, a, c):
    return c * (xx + 0.1) ** a


def powLaw3param(xx, a, b, c):
    return c * (xx + 0.1 + b) ** a


def linear_func(xx, alpha, beta):
    return beta*xx + alpha


def linear(xx, beta, alpha):
    return beta*xx + alpha


def linear_func_one_param(xx, beta):
    return beta*xx


def fitIt(x, y, funct, p0, nameFunc="exponential", bounds=False):

    xx = np.array(x)
    yy = np.array(y)
    if not bounds:
        popt, pcov = curve_fit(funct, xx, yy, p0=p0, maxfev=100000)
    else:
        popt, pcov = curve_fit(funct, xx, yy, p0=p0,
                               maxfev=100000, bounds=bounds)
    yAvg = np.array(np.mean(yy))
    SStot = np.sum((yy-yAvg)**2)
    SSreg = np.sum((yy-funct(xx, *popt))**2)
    square_dist = np.sum(np.abs(yy-funct(xx, *popt)))/len(yy)
    R2 = 1 - (SSreg/SStot)
    stringtoPrint = "r2 = {0}".format(R2)
    for i, val in enumerate(popt):
        stringtoPrint += "\nParam_" + str(i)+" = {0:.2f}".format(val)
    # print(stringtoPrint)
    return popt, R2, square_dist


def fitAndPlot(quantity, timeDist, gtfsDB, city, funct, p0=[1, 1], nameFunc="exponential", bounds=False):
    sns.set_style("ticks")
    sns.set_context("paper", font_scale=2)
    fig = plt.figure(figsize=(17, 9))

    x = []
    y = []
    time_limit_new = 3600*2
    for p in gtfsDB['points'].find({'city': city}, {quantity: 1, timeDist: 1}).sort([('pos', 1)]):
        if p[timeDist] < time_limit_new:
            x.append(p[timeDist] / 3600)
            if isinstance(p[quantity], dict):
                y.append(p[quantity]['avg'])
            else:
                y.append(p[quantity])
    x = np.array(x)
    y = np.array(y)
    xfine = np.linspace(0., time_limit_new/3600, 10000)
    bins = 40
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)

    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])

    plt.subplot(3, 2, 1)
    plt.plot(x, y, '.')
    (popt, R2, square_dist) = fitIt(x, y, funct, p0, bounds=bounds)
    stringtoPrint = f"{nameFunc} \n"
    stringtoPrint += "r2 = {0:.4f}".format(R2)
    for i, val in enumerate(popt):
        stringtoPrint += "\nParam_" + str(i)+" = {0:.2f}".format(val)
    fitLine = plt.plot(xfine, funct(xfine, *popt), '-',
                       linewidth=3, label=stringtoPrint)
    plt.legend()

    plt.subplot(3, 2, 2)
    (popt_hist, R2_hist, square_dist) = fitIt(
        fitHistX, fitHistY, funct, p0,  bounds=bounds)
    stringtoPrint = "r2 = {0:.4f}".format(R2_hist)
    for i, val in enumerate(popt_hist):
        stringtoPrint += "\nParam_" + str(i)+" = {0:.2f}".format(val)
    plt.plot(xfine, funct(xfine, *popt_hist), '-',
             linewidth=3, label=stringtoPrint)
    plt.plot(fitHistX, fitHistY, 'g-', label="histogram")
    # plt.semilogy()
    plt.legend()

    plt.show()
    return {'hist': {'R2': R2_hist, 'popt': popt_hist}, 'points': {'R2': R2, 'popt': popt}}


def fitAndPlotLinear(x, y, bins=30, p0=[1, 0]):

    n, _ = np.histogram(x, bins=bins)
    sy, _ = np.histogram(x, bins=bins, weights=y)
    sy2, _ = np.histogram(x, bins=bins, weights=y*y)
    mean = []
    std = []

    centers_bin = []
    for i in range(len(sy)):
        if n[i] > 10:
            mean.append(sy[i] / n[i])
            ii = len(mean) - 1
            std.append(np.sqrt(sy2[i]/n[i] - mean[ii]*mean[ii] + 0.000001))
            centers_bin.append((_[i] + _[i+1])/2)
        # else:
            # mean.append(0.)
            # std.append(0.)

    std = np.array(std)
    mean = np.array(mean)
    centers_bin = np.array(centers_bin)

    funct = linear_func

    (popt, R2) = fitIt(x, y, funct, p0)
    (popt_hist, R2_hist) = fitIt(centers_bin, mean, funct, p0)

    stringtoPrint = "r2 = {0:.4f}".format(R2)
    stringtoPrint_hist = "r2 = {0:.4f}".format(R2_hist)

    stringtoPrint += "\n alpha = {0:.2f}".format(popt[0])
    stringtoPrint += "\n beta = {0:.2f}".format(popt[1])
    stringtoPrint_hist += "\n alpha = {0:.2f}".format(popt_hist[0])
    stringtoPrint_hist += "\n beta = {0:.2f}".format(popt_hist[1])

    xfine = np.linspace(centers_bin[0], max(x), 1000)
    (fig, axs) = plt.subplots(1, 2, figsize=(10, 4))
    axs[0].plot(x, y, '.')
    axs[0].plot(xfine, funct(xfine, *popt), '-',
                linewidth=3, label=stringtoPrint)
    axs[1].plot(centers_bin, mean, marker="o", ls="none", label="histogram", )
    axs[1].plot(xfine, funct(xfine, *popt_hist), '-',
                linewidth=3, label=stringtoPrint_hist)
    axs[0].legend()
    axs[1].legend()

    plt.show()
    return {"fit": (popt.tolist(), R2), "fit_hist": (popt_hist.tolist(), R2_hist)}


def allTimeDist(quantity, timeDist, gtfsDB, city):
    import matplotlib.pyplot as plt
    import matplotlib
    import sys
    import seaborn as sns
    import math
    import numpy as np
    sns.set_style("ticks")
    sns.set_context("paper", font_scale=2)

    fig, ax = plt.subplots(ncols=3, nrows=3, figsize=(15, 20))

    x = []
    y = []
    for p in gtfsDB['points'].find({'city': city}, {quantity: 1, timeDist: 1}).sort([('pos', 1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])

    ax = fig.add_subplot()
    ax.plot(x, y, '.')
    sns.jointplot(x=np.array(x), y=np.array(y), kind="hex")

    x = np.array(x)
    y = np.array(y)

    def expon(xx, a, b):
        return a * np.exp(-b*xx)

    popt, R2 = fitIt(x, y, expon, [1, 0.001])

    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)

    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])

    fitIt(fitHistX, fitHistY, expon, [1, 0.001])

    xfine = np.linspace(0., 15000., 15000)
    ax.plot(x, y, '.', markersize=4)
    ax.plot(xfine, expon(xfine, *popt), '-', linewidth=3)
    ax.plot(fitHistX, fitHistY, 'g-')

    return {'plt': plt}


def expDecayTimeDist(quantity, timeDist, gtfsDB, city):
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
    for p in gtfsDB['points'].find({'city': city}, {quantity: 1, timeDist: 1}).sort([('pos', 1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])
    fig = plt.figure()
    # matplotlib.rcParams['figure.figsize'] = (20, 14)
    ax = fig.add_subplot(111)
    ax.plot(x, y,  'bo')
    sns.jointplot(x=np.array(x), y=np.array(y), kind="hex")

    sns.set_style("ticks")
    sns.set_context("paper", font_scale=3)
    # sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

    # plt.rc('text', usetex=True)
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(10, 7))

    x = np.array(x)
    y = np.array(y)

    # def expon(xx, a, b,c):
    #    return a * np.exp(-b*xx)+c

    def expon(xx, a, b):
        return a * np.exp(-b*xx)

    (popt, R2) = fitIt(x, y, expon, [1, 0.001])

    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)

    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])

    fitIt(fitHistX, fitHistY, expon, [1, 0.001])

    xfine = np.linspace(0., 15000., 15000)
    ax.plot(x, y, '.', markersize=4)
    ax.plot(xfine, expon(xfine, *popt), '-', linewidth=3)
    ax.plot(fitHistX, fitHistY, 'g-')

    return {'plt': plt}


def gaussDecayTimeDist(quantity, timeDist, gtfsDB, city):
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
    for p in gtfsDB['points'].find({'city': city}, {quantity: 1, timeDist: 1}).sort([('pos', 1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])
    fig = plt.figure()
    # matplotlib.rcParams['figure.figsize'] = (20, 14)
    ax = fig.add_subplot(111)
    ax.plot(x, y,  'bo')
    sns.jointplot(x=np.array(x), y=np.array(y), kind="hex")

    sns.set_style("ticks")
    sns.set_context("paper", font_scale=3)
    # sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

    # plt.rc('text', usetex=True)
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(10, 7))

    x = np.array(x)
    y = np.array(y)

    # def expon(xx, a, b,c):
    #    return a * np.exp(-b*xx)+c

    def expon(xx, a, b):
        return a * np.exp(-b*xx**1.5)
    p0 = [100000, 0.000001]
    (popt, R2) = fitIt(x, y, expon, p0)

    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)

    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])

    fitIt(fitHistX, fitHistY, expon, p0)

    xfine = np.linspace(0., 15000., 15000)
    ax.plot(x, y, '.', markersize=4)
    ax.plot(xfine, expon(xfine, *popt), '-', linewidth=3)
    ax.plot(fitHistX, fitHistY, 'g-')

    return {'plt': plt}


def expVarDecayTimeDist(quantity, timeDist, gtfsDB, city):
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
    for p in gtfsDB['points'].find({'city': city}, {quantity: 1, timeDist: 1}).sort([('pos', 1)]):
        if p[timeDist] < 15000:
            x.append(p[timeDist])
            y.append(p[quantity]['avg'])
    fig = plt.figure()
    # matplotlib.rcParams['figure.figsize'] = (20, 14)
    ax = fig.add_subplot(111)
    ax.plot(x, y,  'bo')
    sns.jointplot(x=np.array(x), y=np.array(y), kind="hex")

    sns.set_style("ticks")
    sns.set_context("paper", font_scale=3)
    # sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

    # plt.rc('text', usetex=True)
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(10, 7))

    x = np.array(x)
    y = np.array(y)

    # def expon(xx, a, b,c):
    #    return a * np.exp(-b*xx)+c

    maxValue = y.max()

    def expon(xx, a, b):
        return maxValue * np.exp(-b*xx**a)

    p0 = [1, 0.0001]
    popt = fitIt(x, y, expon, p0)

    bins = 300
    resFrq = np.histogram(x, bins=bins)
    res = np.histogram(x, bins=bins, weights=y)

    fitHistX = []
    fitHistY = []

    for ii, xxx in enumerate(resFrq[0]):
        if xxx != 0:
            fitHistY.append(res[0][ii] / resFrq[0][ii])
            fitHistX.append(res[1][ii])

    fitIt(fitHistX, fitHistY, expon, p0)

    xfine = np.linspace(0., 15000., 15000)
    ax.plot(x, y, '.', markersize=4)
    ax.plot(xfine, expon(xfine, *popt), '-', linewidth=3)
    ax.plot(fitHistX, fitHistY, 'g-')

    return {'plt': plt}
