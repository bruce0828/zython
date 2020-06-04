#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')

def geoplot_in_bound(gdf,column,bound,ax=None,cmap='Reds',cmap_display=False,fig=None):
    
    """ improved geopandas.plot() function, plotting based on discrete listedcmap
    Params:
        gdf: geodataframe
        column: same to gdf.plot(column) 
        bound: list type, values between vmin and vmax
        cmap: same to gdf.plot(cmap)
        cmap_display: show the color bar. If cmap_display=True, fig must add the input.
    """
    # import packages
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from matplotlib.colors import ListedColormap
    
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
        ("")

if __name__ == '__main__':
    # parameters
    bound = [10,50,100,200]
    
    # single map, with colormap
    fig,ax = plt.subplots(figsize=(7,7))  
    geoplot_in_bound(gdf=hfnc_xf_1000.fillna(0),column='cnt',bound=bound,cmap='Oranges',cmap_display=True,fig=fig,ax=ax)

    # multiple map, without colormap
    bmap = gpd.read_file(r'E:\2_Data\全国行政边界数据-高德API\研究范围\上海苏州南通-区县.shp',encoding='utf-8')
    sh = gpd.read_file(r'E:\2_Data\全国行政边界数据-高德API\研究范围\上海市域边界.shp',encoding='utf-8')
    
    fig = plt.figure(1,(15,10))  
    ax = plt.subplot(131)
    geoplot_in_bound(ax=ax,gdf=hfc_tq_1000.fillna(0),column='cnt',bound=bound)
    ax.set_title("High-frequency commuters' commuting")
    sh.plot(ax=ax,facecolor="none",edgecolor='k',linewidth=0.3)
    ax.set_xticks([])
    ax.set_yticks([])

    ax2 = plt.subplot(132)
    geoplot_in_bound(ax=ax2,gdf=hfc_xf_1000.fillna(0),column='cnt',bound=bound)
    ax2.set_title("High-frequency commuters' consumption")
    sh.plot(ax=ax2,facecolor="none",edgecolor='k',linewidth=0.3)
    ax2.set_xticks([])
    ax2.set_yticks([])

    ax3 = plt.subplot(133)
    geoplot_in_bound(ax=ax3,gdf=hfnc_xf_1000.fillna(0),column='cnt',bound=bound)
    ax3.set_title("High-frequency non-commuters' consumption")
    sh.plot(ax=ax3,facecolor="none",edgecolor='k',linewidth=0.3)
    ax3.set_xticks([])
    ax3.set_yticks([])

    plt.subplots_adjust(wspace=0.1)

# plt.savefig(fname=r'C:\Users\ZY\Desktop\high-frequency.png',bbox_inches='tight',pad_inches=0.1,dpi=300)

