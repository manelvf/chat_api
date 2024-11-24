""" App main entrypoint """
from storage import (
    add_user,
    get_user_from_session,
    get_user_by_username,
    login_user,
    save_message,
    InvalidUsernamePasswordError
)
from connection_manager import ConnectionManager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.responses import HTMLResponse


# FastAPI application
app = FastAPI()


# initialize websocket connection manager
manager = ConnectionManager()

# read test html template
def read_html():
    with open("client.html") as f:
        return f.read()

html = read_html()


@app.get("/")
async def get():
    """Serve the test HTML page."""
    return HTMLResponse(html)


@app.post("/register")
async def register_user(username: str, password: str):
    """Register a new user."""
    if get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already exists")

    add_user(username, password)

    return {"msg": "User registered successfully"}


@app.post("/login")
async def login(username: str, password: str, response: Response):
    """Authenticate user and create a session."""
    try:
        session_id = login_user(username, password)
    except InvalidUsernamePasswordError:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Set session ID in an HTTP-only cookie
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    return {"msg": "Login successful"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with session-based authentication."""
    # Retrieve session ID from cookies
    session_id = websocket.cookies.get("session_id")
    user = get_user_from_session(session_id) if session_id else None
    username = user.username if user else "Anonymous"

    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            save_message(data, user)

            # Broadcast message to all clients
            await manager.broadcast(f"{username} says: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{username} has disconnected.")
