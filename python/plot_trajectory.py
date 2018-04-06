import tables
import gmplot
import numpy as np
import math
import path
from scipy.interpolate import splprep, splev

np.set_printoptions(threshold=np.nan)
filename = "/Volumes/Infinity/mbta/h5/2014/mbta_trajectories_2014_13.h5"
bus_ids = ['0497', '2191', '2194', '2297', '2134', '6005', '2204', '2206', '2229', '2149', '2223', '2220', '6009', '2248', '2151', '2174', '2175', '2245', '2178', '2179', '2266', '2241', '2242', '2243', '2288', '2281', '2283', '2284', '2285', '2286', '2287', '2183', '2186', '2185', '2189', '2260', '2123', '2125', '2124', '2126', '2219', '2235', '2237', '2159', '2147', '2146', '2169', '2142', '2251']
route = 1
bus = bus_ids[11]
direction = '1_1_var0'
# h5filenames = glob('/Volumes/Infinity/mbta/h5/2014/*.h5')
# for filename in h5filenames:
h5file = tables.open_file(filename)

VehicleLocations = h5file.root.VehicleLocations
queryString = "((route == '%s') & (direction == '%s'))" % (route, direction)
trajectories = VehicleLocations.where(queryString)

queryResults = [(timePoint['time'], timePoint['vehicleID'], timePoint['latitude'], timePoint['longitude']) for timePoint in trajectories]
queryResults = sorted(queryResults,key=lambda x:x[0])
d = [2] + np.diff([x[0] for x in queryResults])
# print(d)
filtered = [lambda x: d[x[0]] > 2 ,enumerate(queryResults)]
filtered = filter(lambda x: x[1] == bus, queryResults)
lats = [x[2] for x in filtered]
lons = [x[3] for x in filtered]
# radius of earth in m
xs,ys = path.gps_to_xy(lats,lons)
m = min([x[0] for x in filtered])
ts = [x[0]-m for x in filtered]

boston_lat = 42.3528
boston_lon = -71.1048
gmap = gmplot.GoogleMapPlotter(boston_lat, boston_lon, 14)

gmap.scatter(lats, lons, '#3B0B39', size=40, marker=False)
gmap.draw("mymap.html")



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


# spline parameters
s=3.0 # smoothness parameter
k=1 # spline order
nest=-1 # estimate of number of knots needed (-1 = maximal)

for i in range(len(cuts)-1):
    cut_start = cuts[i]
    cut_end = cuts[i+1]
    l = cut_end - cut_start
    if l < 100:
        continue
    print("\n")
    print("length of sequence: ",l)
    xss = xs[cut_start:cut_end]
    yss = ys[cut_start:cut_end]
    tss = ts[cut_start:cut_end]
    print(zip(xss,yss))
    tckp,u = splprep([xss,yss,tss],s=s,k=k,nest=-1)
    xnew,ynew,znew = splev(np.linspace(0,1,l*2),tckp)

    import pylab
    pylab.subplot(1,1,1)
    data,=pylab.plot(xss,yss,'bo-',label='data')
    # fit,=pylab.plot(xnew,ynew,'r-',label='fit')
    for i,v in enumerate(xss):
        pylab.annotate(i,(xss[i]+np.random.rand()*100,yss[i]+np.random.rand()*100))
# pylab.scatter(xs,ys)
    pylab.legend()

    pylab.axis('equal')
    pylab.show()
