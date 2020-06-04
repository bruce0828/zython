#!/usr/bin/env python
# coding: utf-8

# In[21]:


"""
*****************************************************************************************
This function is used to plot geodata based on the discrete bounds, improving the geopandas plot.
Env: python 3.7

Author: Yang Zhou, e-mail: txzhpy@gmail.commuters
Update date: June 4, 2020
*****************************************************************************************
"""

# import packages
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import ListedColormap
get_ipython().run_line_magic('matplotlib', 'inline')

def geoplot_listed_colormap(gdf,column,bound,ax=None,cmap='Reds',cmap_display=False,fig=None):
    
    """ improved geopandas.plot() function, plotting based on discrete listedcmap
    Params:
        gdf: geodataframe
        column: same to gdf.plot(column) 
        bound: list type, values between vmin and vmax
        cmap: same to gdf.plot(cmap)
        cmap_display: show the color bar. If cmap_display=True, fig must add the input.
    """    
    # bounds
    vmin = gdf[column].min()
    vmax = gdf[column].max()
    bounds = [vmin] + bound + [vmax]
    
    def bound_value(x,bounds):
        for i,(bmin,bmax) in enumerate(zip(bounds[:-1],bounds[1:])):
            if i == 0 and x == bmin: return i
            elif bmin < x <= bmax: return i
            
    gdf['csign'] = gdf[column].apply(lambda x: bound_value(x,bounds))
    
    # colormap
    c = mpl.cm.get_cmap(cmap, 256)
    colors = c(np.linspace(0, 1, len(bounds)-1))
    cmap = ListedColormap(colors)
    gdf.plot(ax=ax,column='csign',cmap=cmap)
    
    # colorbar
    if cmap_display:
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        cbar = fig.colorbar(mappable=mpl.cm.ScalarMappable(cmap=cmap), cax=cax,ticks=np.linspace(0,1,len(bounds)))
        cbar.ax.set_yticklabels(bounds)  # vertically oriented colorbar


# In[35]:


if __name__ == '__main__':
    """ Example
    """
    # read data
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    
    # compare two plotting mathods
    fig,ax = plt.subplots(figsize=(15,5))
    ax1 = plt.subplot(121)
    geoplot_listed_colormap(gdf=world,column='pop_est',bound=[0.5*10e7,1*10e7,2*10e7,3*10e7],cmap='Reds',cmap_display=True,fig=fig,ax=ax1)
    ax1.set_xticks([])
    ax1.set_yticks([])
    
    ax2 = plt.subplot(122)
    world.plot(column='pop_est',cmap='Reds',ax=ax2)
    ax2.set_xticks([])
    ax2.set_yticks([])
    plt.subplots_adjust(wspace=0.1)

