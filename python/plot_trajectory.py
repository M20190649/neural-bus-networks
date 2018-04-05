import tables
import gmplot
import numpy as np
import math
from scipy.interpolate import splprep, splev

np.set_printoptions(threshold=np.nan)
filename = "/Volumes/Infinity/mbta/h5/2016/mbta_trajectories_2016_01.h5"
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
filtered = queryResults
filtered = filter(lambda x: x[1] == bus, queryResults)
lats = [x[2] for x in filtered]
lons = [x[3] for x in filtered]
# radius of earth in m
R = 6371* 1000
# xs = [R*math.cos(lats[i]*180/math.pi)*math.cos(lons[i]*180/math.pi) for i in range(len(filtered))]
# ys = [R*math.cos(lats[i]*180/math.pi)*math.sin(lons[i]*180/math.pi) for i in range(len(filtered))]
xs = [-R*lons[i]*math.cos(lats[0]*180/math.pi) for i in range(len(filtered))]
ys = [R*lats[i] for i in range(len(filtered))]
m = min([x[0] for x in filtered])
ts = [x[0]-m for x in filtered]

# m = min([x[0] for x in filtered])
# print(np.diff([int(x[0]) for x in sorted(map(lambda x: [x[0]-m,x[1],x[2],x[3]],filtered),key=lambda x : x[0])]))
# print(diff)
boston_lat = 42.3528
boston_lon = -71.1048
gmap = gmplot.GoogleMapPlotter(boston_lat, boston_lon, 14)
gmap.scatter(lats, lons, '#3B0B39', size=40, marker=False)
# gmap.draw("mymap.html")

# spline parameters
s=3.0 # smoothness parameter
k=2 # spline order
nest=-1 # estimate of number of knots needed (-1 = maximal)

tckp,u = splprep([xs,ys,ts],s=s,k=k,nest=-1)


# print(u)
# print(tckp)
# evaluate spline, including interpolated points
xnew,ynew,znew = splev(np.linspace(0,1,400),tckp)

import pylab
pylab.subplot(1,1,1)
data,=pylab.plot(xs,ys,'bo-',label='data')
fit,=pylab.plot(xnew,ynew,'r-',label='fit')
# pylab.scatter(xs,ys)
pylab.legend()
pylab.show()
