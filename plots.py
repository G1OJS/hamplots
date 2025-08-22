import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.colors as mcolors
import os
import time
from collections import Counter
from collections import defaultdict
import subprocess

global myBands, myModes, mydxccs

def get_cfg():
    global myBands, myModes, mydxccs
    with open("hamplots.cfg","r") as f:
        lines = f.readlines()
    mydxccs = [e.strip() for e in lines[0].split(",")]
    myBands = [e.strip() for e in lines[1].split(",")]
    myModes = [e.strip() for e in lines[2].split(",")]
    

def get_decodes(RxTx, band, mode, decodes_file, timewin_secs):
    filepath = f"{RxTx}_{decodes_file}"
    decodes = []
    timestr = ""
    with open(filepath, "r") as f:
        for l in f.readlines():
            ls=l.strip().split(", ")
            b,m,rt = ls[1], ls[3], ls[7]
            if( b==band and m==mode):
                d = {'t':int(ls[0]), 'b':b, 'md':m, 'hc':ls[4].replace('-','.'), 'oc':ls[8].replace('-','.'),'rp':ls[11]}
                decodes.append(d)
    if(decodes):
        tmax = max([d['t'] for d in decodes])
        decodes = [d for d in decodes if d['t']> (tmax - timewin_secs)]
        print(f"Read {len(decodes)} decodes from {filepath}")
        timestr = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(tmax))
    return decodes, timestr

def get_plot_data(decodes):
    best = {}
    for d in decodes:
        hc, oc, snr = d["hc"], d["oc"], int(d["rp"])
        key = (hc, oc)
        best[key] = max(snr, best.get(key, -80))
    # best snr for each hc-oc pair over time window
    best_reports = [(hc, oc, snr) for (hc, oc), snr in best.items()]

    # home calls' coverage of other calls
    hc_cover = Counter(hc for hc, oc, snr in best_reports)
    # other calls' coverage of home calls
    oc_cover = Counter(oc for hc, oc, snr in best_reports)


    # rarity-weighted score for each home call
#    hc_score = defaultdict(float)
#    for hc, oc, snr in best_reports:
#        hc_score[hc] += 1 / oc_cover[oc]
    # sort home calls by rarity-weighted score
#    home_calls = sorted(hc_score, key=lambda hc: hc_score[hc], reverse=True)

    # sort home calls by number of other calls covered
    home_calls = sorted({hc for hc, _, _ in best_reports}, key=lambda hc: hc_cover[hc], reverse=True)


    # sort other calls by number of home calls covered
    other_calls = sorted({oc for _, oc, _ in best_reports}, key=lambda oc: oc_cover[oc])

    # regenerate [(hc, oc, snr)] respecting the ordering of hc and oc calculated above
    hc_idx = {hc: i for i, hc in enumerate(home_calls)}     # = {'call',i} i=0,1,2,3 ...
    oc_idx = {oc: i for i, oc in enumerate(other_calls)}
    sorted_reports = sorted(best_reports, key=lambda x: (hc_idx[x[0]], oc_idx[x[1]]))

    # arrays ready for plotting
    hc_idxs = [hc_idx[hc] for hc, oc, snr in sorted_reports] # = 0,0,0,0,1,1,1,1,1,2,2,2 ...
    oc_idxs = [oc_idx[oc] for hc, oc, snr in sorted_reports]
    snrs = [snr for hc, oc, snr in sorted_reports]

    return hc_idxs, oc_idxs, snrs, home_calls, other_calls

def git_upload():
    repo_dir = r"C:\Users\drala\Documents\Projects\GitHub\hamplots"
    subprocess.run(["git", "add", "-f", "./plots/*.png"], cwd=repo_dir)
    subprocess.run(["git", "commit", "-m", "upload local data"], cwd=repo_dir)
    subprocess.run(["git", "pull", "--rebase"], cwd=repo_dir)
    subprocess.run(["git", "push", "-f"], cwd=repo_dir)

def do_plots(decodes_file = "decodes_local.csv", timewin_start_offset_secs = 30*60):
    get_cfg()
    print(f"Starting plots with time window {timewin_start_offset_secs} secs")
    for RxTx in ["Rx","Tx"]:
        for band in myBands:
            for mode in myModes:
                decodes, timestr = get_decodes(RxTx, band, mode, decodes_file, timewin_start_offset_secs)
                fig, axs = plt.subplots(2, 1, gridspec_kw={'height_ratios': [5, 1]})
                ax, axtext = axs[0], axs[1]
                axtext.set_axis_off()
                ax.set_ylabel(f"{'Transmitting' if RxTx == 'Rx' else 'Receiving'} callsign")
                plt.suptitle(f"SNR for {'receivers' if RxTx == 'Rx' else 'Transmitters'} in dxcc={','.join(mydxccs)} on {band} {mode}")
                
                fig.patch.set_alpha(0.4)
                ax.patch.set_alpha(0.4)
                if(decodes):
                    hcs_idxs, ocs_idxs, rpts_lst, home_calls, other_calls = get_plot_data(decodes)
                    if(len(home_calls)<75):
                        ax.set_xticks(range(len(home_calls)), home_calls, rotation='vertical', size = 6)
                    if(len(other_calls)<75):
                        ax.set_yticks(range(len(other_calls)), other_calls, size = 6)
                    rpts_lst = [min(max(r,-20),20) for r in rpts_lst]
                    scatter = ax.scatter(hcs_idxs, ocs_idxs, c=rpts_lst, cmap='inferno', s=25, alpha = 0.6)
                    fig.colorbar(scatter, label='SNR')
                    
                    axtext.text(0,1.4,f"Chart shows activity for {timewin_start_offset_secs/60:.0f} mins to {timestr} UTC", horizontalalignment='left', fontsize=10)
                    txt =  f"Home callsigns sorted left-right by number of other callsigns {'reached' if RxTx=='Tx' else 'heard'}"
                    txt += f"\nCallsigns sorted top-bottom by number of home callsigns {'reached' if RxTx=='Rx' else 'heard'}"
                    txt += f"\nNumber of active home callsigns: {len(home_calls)}"
                    txt += f"\nTop 10 home callsigns by number of callsigns {'reached' if RxTx=='Tx' else 'heard'}:"
                    txt += f"\n{', '.join(home_calls[0:10])}"
                    axtext.text(0.02,0.3,txt, horizontalalignment = 'left', fontsize=7)
                    
                ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
                plt.tight_layout()         
                if not os.path.exists("plots"):
                    os.makedirs("plots")
                print(f"Saving plot plots/{RxTx}_{band}_{mode}.png")
                plt.savefig(f"plots/{RxTx}_{band}_{mode}.png")
                plt.close()

if os.path.exists("local_token"):
    print("Running local")
    do_plots(decodes_file = "decodes_local.csv", timewin_start_offset_secs = 30*60)
    git_upload()
else:
    print("Running remote")
    do_plots(decodes_file = "decodes.csv", timewin_start_offset_secs = 30*60)

