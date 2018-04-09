import numpy as np
import path
import pylab

np.set_printoptions(threshold=np.nan)

xs,ys,ts = path.get_trajectory("/Volumes/Infinity/mbta/h5/2014/mbta_trajectories_2014_13.h5")
cuts = path.get_cuts(xs,ys,ts)
path_x,path_y = path.get_path()

for i in range(len(cuts)-1):
    cut_start = cuts[i]
    cut_end = cuts[i+1]
    l = cut_end - cut_start
    # print(l)
    if l < 100:
        continue

    xss = xs[cut_start:cut_end]
    yss = ys[cut_start:cut_end]
    tss = ts[cut_start:cut_end]

    projection = [path.project(x,y,path_x,path_y) for (x,y) in zip(xss,yss)]
    ps = [p[0] for p in projection]
    percentages = [p[1] for p in projection]
    px = [p[0] for p in ps]
    py = [p[1] for p in ps]
    sanitary = path.sanitize(percentages, tss)
    pylab.plot(list(x[1] for x in sanitary),list(x[0] for x in sanitary),'bo-',label='data')
    # pylab.plot(tss,percentages,'bo-',label='data')
    # pylab.plot(xss,yss,'bo-',label='data')
    # print(tss)
    # pylab.plot(path_x,path_y,'ro-',label='swag')
    # pylab.plot(px,py,'go-',label='swag')
    pylab.legend()
    # pylab.axis('equal')
    pylab.show()
    # break
