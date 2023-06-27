#Holds custom colormaps to use in ttrappy

import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import pickle

class TtrappyColormap():

 
    def __init__(self):
    
        #Colormaps created from what I have in GR2 at the moment
                
        self.cmaps = {}
        self.minMax = {}
    
        ref = None
        vel = None
        with open('ttrappy/colors/ref.pkl', 'rb') as f:
            ref = pickle.load(f)
        with open('ttrappy/colors/vel.pkl', 'rb') as f:
            vel = pickle.load(f)
        
        self.cmaps["reflectivity"] = LinearSegmentedColormap.from_list("reflectivity", ref, N=1223)
        self.cmaps["velocity"] = LinearSegmentedColormap.from_list("velocity", vel, N=1223)
        self.minMax["reflectivity"] = (-15, 80)
        self.minMax["velocity"] = (-115, 115)
        
        return