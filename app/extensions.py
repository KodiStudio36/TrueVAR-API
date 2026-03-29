from flask_socketio import SocketIO

app_socketio = SocketIO(
    cors_allowed_origins="*",  # tighten in production
    async_mode="threading",     # simplest; you can switch later
)