#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import time
import datetime
import pytz
import math
import requests
import json
import geopandas as gpd
import folium
from shapely.geometry import LineString
import shapely
from shapely import wkt
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')


# In[2]:


def get_current_time(timezone='Asia/Shanghai'):
    tz = pytz.timezone(timezone)
    dt = datetime.datetime.now(tz)
    return dt

def strftime(t): 
    return datetime.datetime.strftime(t,'%Y-%m-%d %H:%M:%S')


# In[3]:


class TransformCoordinates(object):
    # 坐标转化，主要用到 gcj02_wgs84()
    def __init__(self):
        self.x_pi = 3.14159265358979324 * 3000.0 / 180.0
        self.pi = 3.1415926535897932384626  # π
        self.a = 6378245.0  # 长半轴
        self.ee = 0.00669342162296594323  # 扁率
        
    def gcj02_wgs84(self,lng, lat):
        dlat = self.transformlat(lng - 105.0, lat - 35.0)
        dlng = self.transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [lng * 2 - mglng, lat * 2 - mglat]
    
    def wgs84_gcj02(self,lng, lat):
        dlat = self.transformlat(lng - 105.0, lat - 35.0)
        dlng = self.transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [mglng, mglat]

    def transformlat(self,lng, lat):
        ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 *  math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * self.pi) + 40.0 * math.sin(lat / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * self.pi) + 320 * math.sin(lat * self.pi / 30.0)) * 2.0 / 3.0
        return ret

    def transformlng(self,lng, lat):
        ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 * math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lng * self.pi) + 40.0 * math.sin(lng / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lng / 12.0 * self.pi) + 300.0 * math.sin(lng / 30.0 * self.pi)) * 2.0 / 3.0
        return ret
    
    def coordinates(self,c,tctype='_wgs84'):
        lng,lat = c.split(',')
        lng,lat = float(lng),float(lat)
        if tctype == '_wgs84':
            wlng,wlat = self.gcj02_wgs84(lng,lat)
        elif tctype == '_gcj02':
            wlng,wlat = self.wgs84_gcj02(lng,lat)
        else: print('Check parameters.')
        return wlng,wlat


# In[4]:


def get_traffic(key,blLoc,urLoc,level=5):
    """ Get traffic data from amap API
    Parameters
    ----------
    key: amap api key
    blLoc: bottom left location, "lon,lat", wgs84
    urLoc: upper right location, "lon,lat", wgs84
    level: 1 - 高速（京藏高速）
           2 - 城市快速路、国道(西三环、103国道)
           3 - 高速辅路（G6辅路）
           4 - 主要道路（长安街、三环辅路路）
           5 - 一般道路（彩和坊路）
           6 - 无名道路

    Return: Json data
    """
    # transform coordinates, from wgs84 to gcj02
    tc = TransformCoordinates()
    blLon,blLat = tc.coordinates(blLoc,tctype='_gcj02')
    urLon,urLat = tc.coordinates(urLoc,tctype='_gcj02')
    blLoc = str(blLon) + ',' + str(blLat)
    urLoc = str(urLon) + ',' + str(urLat)
    
    traffic_url = 'https://restapi.amap.com/v3/traffic/status/rectangle'
    params = {'key':key,
              'level':level,
              'extensions': 'all',
              'output':'json',
              'rectangle':'{};{}'.format(blLoc,urLoc)
             }
    response = requests.get(traffic_url,params=params)
#     print(response.request.url)
    data = json.loads(response.text)
    return data


# In[5]:


def parse_traffic(data):
    """parse json data and get infomation
    """
    roads = data['trafficinfo']['roads']
    codes = {'0':'未知','1':'畅通','2':'缓行','3':'拥堵','4':'严重拥堵'}
    traffic_list = []
    for item in roads:
        name = item['name']            # 道路名称
        status_code = item['status']
        status = codes[status_code]
        direction = item['direction']  # 以正东方向为0度，逆时针方向为正，取值范围：[0,360]
        if 'speed' in item.keys():
            speed = item['speed']          # 单位：千米/小时
        else: 
            speed = ''
        lcodes = item['lcodes']
        polyline = item['polyline']

        # transform coordinates
        tc = TransformCoordinates()
        polyline_wgs84 = [tc.coordinates(c,tctype='_wgs84') for c in polyline.split(';')]
        geometry = LineString(polyline_wgs84)
        traffic_list.append([name,status,direction,speed,lcodes,geometry])
        
    cols = ['name','status','direction','speed','lcodes','geometry']
    traffic = gpd.GeoDataFrame(traffic_list,columns=cols)
    return traffic


# In[6]:


