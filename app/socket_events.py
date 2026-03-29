# app/sockets.py
from flask import request
from flask_socketio import disconnect, emit, join_room
from app.extensions import app_socketio
from app.socket_token import verify_socket_token
from database import InsertNewFight, UpdateFight, assignDeviceFightId, assignDeviceSid, getAllTournamentsNames, getTournamentByName, checkDeviceAssignedTournament, getTournamentById, assignDeviceToTournament, Tournaments, getTournamentIdByLicenseKey, getFightById, getCurrentFightByLicenseKey, getDeviceByLicenseKey, getFightByTournamentIdAndId

SOCKET_TOKEN_TTL_SECONDS = 300

@app_socketio.on("connect")
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

@app_socketio.on("select_tournament")
def tournament_data(req):

    tournament_name = req.get("tournament_name")
    license_key = req.get("license_key")
    court = req.get("court_number")

    print(tournament_name, license_key)

    if not tournament_name:
        emit("tournament_data", {"message": "error", "data": {}})
        return
    
    data: Tournaments = getTournamentByName(tournament_name)
    print("Printing from select_tournament")
    print(data)

    if not data:
        emit("tournament_data", {"message": "error", "data": {}})
        return
    
    assignDeviceToTournament(license_key, data.id, court)

    emit("tournament_data", {"message": "ok", "data": data.to_dict()})
    return

@app_socketio.on("confirm_connection")
def confirmConnection(data):
    print("Confirm Selection")

    sid = request.sid
    license_key = data.get("license_key")
    print(sid, license_key)

    tournament_id = assignDeviceSid(sid, license_key)

    join_room(tournament_id)
    print(tournament_id)

    return

@app_socketio.on("new_fight")
def confirmConnection(data):
    row = data["data"]
    license_key = data.get("license_key")

    tournament_id = getTournamentIdByLicenseKey(license_key)

    row["tournament_id"] = tournament_id
    # ak nahodou existuje fight kde su poslane data rovnake pri tournament_id a fight_id -> update fight
    neexistuje_fight = getFightByTournamentIdAndId(int(tournament_id), int(data["id"]))

    if not neexistuje_fight:
        UpdateFight(int(data["id"]), data)
    else:
        status = InsertNewFight(row)
        if not status:
            raise RuntimeError("Error inserting new Fight")
    
    assignDeviceFightId(license_key, row["id"])
    return

@app_socketio.on("start_fight")
def confirmConnection(data):
    license_key = data.get("license_key")

    device_data = getDeviceByLicenseKey(license_key).to_dict()
    fight_data = getFightById(str(device_data["current_fight"]))

    print(device_data, fight_data)
    emit("other_fight_started", {"data": fight_data.to_dict(), "court": device_data["court"]}, room=device_data["tournament_id"])

@app_socketio.on("ping")
def on_ping(data):
    # basic echo
    emit("pong", {"ts": data.get("ts")})

@app_socketio.on("ivr:event")
def on_ivr_event(data):
    # Example of broadcasting to all sockets under the same license_key
    license_key = request.environ.get("license_key")
    if not license_key:
        # disconnect()
        return

    app_socketio.emit("ivr:update", data, room=f"lic:{license_key}")

