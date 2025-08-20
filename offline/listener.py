
import paho.mqtt.client as mqtt
import ast
import datetime
import time
import pickle

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

def subscribe(client, userdata, flags, reason_code, properties):
    # pskr/filter/v2/{band}/{mode}/{sendercall}/{receivercall}/{senderlocator}/{receiverlocator}/{sendercountry}/{receivercountry}
    print(f"Connected: {reason_code}")
    for sq in mySquares:
        for b in myBands:
            for md in myModes:
                for TxRx in ["Rx","Tx"]:
                    print(f"Subscribe to {TxRx} in {sq} on {b} {md}")
                    tailstr = f"+/+/{sq}/+/+/#" if TxRx == "Tx" else f"+/+/+/{sq}/+/#"
                    client.subscribe(f"pskr/filter/v2/{b}/{md}/{tailstr}")

def dump_decode(client, userdata, msg):
    global decodes
    d = ast.literal_eval(msg.payload.decode())
    d['sl'] = d['sl'].upper()
    if(len(d['sl'])<4):
        return
    d['rl'] = d['rl'].upper()
    TxRx = "Tx" if(d['sl'][0:4] in mySquares) else "Rx"
    d.update({'TxRx':TxRx})
    d.update({'ta':  time.time()})
    d.update({'hc':  d['rc'] if TxRx =="Rx" else d['sc']})
    d.update({'hl':  d['rl'] if TxRx =="Rx" else d['sl']})
    d.update({'ha':  d['ra'] if TxRx =="Rx" else d['sa']})
    d.update({'oc':  d['sc'] if TxRx =="Rx" else d['rc']})
    d.update({'ol':  d['sl'] if TxRx =="Rx" else d['rl']})
    d.update({'oa':  d['sa'] if TxRx =="Rx" else d['ra']})
    with open(f"decodes/{d['sq']}","wb") as f:
        pickle.dump(d,f)

get_cfg()
mqtt_cl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_cl.on_connect = subscribe
mqtt_cl.on_message = dump_decode
mqtt_cl.connect("mqtt.pskreporter.info", 1883, 60)

mqtt_cl.loop_forever()