def gridding(blLoc,urLoc,size):
    """ Segment area into grids
    Parameters
    ----------
    blLoc: bottom left location, "lon,lat"
    urLoc: upper right location, "lon,lat"
    size: width of square
    """
    blLon,blLat = blLoc.split(',')
    urLon,urLat = urLoc.split(',')
    [blLon,blLat,urLon,urLat] = [float(x) for x in [blLon,blLat,urLon,urLat]]
    
    # transform grid size to delta lon and lat
    deltaLon = size * 360 / (2 * math.pi * 6371004 * math.cos((blLat + urLat) * math.pi / 360))
    deltaLat = size * 360 / (2 * math.pi * 6371004)
    numLon = math.ceil((urLon - blLon) / deltaLon)
    numLat = math.ceil((urLat - blLat) / deltaLat)
    print('The area is divided into {} grids, {} in rows and {} in columns'.format(numLon*numLat,numLon,numLat))
    
    grids = []
    for i in range(numLon):
        for j in range(numLat):
            blLon_grid = blLon + deltaLon * i
            blLat_grid = blLat + deltaLat * j
            urLon_grid = min(blLon + deltaLon * (i + 1), urLon)
            urLat_grid = min(blLat + deltaLat * (j + 1), urLat)
            poly = shapely.geometry.box(blLon_grid,blLat_grid,urLon_grid,urLat_grid).wkt
            grids.append([i, j, str(blLon_grid) + ',' + str(blLat_grid), str(urLon_grid) + ',' + str(urLat_grid),poly])
    grids = pd.DataFrame(grids,columns = ['xid','yid','blc','urc','geometry'])
    grids['geometry'] = grids['geometry'].apply(wkt.loads)
    grids = gpd.GeoDataFrame(grids,geometry='geometry')
    return grids


# In[16]:


if __name__ == '__main__':
    # (shanghai) parameters setting  
    key = ''
    bl = '120.852620,30.677790'
    ur = '122.242919,31.874625'
    levels = [1,2,3,4,5,6]
    size = 7000
    
    grids = gridding(bl,ur,size)
    res = gpd.GeoDataFrame(columns=['level','name','status','direction','speed','lcodes','geometry'])
    err_idx = []
    for level in levels:
        t0 = get_current_time()
        level_codes = {1:'高速',2:'城市快速路、国道',3:'高速辅路',4:'主要道路',5:'一般道路',6:'无名道路'}
        road = level_codes[level]
        for i in range(len(grids)):
            try:
                data = get_traffic(key,grids.loc[i,'blc'],grids.loc[i,'urc'],level)
            except:  # TimeoutError
                time.sleep(10)
                data = get_traffic(key,grids.loc[i,'blc'],grids.loc[i,'urc'],level)
            
            # print errors.  Amap error code: https://lbs.amap.com/api/webservice/guide/tools/info/
            if data['status'] == '0':
                err_idx.append(i)
                continue
                if data['info'] != 'UNKNOWN_ERROR':
                    print('Error occurs at {}: {}'.format(i,data['infocode']))
                
            traffic = parse_traffic(data)
            traffic['level'] = level
            res = pd.concat([res,traffic],axis=0,ignore_index=True)
            
        t1 = get_current_time()
        print('{}: finished!'.format(road))
        print('Run from {} to {}, and consume {} minutes.'.format(strftime(t0), strftime(t1),(t1 - t0).seconds / 60))
        print('\n')

    res.to_file(r'C:\Users\ZY\Desktop\交通态势\traffic.shp',encoding='utf-8')


# In[17]:


    # visualization
    sh = gpd.read_file(r'E:\2_Data\全国行政边界数据-高德API\研究范围\上海区县边界.shp',encoding='utf-8')

    location = ((np.array(bl.split(',')[::-1],dtype=float) + np.array(ur.split(',')[::-1],dtype=float)) / 2).tolist()
    m = folium.Map(location=location, zoom_start=10, tiles='OpenStreetMap')  # 'OpenStreetMap','Stamen Toner','cartodbpositron'
    folium.Choropleth(sh.to_json(),line_weight=1,fill_opacity=0,line_color='black',name='Shanghai Boundary').add_to(m)
    folium.Choropleth(grids.to_json(),fill_opacity=0,line_weight=1,line_color='green',name='Grid').add_to(m)
    folium.Choropleth(grids[grids.index.isin(err_idx)].to_json(),fill_opacity=0,line_weight=1,line_color='red',name='Error grid').add_to(m)
    folium.Choropleth(res[res.level==1].to_json(),line_weight=1,line_color='blue',name='高速').add_to(m)
    folium.Choropleth(res[res.level==2].to_json(),line_weight=1,line_color='blue',name='城市快速路、国道').add_to(m)
    folium.Choropleth(res[res.level==3].to_json(),line_weight=1,line_color='blue',name='高速辅路').add_to(m)
    folium.Choropleth(res[res.level==4].to_json(),line_weight=1,line_color='blue',name='主要道路').add_to(m)
    folium.Choropleth(res[res.level==5].to_json(),line_weight=1,line_color='blue',name='一般道路').add_to(m)
    folium.Choropleth(res[res.level==6].to_json(),line_weight=1,line_color='blue',name='无名道路').add_to(m)

    folium.LayerControl().add_to(m)
    m


# In[ ]:




