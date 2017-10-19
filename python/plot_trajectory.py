import tables
import gmplot

filename = "data/mbta_trajectories_2016_01.h5"
bus_ids = ['0497', '2191', '2194', '2297', '2134', '6005', '2204', '2206', '2229', '2149', '2223', '2220', '6009', '2248', '2151', '2174', '2175', '2245', '2178', '2179', '2266', '2241', '2242', '2243', '2288', '2281', '2283', '2284', '2285', '2286', '2287', '2183', '2186', '2185', '2189', '2260', '2123', '2125', '2124', '2126', '2219', '2235', '2237', '2159', '2147', '2146', '2169', '2142', '2251']
route = 1
bus = bus_ids[10]
direction = '1_1_var0'
h5file = tables.open_file(filename)

VehicleLocations = h5file.root.VehicleLocations
queryString = "((route == '%s') & (direction == '%s'))" % (route, direction)
trajectories = VehicleLocations.where(queryString)

queryResults = [(timePoint['time'], timePoint['vehicleID'], timePoint['latitude'], timePoint['longitude']) for timePoint in trajectories]
filtered = filter(lambda x: x[1] == bus, queryResults)
lats = [x[2] for x in filtered]
lons = [x[3] for x in filtered]

boston_lat = 42.3528
boston_lon = -71.1048
gmap = gmplot.GoogleMapPlotter(boston_lat, boston_lon, 14)
gmap.scatter(lats, lons, '#3B0B39', size=40, marker=False)
gmap.draw("mymap.html")
