
import paho.mqtt.client as mqtt
import ast
import datetime
import time

global myBands, myModes, mydxccs, decodes

def get_cfg():
    global myBands, myModes, mydxccs
    with open("hamplots.cfg","r") as f:
        lines = f.readlines()
    mydxccs = [int(e.strip()) for e in lines[0].split(",")]
    myBands = [e.strip() for e in lines[1].split(",")]
    myModes = [e.strip() for e in lines[2].split(",")]
    print(f"mydxccs {mydxccs}")
    print(f"myBands {myBands}")
    print(f"myModes {myModes}")

def subscribe(client, userdata, flags, reason_code, properties):
    # pskr/filter/v2/{band}/{mode}/{sendercall}/{receivercall}/{senderlocator}/{receiverlocator}/{sendercountry}/{receivercountry}
    print(f"Connected: {reason_code}")
    for dxcc in mydxccs:
        for b in myBands:
            for md in myModes:
                for TxRx in ["Rx","Tx"]:
                    print(f"Subscribe to {TxRx} in {dxcc} on {b} {md}")
                    tailstr = f"+/+/+/+/{dxcc}/#" if TxRx == "Tx" else f"+/+/+/+/+/{dxcc}"
                    subs = f"pskr/filter/v2/{b}/{md}/{tailstr}"
                    print(subs)
                    client.subscribe(subs)

def add_decode(client, userdata, msg):
    global decodes
    d = ast.literal_eval(msg.payload.decode())
    d['sl'] = d['sl'].upper()
    if(len(d['sl'])<4):
        return
    d['rl'] = d['rl'].upper()
    TxRx=False
    if(d['sa'] in mydxccs):
        TxRx = "Tx"
    if(d['ra'] in mydxccs):
        TxRx = "Rx"
    if(TxRx):
        d.update({'TxRx':TxRx})
        d.update({'hc':  d['rc'] if TxRx =="Rx" else d['sc']})
        d.update({'hl':  d['rl'] if TxRx =="Rx" else d['sl']})
        d.update({'ha':  d['ra'] if TxRx =="Rx" else d['sa']})
        d.update({'oc':  d['sc'] if TxRx =="Rx" else d['rc']})
        d.update({'ol':  d['sl'] if TxRx =="Rx" else d['rl']})
        d.update({'oa':  d['sa'] if TxRx =="Rx" else d['ra']})
        decodes.append(d)

decodes = []
get_cfg()
mqtt_cl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_cl.on_connect = subscribe
mqtt_cl.on_message = add_decode
mqtt_cl.connect("mqtt.pskreporter.info", 1883, 60)

time_seconds = 60*5
mqtt_cl.loop_start()
time.sleep(time_seconds)
mqtt_cl.loop_stop()
mqtt_cl.disconnect()

frx = open("Rx_decodes.csv","a")
ftx = open("Tx_decodes.csv","a")
for d in decodes:
    ebfm = f"{d['t']}, {d['b']}, {d['f']}, {d['md']}, "
    spot = f"{d['hc']}, {d['hl']}, {d['ha']}, {d['TxRx']}, {d['oc']}, {d['ol']}, {d['oa']}, {d['rp']}\n"
    f = ftx if d['TxRx'] == "Tx" else frx
    f.write(ebfm+spot)
f.flush()




