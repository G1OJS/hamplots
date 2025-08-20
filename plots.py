import matplotlib.pyplot as plt
from matplotlib import cm
import os
import datetime
from collections import Counter

global myBands, myModes, mydxccs

def get_cfg():
    global myBands, myModes, mydxccs
    with open("hamplots.cfg","r") as f:
        lines = f.readlines()
    mydxccs = [e.strip() for e in lines[0].split(",")]
    myBands = [e.strip() for e in lines[1].split(",")]
    myModes = [e.strip() for e in lines[2].split(",")]
    

def get_decodes(RxTx, band, mode, timewin_secs):
    filepath = f"{RxTx}_decodes.csv"
    decodes = []
    with open(filepath, "r") as f:
        for l in f.readlines():
            ls=l.strip().split(", ")
            b,m,rt = ls[1], ls[3], ls[7]
            if( b==band and m==mode and rt==RxTx):                
                d = {'t':int(ls[0]), 'b':b, 'md':m, 'hc':ls[4].replace('-','.'), 'TxRx':rt, 'oc':ls[8].replace('-','.'),'rp':ls[11]}
                decodes.append(d)
    if(decodes):
        tmax = max([d['t'] for d in decodes])
        decodes = [d for d in decodes if d['t']> (tmax - timewin_secs)]
        print(f"Read {len(decodes)} decodes from {filepath}")
        timestr = tmax.strftime("%d/%m/%Y %H:%M UTC")
    return decodes, timestr

def get_plot_data(decodes):
    best = {}
    for d in decodes:
        hc, oc, snr = d["hc"], d["oc"], int(d["rp"])
        key = (hc, oc)
        best[key] = max(snr, best.get(key, -80))
    best_reports = [(hc, oc, snr) for (hc, oc), snr in best.items()]

    hc_cover = Counter(hc for hc, oc, snr in best_reports)
    oc_cover = Counter(oc for hc, oc, snr in best_reports)

    home_calls = sorted({hc for hc, _, _ in best_reports}, key=lambda hc: hc_cover[hc], reverse=True)
    other_calls = sorted({oc for _, oc, _ in best_reports}, key=lambda oc: oc_cover[oc])

    hc_idx = {hc: i for i, hc in enumerate(home_calls)}     # = {'call',i} i=0,1,2,3 ...
    oc_idx = {oc: i for i, oc in enumerate(other_calls)}

    sorted_reports = sorted(best_reports, key=lambda x: (hc_idx[x[0]], oc_idx[x[1]]))

    # arrays ready for plotting
    hc_idxs = [hc_idx[hc] for hc, oc, snr in sorted_reports] # = 0,0,0,0,1,1,1,1,1,2,2,2 ...
    oc_idxs = [oc_idx[oc] for hc, oc, snr in sorted_reports]
    snrs = [snr for hc, oc, snr in sorted_reports]

    return hc_idxs, oc_idxs, snrs, home_calls, other_calls



def do_plots(timewin_start_offset_secs):
    print(f"Starting plots with time window {timewin_start_offset_secs} secs")

    for RxTx in ["Rx","Tx"]:
        for band in myBands:
            for mode in myModes:
                decodes, timestr = get_decodes(RxTx, band, mode, timewin_start_offset_secs)
                fig, ax = plt.subplots(facecolor='grey')
                ax.set_facecolor("#1CC4AF")
                other_action = "Transmitting" if RxTx == "Rx" else "Receiving"
                home_entities = "Receivers'" if RxTx == "Rx" else "Transmitters'"
                ax.set_ylabel(f"{other_action} callsign")
                plt.suptitle(f"Activity {timewin_start_offset_secs/60:.0f} mins to {timestr}")
                ax.set_title(f"{home_entities} SNR on {band} {mode}, to/from dxcc={mydxccs}")
                scatter = ax.scatter(hcs_lst, ocs_lst, c=rpts_lst, cmap='inferno', s=25, alpha = 0.6)

                if(decodes):
                    hcs_lst, ocs_lst, rpts_lst, home_calls, other_calls = get_plot_data(decodes)
                    if(len(home_calls)<400):
                        ax.set_xticks(range(len(home_calls)), home_calls, rotation='vertical', size = 6)
                    if(len(other_calls)<200):
                        ax.set_yticks(range(len(other_calls)), other_calls, size = 6)
                ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
                fig.colorbar(scatter, label='SNR')
                plt.tight_layout()         
                if not os.path.exists("plots"):
                    os.makedirs("plots")
                plt.savefig(f"plots/{RxTx}_{band}_{mode}.png")
                plt.close()

get_cfg()

do_plots(30*60)
