#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
from matplotlib.colors import ListedColormap
import folium
from folium.plugins import HeatMap
import geopandas as gpd

get_ipython().run_line_magic('matplotlib', 'inline')

pd.set_option('max_columns',50)


# In[2]:


def encode(data,to_='pat'):
    """ activity pattern encode transforming between letter and number
    Parameters
    ----------
    data: activity pattern
    to_:  'pat' or 'num'.
          'pat' is to transform number to pattern
          'num' is to transform pattern to number
    """
    code = {'H':1,'W':2,'S':3,'E':4,'B':5,'D':6,'R':7,'O':8}
    code_r = dict((v,k) for k,v in code.items())
    if to_ == 'num':
        num = data.applymap(lambda x: code[x])
        return num
    elif to_ == 'pat':
        pat = data.applymap(lambda x: code_r[x])
        return pat


def activity_pattern():
    """ read activity pattern
    """
    fname = r'E:\8.0 博士研究\R9 出行目的识别\Data process\activity_pattern_noT.csv'
    actiPattern = pd.read_csv(fname,index_col='PersonID')
    return actiPattern


def cluster(n):
    """ clustering results
    Paramter: n, number of classes
    return:   cls, clustering dataframe
    """
    fname = r'E:\8.0 博士研究\R9 出行目的识别\results\Markov chain based\class-{}.txt'.format(str(n))
    cls = pd.read_csv(fname, skiprows=1,header=None,names=['idx','classid'])
    return cls
    
    
def results(cls):
    """ get the clustered activity patterns
    Parameter: cls - the clustering result dataframe
    Return: actiPatNum - the multiIndex dataframe, indexes include class no. and person id.
    """
    # activity pattern
    actiPattern = activity_pattern()
    actiPatNum = encode(actiPattern,to_='num')
    
    # class
    class_ = sorted(cls.classid.unique())
    cls['pidx'] = actiPatNum.index
    cls.set_index('pidx',inplace=True)
    actiPatNum['c'] = pd.Series(cls.classid)
    actiPatNum = actiPatNum.sort_values('c').reset_index().set_index(['c','PersonID'])  # multi index
    return actiPatNum


# In[3]:


def transition_matrix(group):
    """ 
    """
    link = []
    for idx in group.index.tolist():
        pat = group.loc[idx].values.tolist()
        pre = pat[:-1]
        post = pat[1:]
        l = list(zip(pre,post))
        link += l

    link = pd.DataFrame(link,columns=list('st')).reset_index()
    link = link.groupby(['s','t']).index.count().reset_index()
    mtr = pd.pivot(link,index='s',columns='t',values='index').fillna(0)

    tm = mtr.reindex(index=list('HWSEBDRO'),columns=list('HWSEBDRO')).fillna(0).astype(int)  # transition matrix
    #tm = tm.div(tm.sum(axis=0),axis=0).fillna(0).round(3)*100  # rate
    tm = tm.div(tm.sum().sum()).round(3)*100
    return tm


# In[4]:


cls = cluster(n=3)
class_ = sorted(cls.classid.unique())
data = results(cls)


# In[5]:


ap = encode(data,to_='pat')
print(len(ap.loc[3]),len(ap.loc[1]),len(ap.loc[2]))

# each group activity patterns
group1 = ap.loc[3]
group2 = ap.loc[1]
group3 = ap.loc[2]


# ## style 1

# In[6]:


def plot_transition_matrix(ax,data,title,vmin,vmax,cmap_display=True):
    import seaborn as sns
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    im = ax.imshow(data,cmap="Greens",vmin=vmin,vmax=vmax)

    # Create colorbar
    if cmap_display:
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        fig.colorbar(im, cax=cax)

    cols = ['H','W','S','E','B','D','R','O']
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    ax.set_xticklabels(cols,fontsize=12)
    ax.set_yticklabels(cols,fontsize=12)

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=False, bottom=True,labeltop=False,labelbottom=True)

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
        spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_title(title,fontsize=14)

    textcolors=("black", "white")
    threshold = (vmax + vmin) / 1.5
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            color=textcolors[int(data.iloc[i, j] > threshold)]
            im.axes.text(j, i, round(data.iloc[i, j],1),ha='center', va='center',color=color,fontsize=10)


# In[7]:


tm1 = transition_matrix(group1)
tm2 = transition_matrix(group2)
tm3 = transition_matrix(group3)


# In[8]:


fig,(ax1,ax2,ax3) = plt.subplots(1,3,figsize=(15,5))
plot_transition_matrix(ax=ax1,data=tm1,title='Cluster 1',vmin=0.5,vmax=5,cmap_display=False)
plot_transition_matrix(ax=ax2,data=tm2,title='Cluster 2',vmin=1,vmax=10,cmap_display=False)
plot_transition_matrix(ax=ax3,data=tm3,title='Cluster 3',vmin=1,vmax=6,cmap_display=False)
plt.subplots_adjust(wspace=0.15)
# plt.savefig(fname=r'C:\Users\ZY\Desktop\tm.png',dpi=300,bbox_inches='tight',pad_inches=0)


# ## style 2

# In[9]:


def plot_transition_matrix2(ax,data,title,cmap_display=True):
    import seaborn as sns
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    import matplotlib as mpl
    from matplotlib.colors import ListedColormap
    
    # data
    m = np.array(data)
    diag = np.zeros((8,8))
    non_diag = np.zeros((8,8))
    for i in range(8):
        for j in range(8):
            if i == j:
                diag[i,j] = m[i,j]
                non_diag[i,j] = np.nan
            else:
                diag[i,j] = np.nan
                non_diag[i,j] = m[i,j]
    
    
    # 定制新的colormap
    base_color = mpl.cm.get_cmap('bwr') # blue - white - red
    blue = base_color(np.linspace(0,0.5,100))
    red  = base_color(np.linspace(0.5,1,100))

    cm_blue = ListedColormap(blue[::-1])
    cm_red  = ListedColormap(red)
    
    
    # plot
    ax.imshow(diag,cmap=cm_red,vmin=-3,vmax=100)
    ax.imshow(non_diag,cmap=cm_blue,vmin=-0.1,vmax=2)

    cols = ['H','W','S','E','B','D','R','O']
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    ax.set_xticklabels(cols,fontsize=12)
    ax.set_yticklabels(cols,fontsize=12)

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=False, bottom=True,labeltop=False,labelbottom=True)

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
        spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_title(title,fontsize=14)

    # 添加数字
    textcolors=("black", "white")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if i == j:
                color=textcolors[int(m[i, j] > 50)]
                ax.text(j, i, round(m[i, j],1),ha='center', va='center',color=color,fontsize=10)
            else:
                color=textcolors[int(m[i, j] >= 1)]
                ax.text(j, i, round(m[i, j],1),ha='center', va='center',color=color,fontsize=10)


# In[10]:


fig,(ax1,ax2,ax3) = plt.subplots(1,3,figsize=(15,5))
plot_transition_matrix2(ax=ax1,data=tm1,title='Cluster 1',cmap_display=False)
plot_transition_matrix2(ax=ax2,data=tm2,title='Cluster 2',cmap_display=False)
plot_transition_matrix2(ax=ax3,data=tm3,title='Cluster 3',cmap_display=False)
plt.subplots_adjust(wspace=0.15)
# plt.savefig(fname=r'C:\Users\ZY\Desktop\tm.png',dpi=300,bbox_inches='tight',pad_inches=0)


# In[ ]:




