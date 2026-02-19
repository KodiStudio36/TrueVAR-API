# app/sockets.py
from flask import request
from flask_socketio import disconnect, emit, join_room
from app import socketio
from app.socket_token import verify_socket_token
from database import getAllTournamentsNames, getTournamentByName, checkDeviceAssignedTournament, getTournamentById, assignDeviceToTournament, Tournaments

SOCKET_TOKEN_TTL_SECONDS = 300

@socketio.on("connect")
def on_connect(auth):
    """
    Client should pass token via:
      io("https://host", { auth: { token: "..." } })
    """
    token = None
    if isinstance(auth, dict):
        token = auth.get("token")

    if not token:
        return False  # reject connection

    try:
        payload = verify_socket_token(token, max_age_seconds=SOCKET_TOKEN_TTL_SECONDS)
    except Exception:
        return False  # reject connection

    # At this point the socket is authenticated
    license_key = payload["license_key"]
    machine_id = payload["machine_id"]

    tournament_id = checkDeviceAssignedTournament(license_key=license_key)
    print(tournament_id)
    
    if tournament_id:
        data = getTournamentById(tournament_id).to_dict()
        print(data)
        emit("tournament_data", {"message": "ok", "data": data})
        return

    # You can put them into the socket session (per-connection context)
    # request.environ["license_key"] = license_key
    # request.environ["machine_id"] = machine_id

    # Optional: group sockets by license key
    # join_room(f"lic:{license_key}")

    all_tournaments = getAllTournamentsNames()
    print("Success conn")
    emit("tournaments_list", {
        "message" : "ok",
        "license_key": license_key,
        "tournaments": all_tournaments
        })

@socketio.on("select_tournament")
def tournament_data(req):

    tournament_name = req.get("tournament_name")
    license_key = req.get("license_key")

    print(tournament_name, license_key)

    if not tournament_name:
        return 400
    
    data: Tournaments = getTournamentByName(tournament_name)
    print(data)

    if not data:
        emit("tournament_data", {"message": "ok", "data": {}})
        return
    
    assignDeviceToTournament(license_key, data.id)

    emit("tournament_data", {"message": "ok", "data": data.to_dict()})
    return


@socketio.on("ping")
def on_ping(data):
    # basic echo
    emit("pong", {"ts": data.get("ts")})

@socketio.on("ivr:event")
def on_ivr_event(data):
    # Example of broadcasting to all sockets under the same license_key
    license_key = request.environ.get("license_key")
    if not license_key:
        disconnect()
        return

    socketio.emit("ivr:update", data, room=f"lic:{license_key}")
