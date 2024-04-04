from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
      
        <h1>WebSocket Chat</h1>
        <hr>
        <label for="username"><b>Username:</b></label>
        <input type="text" id="username" autocomplete="off" required/>
        <br>
        <label for="file"><b>Uplad file:</b></label>
        <input type="file" id="file" enctype="multipart/form-data" autocomplete="off"/>
        
        <br>
        
        <button onclick="submitUsername()">Submit</button>
        
        <hr>
        
        
        <form action="" onsubmit="sendMessage(event)">
            <label><b>Messages:</b></label><input type="text" id="messageText" autocomplete="off" required/>
            <button>Send</button>
        </form>
        <hr>
        <ul id='messages'>
        </ul>
    
        <script>
            var file='';
            var username = '';
            
            var ws;

            function submitUsername() {
                username = document.getElementById("username").value;
                file = document.getElementById("file").files[0].name;
                
                

                ws = new WebSocket(`ws://localhost:8000/ws/${username}`);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
            }

            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(`${username}: ${input.value}`)
                
                ws.send(`file:${file}`)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {username} left the chat")