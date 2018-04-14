import gmplot
import json
import scrapetimetable
import datetime
import tables
import math
from scipy import optimize
import scipy.io as io
import matplotlib.pyplot as plt
import numpy as np

# bus_ids = ['0497', '2191', '2194', '2297', '2134', '6005', '2204', '2206', '2229', '2149', '2223', '2220', '6009', '2248', '2151', '2174', '2175', '2245', '2178', '2179', '2266', '2241', '2242', '2243', '2288', '2281', '2283', '2284', '2285', '2286', '2287', '2183', '2186', '2185', '2189', '2260', '2123', '2125', '2124', '2126', '2219', '2235', '2237', '2159', '2147', '2146', '2169', '2142', '2251']

# Paramaterizes the path of the 1 bus
path_lats = [42.373989, 42.373203, 42.375638, 42.375908, 42.375576, 42.374745, 42.372336, 42.372210, 42.371048, 42.368632, 42.360855, 42.359038, 42.343444, 42.340393, 42.333535, 42.331213, 42.332889, 42.331979, 42.330677, 42.330037]
path_lons = [-71.118910, -71.118116, -71.118449, -71.117848, -71.115702, -71.114484, -71.115128, -71.115643,-71.116074, -71.109294, -71.096016, -71.093586, -71.085840, -71.081463, -71.073351, -71.076999, -71.081076, -71.081699, -71.083244, -71.084317]

boston_lat = 42.3528
boston_lon = -71.1048
boston_x = 1092798.35753
boston_y = 2698296.888

n = len(path_lats)

def get_total_distance(xs,ys):
    d = 0
    for i in range(len(xs)-1):
        x1,x2 = xs[i],xs[i+1]
        y1,y2 = ys[i],ys[i+1]
        d += np.linalg.norm((x2-x1,y2-y1))
    return d

def plot_map(lats,lons):
    gmap = gmplot.GoogleMapPlotter(boston_lat, boston_lon, 14)
    gmap.scatter(lats, lons, '#3B0B39', size=40, marker=False)
    gmap.draw("mymap.html")

# Convert to a reasonable x,y paramaterization
def gps_to_xy(lats,lons):
    # radius of earth, pretty rough though
    R = 6371
    xs = [-R*lon*math.cos(path_lats[0]*180/math.pi)-boston_y for lon in lons]
    ys = [R*lat-boston_y for lat in lats]
    return xs,ys

def get_path():
    return gps_to_xy(path_lats,path_lons)

path = get_path()
total_distance = get_total_distance(path[0],path[1])

# Takes in a point (x,y) and a set of points (xs,ys) which create a piecewise linear path
# Then projects the point onto the closest linear section of that path
def project(x,y,xs,ys):
    smallest_d = "Taylor"
    point = None
    cum_distance = 0
    percentage = 0
    best_proj = 0
    for i in range(len(xs)-1):
        x1,x2 = xs[i],xs[i+1]
        y1,y2 = ys[i],ys[i+1]
        c,p = closest_point((x1,y1),(x2,y2),(x,y))
        d = np.linalg.norm(np.subtract(c,(x,y)))
        if d < smallest_d:
            smallest_d = d
            best_proj = p
            if p< 0 :
                p = 0
            percentage = (cum_distance + p) / total_distance
            point = c
        cum_distance += np.linalg.norm((x2-x1,y2-y1))
    return point,percentage

# https://stackoverflow.com/questions/3749512/python-group-by
def group_by(seqs,idx=0,merge=True):
    d = dict()
    for seq in seqs:
        k = seq[idx]
        v = d.get(k,tuple()) + (seq[:idx]+seq[idx+1:] if merge else (seq[:idx]+seq[idx+1:],))
        d.update({k:v})
    return d

# Returns the closest point as well as the distance along the path
def closest_point(a, b, p):
    a_to_p = np.subtract(p,a)
    a_to_b = np.subtract(b,a)
    proj = np.dot(a_to_p,a_to_b)/np.linalg.norm(a_to_b)
    return np.add(a,proj*a_to_b/np.linalg.norm(a_to_b)), proj

# Takes in a filename and then returns the (xs,ys,ts) for each bus in a dictionary
def get_trajectory(filename):
    route = 1
    direction = '1_1_var0'
    h5file = tables.open_file(filename)
    VehicleLocations = h5file.root.VehicleLocations
    queryString = "((route == '%s') & (direction == '%s'))" % (route, direction)
    trajectories = VehicleLocations.where(queryString)
    queryResults = [(timePoint['time'], timePoint['vehicleID'], timePoint['latitude'], timePoint['longitude']) for timePoint in trajectories]
    d = group_by(queryResults,1,False)
    # Tuples of (time,lat,lon)
    bus_to_trajectory = {}
    for vehicleID in d:
        d[vehicleID] = sorted(d[vehicleID],key=lambda x:x[0])
        lats = [x[1] for x in d[vehicleID]]
        lons = [x[2] for x in d[vehicleID]]
        ts = [x[0] for x in d[vehicleID]]
        xs,ys = gps_to_xy(lats,lons)
        bus_to_trajectory[vehicleID] = (xs,ys,ts)
    return bus_to_trajectory

# Slices up a trajectory into each route
def get_cuts(xs,ys,ts):
    cuts = [0]
    time_threshold = 120
    distance_threshold = 1000
    for i in range(len(xs)-1):
        x1,x2 = xs[i],xs[i+1]
        y1,y2 = ys[i],ys[i+1]
        t1,t2 = ts[i],ts[i+1]
        if t2-t1 > time_threshold:
            cuts.append(i+1)
        elif math.sqrt((x2-x1)**2 + (y2-y1)**2) > distance_threshold:
            cuts.append(i+1)
    cuts.append(len(xs))
    return cuts

# Make sure there aren't any weird jumps in speed
def sanitize(times,percentages):
    out = [(percentages[0],times[0])]
    for i in range(len(times)-1):
        p1 = percentages[i]
        p2 = percentages[i+1]
        t1 = times[i]
        t2 = times[i+1]
        if (t2-out[-1][1]) <= 0:
            continue
        speed = total_distance*(p2-out[-1][0])/(t2-out[-1][1])
        if 0 <= speed < 0.7:
            out.append((p2,t2))
    percentages_out = [x[0] for x in out]
    times_out = [x[1] for x in out]
    return percentages_out,times_out

# Just get the location of the stop and their percentage along the route
def get_stops():
    # Represents stops with location
    bus_stop_data, directions = scrapetimetable.ReadRouteConfig(route = 1)
    the_direction = "Inbound" # Or "Outbound"
    tags = []
    for direction in directions:
        if direction[0]["name"] == the_direction:
            tags = set([x["tag"] for x in direction[1:]])
    bus_stop_data = filter(lambda x: x["tag"] in tags,bus_stop_data)
    lats = [float(x["lat"]) for x in bus_stop_data]
    lons = [float(x["lon"]) for x in bus_stop_data]
    xs,ys = gps_to_xy(lats,lons)
    pxs,pys = gps_to_xy(path_lats,path_lons)
    l = map(lambda p: project(p[0],p[1],pxs,pys), zip(xs,ys))
    stops = [x[0] for x in l]
    percentages = [x[1] for x in l]
    return stops, percentages

_, stop_percentages = get_stops()
# Computes the arrival time at each stop given the times and z for a bus
def get_arrival_times(times,percentages):
    current_stop = 0
    out = {}
    i = 0
    delta = 0.005
    for stop,stop_percentage in enumerate(stop_percentages):
        while i < len(percentages)-2 and percentages[i+1] < stop_percentage - delta:
            i += 1
        p1 = percentages[i]
        p2 = percentages[i+1]
        t1 = times[i]
        t2 = times[i+1]
        stop_str = "stop_" + str(stop)
        if p1 - delta < stop_percentage < p1 + delta:
            time = t1
            out[stop_str]=time
        elif p2 - delta < stop_percentage < p2 + delta:
            time = t2
            out[stop_str]=time
        elif p1 <= stop_percentage <= p2:
            # Just a little interpolation
            time = t1 + (t2-t1)*(stop_percentage-p1)/(p2-p1)
            out[stop_str]=time
    return out

plot = False
plot_route = False
stops,stop_percentages = get_stops()

# Get all the features we want from a file, ready for training
def get_features(file):
    out = []
    bus_to_trajectory = get_trajectory(file)
    for vehicleID in bus_to_trajectory:
        xs,ys,ts = bus_to_trajectory[vehicleID]
        cuts = get_cuts(xs,ys,ts)
        path_x,path_y = get_path()
        for i in range(len(cuts)-1):
            cut_start = cuts[i]
            cut_end = cuts[i+1]
            l = cut_end - cut_start
            if l < 100:
                continue
            xss = xs[cut_start:cut_end]
            yss = ys[cut_start:cut_end]
            tss = ts[cut_start:cut_end]
            mt = min(tss)
            # tss = [x-mt for x in tss]
            projection = [project(x,y,path_x,path_y) for (x,y) in zip(xss,yss)]
            percentages = [p[1] for p in projection]
            percentages, tss = sanitize(tss,percentages)
            arrival_times = get_arrival_times(tss,percentages)
            if plot:
                if plot_route:
                    plt.plot(xss,yss,'bo-',label='trajectory')
                    plt.axis('equal')
                else:
                    max_t = max(tss)
                    plt.plot(tss,percentages,'bo-',label='data')
                    for p in stop_percentages:
                        plt.plot((0, max_t), (p,p), 'r-')
                    for k in arrival_times:
                        if "stop" in k:
                            plt.plot((arrival_times[k], arrival_times[k]), (0,1), 'g-')
                plt.legend()
                plt.show()
            date = datetime.datetime.fromtimestamp(mt).date()
            time = datetime.datetime.fromtimestamp(mt).time()
            schedule_code = scrapetimetable.TimeToScheduleCode(date)
            arrival_times["bus_id"] = vehicleID
            arrival_times["start_time"] = mt
            arrival_times["schedule_code"] = schedule_code
            arrival_times["day_of_week"] = date.weekday()
            arrival_times["hour"] = time.hour
            arrival_times["year"] = date.year
            out.append(arrival_times)
    # io.savemat(file[0:-3]+"_out", out, oned_as = 'row')
    with open(file[0:-3]+".json", 'w') as outfile:
        json.dump(out, outfile)
    return out


get_features("/Volumes/Infinity/mbta/h5/2014/mbta_trajectories_2014_15.h5")
