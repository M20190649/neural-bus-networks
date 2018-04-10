import numpy as np
import path

np.set_printoptions(threshold=np.nan)
a = path.get_features("/Volumes/Infinity/mbta/h5/2014/mbta_trajectories_2014_13.h5")
for i in a:
    print((i))
