from fastapi import FastAPI

app = FastAPI()

# Store your latest messages here
latest_messages = {}

@app.on_event("startup")
async def startup_event():
    # Here you can start your MQTT client in a background thread or asyncio task
    # Example placeholder:
    import threading, time
    def dummy_mqtt_loop():
        while True:
            latest_messages["dummy"] = "Hello MQTT"
            time.sleep(10)
    threading.Thread(target=dummy_mqtt_loop, daemon=True).start()

@app.get("/")
def hello():
    return {"status": "ok", "message": "Hello from Fly.io"}

@app.get("/data.json")
def get_data():
    return latest_messages
