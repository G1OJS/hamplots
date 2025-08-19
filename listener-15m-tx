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

class pskr_listener:
    def __init__(self, TxRx):
        self.decodes = []
        self.squares = mySquares
        self.bands = myBands
        self.modes = myModes
        self.TxRx = TxRx
        self.mqtt_cl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id = f"subscribe-{self.TxRx}")
        self.mqtt_cl.on_connect = self.subscribe
        self.mqtt_cl.on_message = self.add_decode
        self.mqtt_cl.connect("mqtt.pskreporter.info", 1883, 60)
      
    def loop_and_dump(self, time_seconds):
        self.mqtt_cl.loop_start()
        time.sleep(time_seconds)
        self.mqtt_cl.loop_stop()
        self.mqtt_cl.disconnect()

        with open("Tx_decodes.csv", 'a') as f:
            for d in self.decodes:
                ebfm = f"{d['t']}, {d['b']}, {d['f']}, {d['md']}, "
                spot = f"{d['hc']}, {d['hl']}, {d['ha']}, {d['TxRx']}, {d['oc']}, {d['ol']}, {d['oa']}, {d['rp']}\n"
                f.write(ebfm+spot)
                f.flush()
            self.decodes = []

    def subscribe(self, client, userdata, flags, reason_code, properties):
        # pskr/filter/v2/{band}/{mode}/{sendercall}/{receivercall}/{senderlocator}/{receiverlocator}/{sendercountry}/{receivercountry}
        print(f"Connected: {reason_code}")
        for sq in self.squares:
            for b in self.bands:
                for md in self.modes:
                    print(f"Subscribe to {self.TxRx} in {sq} on {b} {md}")
                    tailstr = f"+/+/{sq}/+/+/#" if self.TxRx == "Tx" else f"+/+/+/{sq}/+/#"
                    client.subscribe(f"pskr/filter/v2/{b}/{md}/{tailstr}")

    def add_decode(self, client, userdata, msg):
        d = ast.literal_eval(msg.payload.decode())
        d['sl'] = d['sl'].upper()
        d['rl'] = d['rl'].upper()
        d.update({'TxRx':self.TxRx})
        d.update({'hc':  d['rc'] if self.TxRx =="Rx" else d['sc']})
        d.update({'hl':  d['rl'] if self.TxRx =="Rx" else d['sl']})
        d.update({'ha':  d['ra'] if self.TxRx =="Rx" else d['sa']})
        d.update({'oc':  d['sc'] if self.TxRx =="Rx" else d['rc']})
        d.update({'ol':  d['sl'] if self.TxRx =="Rx" else d['rl']})
        d.update({'oa':  d['sa'] if self.TxRx =="Rx" else d['ra']})
        self.decodes.append(d)

get_cfg()
tx = pskr_listener("Tx")

tx.loop_and_dump(5*60)
