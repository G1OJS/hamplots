import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import pandas as pd

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

def tabulate_reports(remote_calls, homecall_reports):
    # flatten nested dict
    records = []
    for hc, rc_dict in homecall_reports.items():
        for rc, rplist in rc_dict.items():
            for rp in rplist:
                records.append((rc, hc, int(rp)))

    df = pd.DataFrame(records, columns=["remote", "home", "report"])
    # pivot to table of max report for each home callsign
    pivot = df.groupby(["remote", "home"])["report"].max().unstack(fill_value=-30)
    pivot = pivot.reindex(index=remote_calls, columns=homecall_reports.keys(), fill_value=-30)

    return pivot.index.tolist(), pivot.columns.tolist(), pivot.values.tolist()

def build_connectivity_info(decodes, start_epoch = 0, bands = "20m", modes = "FT8"):
    """
        returns:
         calls[callsign] = nSpots
         spots[homecall] = [reports]
    """
    remote_calls = {}
    homecall_reports = {}

    for d in decodes:
        if(int(d['t']) < start_epoch or d['b'] not in bands or d['md'] not in modes):
            continue
        homecall_reports.setdefault(d['hc'],{})
        homecall_reports[d['hc']].setdefault(d['oc'],[]).append(d['rp'])
        remote_calls.setdefault(d['oc'],0)
        remote_calls[d['oc']] += 1
    return remote_calls, homecall_reports

def cover_home_calls(calls, spots):
    """
    calls: dict {remote_call: count_of_reports}
    spots: dict {home_call: {remote_call: [reports...]}}
    
    Returns: list of remote calls needed to cover all home calls,
             or False if impossible.
    """
    # sort remotes by number of reports (descending)
    sorted_calls = sorted(calls, key=calls.get, reverse=True)
    
    # set of home calls that still need coverage
    uncovered = set(spots.keys())
    needed = []
    
    for rc in sorted_calls:
        # check which home calls this remote covers
        covers = {hc for hc, rcs in spots.items() if rc in rcs}
        if not covers:
            continue
        needed.append(rc)
        uncovered -= covers
        if not uncovered:  # all home calls covered
            return needed
    
    return False  # some home calls never got covered

def read_csv(filepath =  "decodes.csv", start_epoch = 0):
    if (not os.path.isfile(filepath)):
        return False
    
    decodes = []
    with open(filepath, "r") as f:
        for l in f.readlines():
            if('\x00' in l):
                continue
            ls=l.strip().split(", ")
            if(len(ls) == 12):
                d = {'t':ls[0], 'b':ls[1], 'f':ls[2], 'md':ls[3], 'hc':ls[4], 'hl':ls[5], 'ha':ls[6], 'TxRx':ls[7], 'oc':ls[8], 'ol':ls[9], 'oa':ls[10], 'rp':ls[11]}
                if(int(d['t']) < start_epoch):
                    continue
                decodes.append(d)
            
    print(f"Read {len(decodes)} decodes from {filepath}")
    return decodes

def git_upload():
    repo_dir = r"C:\Users\drala\Documents\Projects\GitHub\hamplots"
    subprocess.run(["hamplots", "do_plots", "--plotwinsecs", str(plotwinsecs)], cwd = repo_dir)
    subprocess.run(["git", "add", "-f", "./plots/*.png"], cwd=repo_dir)
    subprocess.run(["git", "add", "-f", "./plots/timestamp"], cwd=repo_dir)
    subprocess.run(["git", "commit", "-m", "upload local data"], cwd=repo_dir)
    subprocess.run(["git", "pull"], cwd=repo_dir)
    subprocess.run(["git", "clean", "-f"], cwd=repo_dir)
    subprocess.run(["git", "push", "-f"], cwd=repo_dir)
    subprocess.run(["git", "clean", "-f"], cwd=repo_dir)

def do_plots(timewin_start_offset_secs):
    print(f"Starting plots with time window {timewin_start_offset_secs} secs")

    for RxTx in ["Rx","Tx"]:
        decodes = read_csv(f"{RxTx}_decodes.csv")
        if(not decodes):
            continue

        timewin_start = time.time() - timewin_start_offset_secs
        for band in myBands:
            for mode in myModes:
                print(f"Rx_{band}_{mode}")

                remote_calls, homecall_reports = build_connectivity_info(decodes, start_epoch = timewin_start, bands=band, modes=mode)
                remote_calls = cover_home_calls(remote_calls, homecall_reports)

                # plot setup
                timestr = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                fig, axs = plt.subplots()
                remote_action = "Transmitting" if RxTx == "Rx" else "Receiving"
                home_entities = "Receivers'" if RxTx == "Rx" else "Transmitters'"
                axs.set_ylabel(f"{remote_action} callsign")
                plt.suptitle(f"Activity over last {timewin_start_offset_secs/60:.0f} minutes\n to/from {mySquares}")
                axs.set_title(f"{home_entities} SNR on {band} {mode}, to {timestr}")
                
                if remote_calls:
                    rowheads, colheads, cells = tabulate_reports(remote_calls, homecall_reports)
                    print(f" ... analysing {len(rowheads)} by {len(colheads)}")
                    
                    # build DataFrame
                    import pandas as pd
                    cells = pd.DataFrame(cells, index=rowheads, columns=colheads)
                    
                    # sort criteria
                    nRemotes_in_row = cells.replace(-30, np.nan).count(axis=1)
                    nRemotes_in_column = cells.replace(-30, np.nan).count(axis=0)
                   # mean_snr_in_column = cells.mean(axis=0)

                    # do sort
                    cells = cells.loc[nRemotes_in_row.sort_values(ascending=True).index,
                                    nRemotes_in_column.sort_values(ascending=False).index]
                    cells = cells.replace(-30, -70)
                
                    my_pcolor(axs,fig, rowheads, colheads, cells)

                plt.tight_layout()         
                if not os.path.exists("plots"):
                    os.makedirs("plots")
                plt.savefig(f"plots/{RxTx}_{band}_{mode}.png")
                plt.close()

get_cfg()
do_plots(30*60)
