#!/usr/bin/env python
#Combine HDF5 files
import datetime
import tables

class VehicleLocation(tables.IsDescription):
    vehicleID = tables.StringCol(4)
    route     = tables.StringCol(8)
    direction = tables.StringCol(16)
    latitude  = tables.Float64Col()   #Reported latitude
    longitude = tables.Float64Col()   #Reported longitude
    time      = tables.Float64Col()   #Time stamp in seconds since epoch time
    heading   = tables.UInt16Col()    #Heading in degrees

import sys
try:
    file2, file1 = sys.argv[1:3]
except ValueError:
    print "Specify the names of at least two files. The first will be extended by all the others"
    exit(1)

if True:
    import sys
    try:
	file2, file1 = sys.argv[1:3]
    except ValueError:
	print "Specify the names of two files. The second will be extended by the first."
	exit(1)
    #Hash present data
    presentData = {}
    f2 = tables.openFile(file2, 'a')
    t2 = f2.root.VehicleLocations
    print "Loading ", len(t2), "entries from ", file2
    for row in t2:
        presentData[row['vehicleID'], row['time']] = True

    #Part 2. Parse vehicle location data.
    for file1 in sys.argv[2:]:
        f1 = tables.openFile(file1)
        t1 = f1.root.VehicleLocations
        print "Loading ", len(t1), "entries from ", file1
        newdata = 0
        for n, row in enumerate(t1):
            if (row['vehicleID'], row['time']) not in presentData:
                newrow = t2.row
                for field in ('direction', 'heading', 'latitude', 'longitude',
                        'route', 'time', 'vehicleID'):
                    newrow[field] = row[field]
                newrow.append()
                #t2.flush()
                presentData[row['vehicleID'], row['time']] = True
                newdata += 1

                #Delete keys that are too old
                #for vehicle, time in presentData.keys():
	        #    if row['time'] - time > 300: #5 minutes
	        #		del presentData[(vehicle, time)]

        print "Added ", newdata, "new entries"
        f1.close()

    f2.close()

