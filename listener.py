
import paho.mqtt.client as mqtt
import ast
import datetime
import time

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

def sub_listen_dump(self, client, userdata, flags, reason_code, properties):
    # pskr/filter/v2/{band}/{mode}/{sendercall}/{receivercall}/{senderlocator}/{receiverlocator}/{sendercountry}/{receivercountry}
    print(f"Connected: {reason_code}")
    for sq in self.squares:
        for b in self.bands:
            for md in self.modes:
                for TxRx in ["Rx","Tx"]:
                    print(f"Subscribe to {TxRx} in {sq} on {b} {md}")
                    tailstr = f"+/+/{sq}/+/+/#" if TxRx == "Tx" else f"+/+/+/{sq}/+/#"
                    client.subscribe(f"pskr/filter/v2/{b}/{md}/{tailstr}")
                  
    mqtt_cl.loop_start()
    sleep(time_seconds)
    mqtt_cl.loop_stop()
    mqtt_cl.disconnect()

    with open("Decodes.csv", 'a') as f:
        for d in decodes:
            ebfm = f"{d['t']}, {d['b']}, {d['f']}, {d['md']}, "
            spot = f"{d['hc']}, {d['hl']}, {d['ha']}, {d['TxRx']}, {d['oc']}, {d['ol']}, {d['oa']}, {d['rp']}\n"
            f.write(ebfm+spot)
            f.flush()
        self.decodes = []

def add_decode(self, client, userdata, msg):
    d = ast.literal_eval(msg.payload.decode())
    d['sl'] = d['sl'].upper()
    d['rl'] = d['rl'].upper()
    if(d['sl'] in mySquares) TxRx = "Tx" else "Rx"
    d.update({'TxRx':TxRx})
    d.update({'hc':  d['rc'] if TxRx =="Rx" else d['sc']})
    d.update({'hl':  d['rl'] if TxRx =="Rx" else d['sl']})
    d.update({'ha':  d['ra'] if TxRx =="Rx" else d['sa']})
    d.update({'oc':  d['sc'] if TxRx =="Rx" else d['rc']})
    d.update({'ol':  d['sl'] if TxRx =="Rx" else d['rl']})
    d.update({'oa':  d['sa'] if TxRx =="Rx" else d['ra']})
    self.decodes.append(d)

get_cfg()
mqtt_cl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id = f"subscribe-{self.TxRx}")
mqtt_cl.on_connect = sub_listen_dump
mqtt_cl.on_message = add_decode
mqtt_cl.connect("mqtt.pskreporter.info", 1883, 60)


