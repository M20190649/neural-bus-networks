#!/usr/bin/env python
import datetime
from glob import glob
import numpy
import tables
import time as unixtime
import scipy
import scipy.io as io
import sys

from scrapetimetable import getBusStopLocation, ChunkTimetable, ReadRouteConfig, ReadMBTATimetable, TimeToScheduleCode, getLocation
from findspacings import ExtractArrivalIntervals, ExtractArrivalTimes

def timestamp(thedatetime, thetime = None):
    #opposite of fromtimestamp
    if thetime is not None: #Assume it's a time object
        thisdatetime = datetime.datetime.combine(thedatetime, thetime)
    else:
        thisdatetime = thedatetime

    return unixtime.mktime(thisdatetime.timetuple())

def toMicroseconds(t1):
    return (t1.hour*60*60 + t1.minute*60 + t1.second)*1000 + t1.microsecond

def unixTimeSeconds(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds()

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print 'No route specified, assuming Route 1'
        theroute = 1
    else:
        theroute = int(sys.argv[1])
        print 'Route to analyze: %d' % theroute

    if len(sys.argv) <= 2:
        print 'No direction specified, assuming I (inbound)1'
        thedirection = 'I' #'O'
    else:
        thedirection = sys.argv[2]
        print 'Direction to analyze: %s' % thedirection

    if len(sys.argv) <= 3:
        print 'No input filename specified: will scan for all *.h5 files'
        h5filenames = glob('data/*.h5')
    else:
        h5filenames = [sys.argv[3]]

    if len(sys.argv) <= 4:
        print 'No output filename specified: saving to spacings.mat'
        outfilename = 'spacings'
    else:
        outfilename = sys.argv[4]

    bus_stop_data, direction_data = ReadRouteConfig(route = theroute)
    # Filter to only use the correct direction

    #TODO Handle multiple variants of inbound and outbound services
    #     Right now it just matches the first variant of each
    # Gets all of the stops for the input direction
    for direction in direction_data:
        if direction[0]['name'] == 'Inbound' and thedirection == 'I':
            direction_tag = direction[0]['tag']
            stops_tags = [d['tag'] for d in direction[1:]]
            break
        elif direction[0]['name'] == 'Outbound' and thedirection == 'O':
            direction_tag = direction[0]['tag']
            stops_tags = [d['tag'] for d in direction[1:]]
            break

    assert stops_tags is not None, 'No data found for direction'

    #Match bus stoptags to GPS coordinates
    # Gets a list of tuples with name of stop and lat/lon
    all_bus_stops = []
    for tag in stops_tags:
        match = [x for x in bus_stop_data if x['tag'] == tag][0]
        coordinates = (float(match['lat']), float(match['lon']))
        name = match['title']
        all_bus_stops.append((coordinates, name))


    all_data = []
    for h5filename in h5filenames:
        #Extract earliest and latest time stamps for the data
        #Pytables 2.4.0 does not have min() and max() query methods...
        h5file = tables.open_file(h5filename)
        timestamps = h5file.root.VehicleLocations.col('time')
        earliest_date = datetime.datetime.fromtimestamp(min(timestamps)).date()
        latest_date   = datetime.datetime.fromtimestamp(max(timestamps)).date()

        #Iterate over all timed bus stops
        for schedule_code in ['W', 'S', 'U']:
            # named_bus_stops has name and times to hit that stop
            named_bus_stops = ReadMBTATimetable(route = theroute, direction = thedirection,
                            timing = schedule_code)

            #Now iterate over ALL bus stops
            # all_bus_stops has just name and location
            for stop_idx, (this_bus_stop_location, this_bus_stop_name) in enumerate(all_bus_stops):

                #See if this is a bus stop that has a timetable on the MBTA website
                timetable = None
                timetable_chunks = None
                for named_stop in named_bus_stops:
                    named_stop_name = named_stop[0].strip()
                    named_stop_location = getLocation(named_stop_name, all_bus_stops)
                    if named_stop_location == this_bus_stop_location:
                        timetable = named_stop[1:]
                        timetable_chunks = ChunkTimetable(named_stop[1:])
                        break

                #Now iterate over all dates
                thedate = earliest_date
                while thedate <= latest_date:
                    thenextday = thedate + datetime.timedelta(days=1)

                    #If it's the wrong day of the week, skip
                    if TimeToScheduleCode(thedate) != schedule_code:
                        thedate = thenextday #Iterate
                        continue

                    #Query HDF5 data file
                    starttime = timestamp(thedate, datetime.time(3, 0))
                    endtime = timestamp(thenextday, datetime.time(3, 0))

                    queryString = "((route == '%s') & (direction == '%s') & (%f <= time) & (time < %f))" % \
                            (theroute, direction_tag, starttime, endtime)
                    trajectories = h5file.root.VehicleLocations.where(queryString)

                    #Calculate spacings
                    spacings, times, vehicle_ids = ExtractArrivalIntervals(trajectories, this_bus_stop_location,
                            doWrite = False)

                    for idx, s in enumerate(spacings):
                        thetime = datetime.datetime.fromtimestamp(times[idx]).time()
                        actual_date_time = datetime.datetime.fromtimestamp(times[idx])

                        # No expected arrival time
                        if timetable is None:
                            error = numpy.NaN
                            expected_unix_time = numpy.NaN
                        # Use closest expected arrival time
                        else:
                            # Finds the closest time.  You need to wrap around if the times span a day
                            expected_time = min(timetable, key= \
                                lambda time: min([abs(toMicroseconds(time.time())-toMicroseconds(thetime)),\
                                86400000000-abs(toMicroseconds(time.time())-toMicroseconds(thetime))])).time()
                            expected_date_time = datetime.datetime.combine(actual_date_time.date(),expected_time)
                            error = abs(expected_date_time-actual_date_time).total_seconds()
                            # More than twelve hour difference means it was closer the the previous day
                            if error>12*60*60:
                                new_expected_date_time = expected_date_time + datetime.timedelta(days=1)
                                if expected_date_time>actual_date_time:
                                    new_expected_date_time = expected_date_time - datetime.timedelta(days=1)
                                expected_date_time = new_expected_date_time
                            expected_unix_time = unixTimeSeconds(expected_date_time)
                            error = abs(expected_date_time-actual_date_time).total_seconds()
                        if timetable_chunks is None: #Not a bus stop with timetable data
                            chunk_idx = numpy.NaN
                            expected_s = numpy.NaN
                        else: #Have timetable data
                            #Determine which chunk it belongs to
                            chunktimes = numpy.array([c[0] for c in timetable_chunks])
                            chunk_idx = len(chunktimes[chunktimes < thetime]) - 1
                            if chunk_idx < 0:
                                chunk_idx += len(chunktimes)
                            expected_s = timetable_chunks[chunk_idx][1]
                        all_data.append([this_bus_stop_name, stop_idx,vehicle_ids[idx], schedule_code, chunk_idx, times[idx], expected_unix_time, error, s, expected_s])
                    thedate = thenextday #Iterate

        h5file.close()

    #Save data
    data_map = {
            'stop_name':        [x[0] for x in all_data],
            'stop_idx':         [x[1] for x in all_data],
            'vehicle_idx':      [x[2] for x in all_data],
            'schedule_code':    [x[3] for x in all_data],
            'chunk_idx':        [x[4] for x in all_data],
            'time':             [x[5] for x in all_data],
            'expected_time':    [x[6] for x in all_data],
            'error':            [x[7] for x in all_data],
            'spacing':          [x[8] for x in all_data],
            'spacing_expected': [x[9] for x in all_data],
            }

    arrival_times = {}
    for i in range(len(data_map['vehicle_idx'])):
        bus = data_map['vehicle_idx'][i]
        if bus not in arrival_times:
            arrival_times[bus] = []
        arrival_times[bus].append((data_map['stop_idx'][i],data_map['error'][i],data_map['time'][i],data_map['stop_name'][i]))



    bus_id_to_arrival_times = {}
    for data_point in all_data:
        bus_id = data_point[2]
        if bus_id not in bus_id_to_arrival_times:
            bus_id_to_arrival_times[bus_id]=[]
        bus_id_to_arrival_times[bus_id].append(data_point)

    for arrival_times_array in bus_id_to_arrival_times.values():
        arrival_times_array.sort(key=lambda x:x[5])

    def get_full_routes(all_arrivals):
        full_routes = []
        stop_idxs = [x[1] for x in all_arrivals]
        first_stop = 6
        last_stop = 28
        start_index = 0
        while first_stop in stop_idxs:
            i = stop_idxs.index(first_stop)
            if i+(last_stop-first_stop)<=len(stop_idxs) and stop_idxs[i:i+(last_stop-first_stop)] == range(first_stop,last_stop):
                full_routes.append(all_arrivals[i:i+(last_stop-first_stop)])
            start_index=i+1
            stop_idxs=stop_idxs[start_index:]
            all_arrivals=all_arrivals[start_index:]
        return full_routes

    all_full_routes=[]
    for bus_arrival_times in bus_id_to_arrival_times.values():
        full_routes = get_full_routes(bus_arrival_times)
        for route in full_routes:
            print "route"
            print route
            # print [x["time"] for x in route]
            all_full_routes.extend(route)

    full_route_data_map = {
            'stop_name':        [x[0] for x in all_full_routes],
            'stop_idx':         [x[1] for x in all_full_routes],
            'vehicle_idx':      [x[2] for x in all_full_routes],
            'schedule_code':    [x[3] for x in all_full_routes],
            'chunk_idx':        [x[4] for x in all_full_routes],
            'time':             [x[5] for x in all_full_routes],
            'expected_time':    [x[6] for x in all_full_routes],
            'error':            [x[7] for x in all_full_routes],
            'spacing':          [x[8] for x in all_full_routes],
            'spacing_expected': [x[9] for x in all_full_routes],
            }

    print "Total data points: ",len(data_map['stop_name'])
    io.savemat(outfilename, data_map, oned_as = 'row')
    io.savemat("full_routes", full_route_data_map, oned_as = 'row')
