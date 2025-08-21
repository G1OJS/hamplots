import paho.mqtt.client as mqtt
import ast
import datetime
import time
import os

global myBands, myModes, mydxccs, ftx, frx

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
    global ftx, frx
    d = ast.literal_eval(msg.payload.decode())
    d['sl'] = d['sl'].upper()
    if(len(d['sl'])<4):
        return
    d['rl'] = d['rl'].upper()
    ebfm = f"{d['t']}, {d['b']}, {d['f']}, {d['md']}, "
    if(d['ra'] in mydxccs):
        spot = f"{d['rc']}, {d['rl']}, {d['ra']}, 'Rx', {d['sc']}, {d['sl']}, {d['sa']}, {d['rp']}\n"
        frx.write(ebfm+spot)
        frx.flush()
    if(d['sa'] in mydxccs):
        spot = f"{d['sc']}, {d['sl']}, {d['sa']}, 'Tx', {d['rc']}, {d['rl']}, {d['ra']}, {d['rp']}\n"
        ftx.write(ebfm+spot)
        ftx.flush()

def run(decodes_file = "decodes_local.csv", time_seconds = 0):
    global ftx, frx
    get_cfg()
    frx = open(f"Rx_{decodes_file}","a")
    ftx = open(f"Tx_{decodes_file}","a")
    mqtt_cl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_cl.on_connect = subscribe
    mqtt_cl.on_message = add_decode
    mqtt_cl.connect("mqtt.pskreporter.info", 1883, 60)
    if(time_seconds == 0):
        mqtt_cl.loop_forever()
    else:
        mqtt_cl.loop_start()
        time.sleep(time_seconds)
        mqtt_cl.loop_stop()
        mqtt_cl.disconnect()

if os.path.exists("local_token"):
    run()
else:
    run(decodes_file = "decodes.csv", time_seconds = 5*60)


