from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import json
import logging
import queue
import os
import sys

app = FastAPI()

# Para comunicar el estado del proceso de fondo al frontend
clients = set()
# Cola para enviar comandos desde el UI al proceso de fondo (ej: test_mic)
ui_commands = asyncio.Queue()
# Cola thread-safe para recibir actualizaciones del proceso de fondo (ej: niveles de audio)
ui_updates = queue.Queue()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("command"):
                    await ui_commands.put(msg)
            except Exception:
                pass
    except WebSocketDisconnect:
        clients.remove(websocket)

async def update_broadcaster():
    """Lee de la cola ui_updates y envía a los WebSockets."""
    while True:
        try:
            # No bloqueamos el loop de asyncio
            status_obj = ui_updates.get_nowait()
            if clients:
                message = json.dumps(status_obj)
                for client in clients:
                    try:
                        await client.send_text(message)
                    except Exception:
                        pass
        except queue.Empty:
            await asyncio.sleep(0.05) # Pequeña pausa
        except Exception as e:
            print(f"Error in broadcaster: {e}")
            await asyncio.sleep(0.5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_broadcaster())

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Servir el frontend
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

static_dir = get_resource_path(os.path.join("app", "static"))
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def start_server(port: int = 8000):
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")

if __name__ == "__main__":
    start_server()
