import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

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


def get_decodes(RxTx, band, mode):
    filepath = f"{RxTx}_decodes.csv"
    if (not os.path.isfile(filepath)):
        return False
    
    decodes = []
    with open(filepath, "r") as f:
        for l in f.readlines():
            if('\x00' in l):
                continue
            ls=l.strip().split(", ")
            if(len(ls) == 12):
                b,m,rt = ls[1], ls[3], ls[7]
                if( b==band and m==mode and rt==RxTx):                
                    d = {'t':ls[0], 'b':b, 'f':ls[2], 'md':m, 'hc':ls[4].replace('-','.'), 'hl':ls[5], 'ha':ls[6], 'TxRx':rt, 'oc':ls[8].replace('-','.'), 'ol':ls[9], 'oa':ls[10], 'rp':ls[11]}
                    decodes.append(d)
            
    print(f"Read {len(decodes)} decodes from {filepath}")
    return decodes

def window_decodes(decodes, timewin_secs):
    decodes2 =  []
    tmax = 0
    for d in decodes:
        t = int(d['t'])
        if(t>tmax):
            tmax=t
    cutoff = tmax - timewin_secs
    for d in decodes:
        t = int(d['t'])
        if (t>=cutoff):
            decodes2.append(d)
    return decodes2

def get_calls(decodes):
    hc = set()
    oc = set()
    for d in decodes:
        hc.add(d['hc'])
        oc.add(d['oc'])
    return list(hc),list(oc)

def get_best_reports(home_calls, other_calls, decodes):
    rpts = {}
    for hc in home_calls:
        for d in decodes:
            if (d['hc']==hc):
                call_pair = f"{hc}-{d['oc']}"
                rpts.setdefault(call_pair, -80)
                rpts[call_pair] = int(d['rp']) if int(d['rp']) > rpts[call_pair]  else rpts[call_pair]
    return rpts

def get_heatmap_list(decodes):
    home_calls, other_calls = get_calls(decodes)
    best_reports_dict = get_best_reports(home_calls, other_calls, decodes)
    best_reports_dict_sorted = {k:v for k, v in sorted(best_reports_dict.items(), key=lambda item: item[1], reverse=True)}
    home_calls_sorted = [  home_calls [ home_calls.index(rp.split("-")[0]) ] for rp in best_reports_dict_sorted]
    other_calls_sorted = [  other_calls  [ other_calls.index(rp.split("-")[1]) ] for rp in best_reports_dict_sorted]
    best_reports_sorted = [v for k,v in best_reports_dict_sorted.items()]

    return home_calls_sorted, other_calls_sorted, best_reports_sorted

def list_print(xvals, yvals, zvals):
    i=0
    for x in xvals:
        print(x, yvals[i], zvals[i])
        i+=1


def snr_size(snr):
    size = [(snr+30)/5 for s in snr]

def do_plots(timewin_start_offset_secs):
    print(f"Starting plots with time window {timewin_start_offset_secs} secs")

    for RxTx in ["Rx","Tx"]:
        for band in myBands:
            for mode in myModes:
                decodes = get_decodes(RxTx, band, mode)
                decodes = window_decodes(decodes, timewin_start_offset_secs)
                timestr = datetime.datetime.now().strftime("%d/%m/%Y %H:%M UTC")
                fig, axs = plt.subplots()
                other_action = "Transmitting" if RxTx == "Rx" else "Receiving"
                home_entities = "Receivers'" if RxTx == "Rx" else "Transmitters'"
                axs.set_ylabel(f"{other_action} callsign")
                plt.suptitle(f"Activity over last {timewin_start_offset_secs/60:.0f} minutes\n to/from {mySquares}")
                axs.set_title(f"{home_entities} SNR on {band} {mode}, to {timestr}")
                home_calls_sorted, other_calls_sorted, best_reports_sorted = get_heatmap_list(decodes)
   
                axs.scatter(home_calls_sorted, other_calls_sorted, [(rp+30)/5 for rp in best_reports_sorted])

                plt.tight_layout()         
                if not os.path.exists("plots"):
                    os.makedirs("plots")
                plt.savefig(f"plots/{RxTx}_{band}_{mode}.png")
                plt.close()

get_cfg()

do_plots(30*60)
