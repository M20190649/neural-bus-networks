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


"Row by row copy of table - attempts to recover broken table"
if True:
    import sys
    try:
        file2, file1 = sys.argv[1:3]
    except:
	print "Usage: h5remake.py [old_file.h5] [new_recovery_file.h5]"

    import os
    if os.path.exists(file1):
	 raise ValueError, file1+' exists. stop'

    compressionOptions = tables.Filters(complevel=9, complib='blosc')
    f1 = tables.openFile(file1, 'w', filters = compressionOptions)
    f2 = tables.openFile(file2)

    t1 = f1.create_table('/', 'VehicleLocations', VehicleLocation, 'MBTA vehicle positions',
		    filters = compressionOptions, expectedrows=240000000)
    t2 = f2.root.VehicleLocations

    #Part 2. Parse vehicle location data.
    if True:#try:
        for n, row in enumerate(t2):
            newrow = t1.row
            print n#,
            for field in ('direction', 'heading', 'latitude', 'longitude',
                    'route', 'time', 'vehicleID'):
                newrow[field] = row[field]
                #print field,':', row[field], ' ',
            #print
            newrow.append()
            #t1.flush()
    #except e:
    #    print e
    #    pass

    f1.close()
    f2.close()


