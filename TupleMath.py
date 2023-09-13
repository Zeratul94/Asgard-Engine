# Copyright © Gedalya Gordon 2023, all rights reserved. #

import math

def addTuple(t1, t2):
    ans = []
    for i in range(len(t1)):
        ans.append(t1[i] + t2[i])
    return tuple(ans)
def subtractTuple(t1, t2):
    ans = []
    for i in range(len(t1)):
        ans.append(t1[i] - t2[i])
    return tuple(ans)

def scale(t, s):
    ans = []
    for i in range(len(t)):
        ans.append(t[i] * s)
    return tuple(ans)

def clampTuple(t, clamps = ((-math.inf, math.inf), (-math.inf, math.inf), (-math.inf, math.inf))):
    ans = []
    for i in range(len(t)):
        ans.append(min(max(clamps[i][0], t[i]), clamps[i][1]))
    return tuple(ans)

def length(t):
    sqsum = 0
    for element in t:
        sqsum += element**2
    return math.sqrt(sqsum)

def normalize(t):
    sqsum = 0
    absedT = []
    for element in t:
        sqsum += element**2
        absedT.append(abs(element))
    length = math.sqrt(sqsum)
    if length == 0: return t
    return scale(t, 1/length)

def roundToward(t, target=0, tolerance=0.1):
    ans = []
    for element in t:
        if abs(float(element) - target) <= tolerance:
            element = target
        ans.append(element)
    return tuple(ans)

def distance(t1, t2):
    sqsum = 0
    for i in range(len(t1)):
        sqsum += (t2[i] - t1[i])**2
    return math.sqrt(sqsum)

def extend(t, dir, dist = 1):
    ans = []
    for i in range(len(t)):
        ans.append(t[i] + (dist*dir[i]))
    return tuple(ans)