import math

def addTuple(t1, t2):
    ans = []
    for i in range(len(t1)):
        ans.append(t1[i] + t2[i])
    return tuple(ans)
def scaleTuple(t, s):
    ans = []
    for i in range(len(t)):
        ans.append(t[i] * s)
    return tuple(ans)
def clampTuple(t, clamps = ((-math.inf, math.inf), (-math.inf, math.inf), (-math.inf, math.inf))):
    ans = []
    for i in range(len(t)):
        ans.append(min(max(clamps[i][0], t[i]), clamps[i][1]))
    return tuple(ans)
def normalizeTuple(t):
    sumOfT = 0
    absedT = []
    for element in t:
        sumOfT += element**2
        absedT.append(abs(element))
    length = math.sqrt(sumOfT)
    if length == 0: return t
    return scaleTuple(t, max(absedT)/length)
def roundToward(t, target=0, tolerance=0.1):
    ans = []
    for element in t:
        if abs(float(element) - target) <= tolerance:
            element = target
        ans.append(element)
    return ans
