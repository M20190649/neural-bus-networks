#!/usr/bin/env python
import datetime
from time import time
import numpy
import tables





#####################
import signal

class TimeoutException(Exception):   # Custom exception class
    pass

def timeout_handler(signum, frame):   # Custom signal handler
    raise TimeoutException

# Change the behavior of SIGALRM
signal.signal(signal.SIGALRM, timeout_handler)


#######################

def dist(origin, destination, radius = 6371.392896):
    # Haversine formula - takes spherical latitude and longitude in degrees and returns distance between the points
    # The default unit returned is in kilometers assuming the sphere has the radius of the earth
    lat1, lon1 = origin
    lat2, lon2 = destination

    dlat = numpy.radians(lat2-lat1)
    dlon = numpy.radians(lon2-lon1)
    a = numpy.sin(dlat/2) * numpy.sin(dlat/2) + numpy.cos(numpy.radians(lat1)) \
            * numpy.cos(numpy.radians(lat2)) * numpy.sin(dlon/2) * numpy.sin(dlon/2)
    c = 2 * numpy.arctan2(numpy.sqrt(a), numpy.sqrt(1-a))
    d = radius * c
    return d


def GetAllIntervalData(VehicleLocations, route=1, direction='1_1_var0', position=(42.3589399, -71.09363)):
    """
    Input the vehiclelocations, the route and direction (inbound/outbound), and the postition, the lat and lon for a stop

    Returns spacings, times, where spacings is the intervals between arrivals at that stop, and times is
    the actual arrival times at that stop.
    """
    #Defaults
    #Get data from
    #   http://webservices.nextbus.com/service/publicXMLFeed?command=routeConfig&a=mbta&r=64
    # 1 bus, inbound, at 84 Mass Ave

    # 1 bus, outbound, at 84 Mass Ave
    # direction='1_0_var0'

    # CT1 bus, outbound, at 84 Mass Ave
    # route=701
    # direction='701_0_var0'

    # CT1 bus, inbound, at 84 Mass Ave
    # route=701
    # direction='701_1_var0'

    # 64
    #route=64
    #direction='64_0_var0'
    #position=(42.3539299, -71.13637)

    # 57 bus inbound at Comm Ave @ Hinsdale
    #route=57
    #direction='57_1_var1'
    #direction='57_1_var1'
    #position=(42.3494, -71.1030599)

    queryString = "((route == '%s') & (direction == '%s'))" % (route, direction)

    #queryString = "((route == '57') & ((direction == '57_1_var1') | (direction == '57_1_var0')))" #Outbound 57 has two variants

    trajectories = VehicleLocations.where(queryString)
    return ExtractArrivalIntervals(trajectories, position)

def getResult(fromList,toList):
    # signal.alarm(1)
    try:
        x=0
        while x<5000:
            a = fromList.next()
            toList.append(a) # Whatever your function that might hang
            x+=1
    except TimeoutException:
        print("timeout")
    except StopIteration:
        print("stopped")
    else:
        print("else")
        # signal.alarm(0)
        return


def ExtractArrivalIntervals(trajectories, position, doWrite = True):
    """
    Takes in trajectories, which are lists of (time, vehicleId, latitude, longitude)

    Returns arrival intervals and times to hit each stop
    """

    # Tweak this parameter to find ideal
    arrivalDistanceThreshold = 0.25 #km
    arrivalTimeThreshold = 300     #seconds
    maxIntervalThreshold = 2*60*60 #seconds

    queryResults = [(timePoint['time'], timePoint['vehicleID'], timePoint['latitude'], timePoint['longitude']) for timePoint in trajectories]
    queryResults = sorted(queryResults) #Sort in time

    # Try to determine when each bus arrived at the bus stop
    # TODO this is very primitive, should replace it with some kind of interpolation and least-squares approach
    data = {}
    for timePoint in queryResults:
        theDistance = dist((timePoint[2], timePoint[3]), position)
        if theDistance > arrivalDistanceThreshold:
            #Vehicle too far away, skip
            continue

        theVehicle, theTime = timePoint[1], timePoint[0]
        if theVehicle in data: #If same vehicle...
            lastTime, lastDistance = data[theVehicle][-1]
            if abs(lastTime - theTime) < arrivalTimeThreshold: #and data is recent in time
                if theDistance < lastDistance:
                    #Update - bus moved closer
                    data[theVehicle].pop()
                    data[theVehicle].append((theTime, theDistance))
                else: # The bus has passed the stop
        else:
            data[theVehicle] = [(theTime, theDistance)]

    #Extract arrival times
    arrivalTimesWithVehicleIdUnsorted = []
    for vehicleId in data:
        vehicleData= data[vehicleId]
        for times, _ in vehicleData:
            arrivalTimesWithVehicleIdUnsorted.append([vehicleId,times])

    arrivalTimesWithVehicleId = sorted(arrivalTimesWithVehicleIdUnsorted, key=lambda x:x[1])
    arrivalTimes = [x[1] for x in arrivalTimesWithVehicleId]
    busIds = [x[0] for x in arrivalTimesWithVehicleId]

    # There is no interval for the first bus
    arrivalIntervals = [numpy.NaN]
    arrivalIntervals.extend(numpy.diff(arrivalTimes))
    for i in range(len(arrivalTimesWithVehicleId)):
        arrivalTimesWithVehicleId[i].append(arrivalIntervals[i])

    busIds = [x[0] for x in arrivalTimesWithVehicleId]
    times = [x[1] for x in arrivalTimesWithVehicleId]
    intervals = [x[2] for x in arrivalTimesWithVehicleId]
    arrivalTimesWithVehicleId = filter(lambda x:x[2]<maxIntervalThreshold, arrivalTimesWithVehicleId)

    return intervals, times,busIds

def ExtractArrivalTimes(trajectories, position, doWrite = True):
    """
    Get the arrival times for a given stop.
    """
    return ExtractArrivalIntervals(trajectories, position, doWrite = True)[1]

if __name__ == '__main__':
    from glob import glob
    all_spacings = []
    all_times = []
    for filename in sorted(glob('*.h5')):
        h5file = tables.open_file(filename)
        print 'Reading data from', filename
        print("file",filename)
        spacings, times = GetAllIntervalData(h5file.root.VehicleLocations)
        h5file.close()
        all_spacings += list(spacings)
        all_times += list(times)
    if True:#doWrite:
        import scipy.io
        data_dict = {'gaps': all_spacings, 'timestamps': all_times}
        scipy.io.savemat('data.mat', data_dict, oned_as = 'row')
    h5file.close()
