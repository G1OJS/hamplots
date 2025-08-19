
import paho.mqtt.client as mqtt
import ast
import datetime
import time

global myBands, myModes, mySquares, decodes

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

def subscribe(client, userdata, flags, reason_code, properties):
    global decodes
    # pskr/filter/v2/{band}/{mode}/{sendercall}/{receivercall}/{senderlocator}/{receiverlocator}/{sendercountry}/{receivercountry}
    print(f"Connected: {reason_code}")
    for sq in mySquares:
        for b in myBands:
            for md in myModes:
                for TxRx in ["Rx","Tx"]:
                    print(f"Subscribe to {TxRx} in {sq} on {b} {md}")
                    tailstr = f"+/+/{sq}/+/+/#" if TxRx == "Tx" else f"+/+/+/{sq}/+/#"
                    client.subscribe(f"pskr/filter/v2/{b}/{md}/{tailstr}")

def add_decode(client, userdata, msg):
    global decodes
    d = ast.literal_eval(msg.payload.decode())
    d['sl'] = d['sl'].upper()
    d['rl'] = d['rl'].upper()
    TxRx = "Tx" if(d['sl'] in mySquares) else "Rx"
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

time_seconds = 30
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




