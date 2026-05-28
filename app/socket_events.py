# app/sockets.py
from flask import json, request
from flask_socketio import disconnect, emit, join_room
from app.extensions import app_socketio
from app.socket_token import verify_socket_token
from database import InsertNewFight, UpdateFight, assignDeviceFightId, assignDeviceSid, clearDeviceCourtTournamentIdSidState, getAllTournamentsNames, getMachineIdBySid, getTournamentByName, checkDeviceAssignedTournament, getTournamentById, assignDeviceToTournament, Tournaments, getTournamentIdByLicenseKey, getFightById, getCurrentFightByLicenseKey, getDeviceByLicenseKey, getFightByTournamentIdAndId, getStreamKeyByTournamentIdAnCourt, setMachineStatus
from database import getTournamentsByDate
import datetime

SOCKET_TOKEN_TTL_SECONDS = 300

def emit_tournament_data(license_key, tournament_id):
    data = getTournamentById(tournament_id).to_dict()
    
    device = getDeviceByLicenseKey(license_key)
    data["stream_key"] = getStreamKeyByTournamentIdAnCourt(tournament_id, device.court)
    data["court_num"] = device.court

    emit("tournament_data", {"message": "ok", "data": data})

@app_socketio.on("connect")
def on_connect(auth=None):
    """
    Client should pass token via:
      io("https://host", { auth: { token: "..." } })
    """
    # check if frontend is connecting
    is_frontend = False

    if isinstance(auth, dict):
        is_frontend = auth.get("token") == "frontend"

    if is_frontend:
        print("Frontend connected")
        join_room("frontend_clients")
        return
        

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

    # clearing device connection if there is any
    clearDeviceCourtTournamentIdSidState(machine_id)

    tournament_id = checkDeviceAssignedTournament(license_key=license_key)
    print(tournament_id)
    
    if tournament_id:
        emit_tournament_data(license_key, tournament_id)
        return

    # You can put them into the socket session (per-connection context)
    
    # request.environ["license_key"] = license_key
    # request.environ["machine_id"] = machine_id

    # Optional: group sockets by license key
    # join_room(f"lic:{license_key}")
    today = datetime.date.today()   
    tournaments = getTournamentsByDate(today)
    print("NEW DEVICE CONNECTION")
    emit("tournaments_list", {
        "message" : "ok",
        "license_key": license_key,
        "tournaments": [x.to_dict() for x in tournaments]
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
    
    tournament: Tournaments = getTournamentByName(tournament_name)
    print("Printing from select_tournament")
    print(tournament)

    if not tournament:
        emit("tournament_data", {"message": "error", "data": {}})
        return
    
    assignDeviceToTournament(license_key, tournament.id, court)

    emit_tournament_data(license_key, tournament.id)
    return

@app_socketio.on("confirm_connection")
def confirmConnection(data):
    print("CONFIRM CONNECTION TRIGGERED")

    sid = request.sid
    license_key = data.get("license_key")
    print(sid, license_key)

    tournament_id = assignDeviceSid(sid, license_key)
    machine_id = getMachineIdBySid(sid)

    if not machine_id:
        raise RuntimeError("No machine id")

    setMachineStatus(machine_id, "online")

    app_socketio.emit(
        "device_status_changed",
        {
            "data": {
                "machine_id": machine_id,
                "status": "online"
            }
        },
        to="frontend_clients"
    )
    join_room(str(tournament_id))
    print(f"JOINED TO ROOM {tournament_id}")

    return

@app_socketio.on("update_fight_data")
def update_fight_data(data):
    print("UPDATING FIGHT DATA")
    row = data["data"]
    license_key = data.get("license_key")

    tournament_id = getTournamentIdByLicenseKey(license_key)

    row["tournament_id"] = tournament_id
    # ak nahodou existuje fight kde su poslane data rovnake pri tournament_id a fight_id -> update fight
    existuje_fight = getFightByTournamentIdAndId(int(tournament_id), int(row["id"]))
    print(existuje_fight)
    if existuje_fight:
        UpdateFight(int(row["id"]), row)
    else:
        status = InsertNewFight(row)
        if not status:
            raise RuntimeError("Error inserting new Fight")
    
    assignDeviceFightId(license_key, row["id"])
    return

@app_socketio.on("start_fight")
def start_fight(data):
    print("FIGHT STARTED")
    license_key = data.get("license_key")

    device_data = getDeviceByLicenseKey(license_key).to_dict()
    fight_data = getFightById(str(device_data["current_fight"]))
    fight_data = fight_data.to_dict()
    fight_data = fight_data.get("data")
    tournament_id = device_data["tournament_id"]

    emit("other_fight_started", {"data": fight_data}, to=str(tournament_id))

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

@app_socketio.on("disconnect")
def disconnect():
    machine_id = getMachineIdBySid(request.sid)

    setMachineStatus(machine_id, "offline")

    app_socketio.emit(
        "device_status_changed",
        {
            "data": {
                "machine_id": machine_id,
                "status": "offline"
            }
        },
        to="frontend_clients"
    )