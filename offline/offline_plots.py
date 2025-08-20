import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import pandas as pd
import pickle

import os.path
import time
import os
import datetime
import subprocess

global myBands, myModes, mySquares

def get_cfg():
    global myBands, myModes, mySquares
    with open("hamplots.cfg","r") as f:
        lines = f.readlines()
    mySquares = [e.strip() for e in lines[0].split(",")]
    myBands = [e.strip() for e in lines[1].split(",")]
    myModes = [e.strip() for e in lines[2].split(",")]
    print(f"mySquares {mySquares}")
    print(f"myBands {myBands}")
    print(f"myModes {myModes}")

def my_pcolor(ax, fig, rowheads, colheads, cells):
    nx=len(colheads)
    ny=len(rowheads)
    x = np.arange(0.5,nx+0.5)
    y = np.arange(0.5,ny+0.5)
    xfs = max(4,min(12,0.7*72*fig.get_figwidth() / nx))
    ax.set_xticks(x, labels=colheads, rotation="vertical", fontsize = xfs)
    yfs = max(4,min(12,0.7*72*fig.get_figheight() / ny))
    ax.set_yticks(y, labels=rowheads, rotation="horizontal", fontsize = yfs)
    ax.pcolor(cells)
    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)


def do_plots(timewin_start_offset_secs):
    timestr = datetime.datetime.now().strftime("%d/%m/%Y %H:%M UTC")
    fig, axs = plt.subplots()


    ta=[]
    t=[]
    for file in os.listdir("decodes"):
        with open(f"decodes/{file}","rb") as f:
            d = pickle.load(f)
        t.append(int(d['t']))
        ta.append(int(d['ta']))

    s = np.array(t)
    s=s - max(s)+60
    sa = np.array(ta)
    sa=sa - max(sa)+60
    
    plt.hist(s, range(60), color = "red")
    plt.hist(sa, range(60), color = "green", alpha =0.5)


    plt.tight_layout()         

    plt.show()

get_cfg()
do_plots(30*60)
