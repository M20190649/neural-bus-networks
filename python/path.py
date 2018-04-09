import gmplot
import tables
from collections import OrderedDict
import math
from scipy import optimize
import matplotlib.pyplot as plt
import numpy as np

bus_ids = ['0497', '2191', '2194', '2297', '2134', '6005', '2204', '2206', '2229', '2149', '2223', '2220', '6009', '2248', '2151', '2174', '2175', '2245', '2178', '2179', '2266', '2241', '2242', '2243', '2288', '2281', '2283', '2284', '2285', '2286', '2287', '2183', '2186', '2185', '2189', '2260', '2123', '2125', '2124', '2126', '2219', '2235', '2237', '2159', '2147', '2146', '2169', '2142', '2251']

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
    # print(R*boston_lat)
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

# Returns the closest point as well as the distance along the path
def closest_point(a, b, p):
    a_to_p = np.subtract(p,a)
    a_to_b = np.subtract(b,a)
    proj = np.dot(a_to_p,a_to_b)/np.linalg.norm(a_to_b)
    return np.add(a,proj*a_to_b/np.linalg.norm(a_to_b)), proj

def get_trajectory(filename):
    route = 1
    bus = bus_ids[11]
    direction = '1_1_var0'
    h5file = tables.open_file(filename)
    VehicleLocations = h5file.root.VehicleLocations
    queryString = "((route == '%s') & (direction == '%s'))" % (route, direction)
    trajectories = VehicleLocations.where(queryString)
    queryResults = [(timePoint['time'], timePoint['vehicleID'], timePoint['latitude'], timePoint['longitude']) for timePoint in trajectories]
    queryResults = sorted(queryResults,key=lambda x:x[0])
    # d = [2] + np.diff([x[0] for x in queryResults])
    # filtered = [lambda x: d[x[0]] > 2 ,enumerate(queryResults)]
    filtered = filter(lambda x: x[1] == bus, queryResults)
    # removes duplicates
    lats = [x[2] for x in filtered]
    lons = [x[3] for x in filtered]
    xs,ys = gps_to_xy(lats,lons)
    m = min([x[0] for x in filtered])
    ts = [x[0]-m for x in filtered]
    return xs,ys,ts

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

def sanitize(percentages,ts):
    print("\n")
    print(len(percentages))
    out = [(percentages[0],ts[0])]
    for i in range(len(ts)-1):
        p1 = percentages[i]
        p2 = percentages[i+1]
        t1 = ts[i]
        t2 = ts[i+1]
        speed = total_distance*(p2-p1)/(t2-t1)
        # print(speed)
        if p2 >= out[-1][0]:
            out.append((p2,t2))
    print(len(out))
    return out


# xs,ys = gps_to_xy(lats,lons)
# ps = [project(x,y,xs,ys) for (x,y) in samples]
# plt.plot(xs, ys, "o")
# plt.plot([x[0] for x in samples],[x[1] for x in samples], "o")
# plt.axis('equal')
# plt.show()
# plt.show()
