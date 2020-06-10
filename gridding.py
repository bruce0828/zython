"""
*****************************************************************************************
This function is used to cut geographic data into fixed-size grids (square)
Env: python 3.7

Author: Yang Zhou, e-mail: txzhpy@gmail.com
Update date: June 4, 2020
*****************************************************************************************
"""


import pandas as pd
import geopandas as gpd
from shapely.geometry import Point,Polygon,MultiPolygon
import shapely
from shapely import wkt
import folium
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')



def gridding(blLoc,urLoc,size,bound=None):
    """ Segment area into grids
    Parameters
    ----------
    blLoc: bottom left location, "lon,lat"
    urLoc: upper right location, "lon,lat"
    size: width of square
    bound: if set, extract grids within polygon; if not, return all grids within rectangle
    
    Retures
    -------
    grids: geodataframe
    """
    blLon,blLat = blLoc.split(',')
    urLon,urLat = urLoc.split(',')
    [blLon,blLat,urLon,urLat] = [float(x) for x in [blLon,blLat,urLon,urLat]]
    
    # transform grid size to delta lon and lat
    deltaLon = size * 360 / (2 * math.pi * 6371004 * math.cos((blLat + urLat) * math.pi / 360))
    deltaLat = size * 360 / (2 * math.pi * 6371004)
    numLon = math.ceil((urLon - blLon) / deltaLon)
    numLat = math.ceil((urLat - blLat) / deltaLat)
    
    grids = []
    for i in range(numLon):
        for j in range(numLat):
            blLon_grid = blLon + deltaLon * i
            blLat_grid = blLat + deltaLat * j
            urLon_grid = min(blLon + deltaLon * (i + 1), urLon)
            urLat_grid = min(blLat + deltaLat * (j + 1), urLat)
            poly = shapely.geometry.box(blLon_grid,blLat_grid,urLon_grid,urLat_grid)
            poly_wkt = poly.wkt
            
            # grids within polygon
            if bound is not None:
                # standardize type of bound
                if type(bound) is gpd.geodataframe.GeoDataFrame:
                    bound.reset_index(inplace=True)
                    bound = bound.loc[0,'geometry']
                elif type(bound) in [shapely.geometry.multipolygon.MultiPolygon,shapely.geometry.polygon.Polygon]:
                    pass
                else:
                    print('Please check the type of bound.')
                
                if bound.contains(poly.centroid):
                    grids.append([i, j, str(blLon_grid) + ',' + str(blLat_grid), str(urLon_grid) + ',' + str(urLat_grid),poly_wkt])
                else:
                    continue
            else:
                grids.append([i, j, str(blLon_grid) + ',' + str(blLat_grid), str(urLon_grid) + ',' + str(urLat_grid),poly_wkt])
    
    grids = pd.DataFrame(grids,columns = ['xid','yid','blc','urc','geometry'])
    grids['geometry'] = grids['geometry'].apply(wkt.loads)
    grids = gpd.GeoDataFrame(grids,geometry='geometry')
    grids.crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    print('The area is divided into {} grids, {} in rows and {} in columns'.format(len(grids),numLon,numLat))
    return grids


if __name__ == '__main__':
    # example
    # Nanjing county boundary
    nj_county = gpd.read_file(r'E:\2_Data\南京\行政区划\南京区县区划.shp',encoding='utf-8')
    nj = nj_county.dissolve('City').reset_index()

    # Nanjing bounds
    (minx,miny,maxx,maxy) = nj.loc[0,'geometry'].bounds
    print('边界: ',minx,miny,maxx,maxy)

    # Nanjing centriod
    print('中心: ',nj.loc[0,'geometry'].centroid.wkt)

    # gridding
    blLoc = str(minx) + ',' + str(miny)
    urLoc = str(maxx) + ',' + str(maxy)
    grids = gridding(blLoc,urLoc,size=5000,bound=nj)

    # visualization
    location = [31.92763,118.84152]
    m = folium.Map(location=location, zoom_start=10, tiles='OpenStreetMap')  # 'OpenStreetMap','Stamen Toner','cartodbpositron'
    folium.Choropleth(nj_county.to_json(),line_weight=1,fill_opacity=0,line_color='black',name='Nanjing').add_to(m)
    folium.Choropleth(grids.to_json(),fill_opacity=0,line_weight=1,line_color='blue',name='Grid').add_to(m)
    folium.LayerControl().add_to(m)
