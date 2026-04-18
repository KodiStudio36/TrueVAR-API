import base64
from datetime import datetime
from flask import Blueprint, json, request, session
from flask_socketio import disconnect, emit, join_room
from app.extensions import app_socketio
from app.socket_token import create_socket_token
from .decorators import license_required, login_required
from database import Devices, getSidByMachineId, returnFightDataByNameAndTournamentId, updateDeviceState, getDevicesByState, getDevice_CourtByMachineIdandTournamentId, getStreamKeyByTournamentIdAndCourt, getStreamIdByStreamKey, getVideoIdsByTournamentId, clearDeviceCourtTournamentIdSidState
from cryptography.hazmat.primitives.asymmetric import ed25519
from youtube import check_stream_health, get_youtube_service, start_youtube_stream, stop_youtube_stream

api_bp = Blueprint("api", __name__)

PRIVATE_KEY_HEX = "6420814ddfdc89a74847db945bc34564132ca842eca3dcde9c9e07c3c5c5ad13"
private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(PRIVATE_KEY_HEX))


@api_bp.route("ivr/fetch/ping", methods=["HEAD", "GET"])
def ping():
    return "", 200

@api_bp.route("ivr/fetch", methods=["POST", "HEAD"])
@license_required
def ivrFetch(device: Devices):
    if request.method == "HEAD":
        return "", 200
    
    license_data = {
                    "license_key": device.license_key,
                    "machine_id": device.machine_id,
                    "issued_at": int(device.issued_at.timestamp()),
                    "expires_at": int(device.expiration_date.timestamp())
                }
    data_string = json.dumps(license_data, sort_keys=True)
    signature = private_key.sign(data_string.encode())

    socket_token = create_socket_token(
        license_key=device.license_key,
        machine_id=device.machine_id,
    )

    return {"status" : "OK",
            "license_blob" : {
                "data" : license_data,
                "signature": base64.b64encode(signature).decode('utf-8')
            },
            "socketio": {
            "token": socket_token,
            "expires_in": 300,  # client info (seconds)
        }
        }, 200

# PRVY go live (jedno ci broadcast or unicast, triggeruje to hocico)
@api_bp.route("dashboard/livestream", methods=["POST"])
@login_required
def start_livestream_unicast():
    data = request.get_json()

    machine_id = data.get("machine_id")
    tournament_id = data.get("tournament_id")

    # action can be start or stop
    action = data["action"]

    # send mode can be broadcast or unicast
    send_mode = data["send_mode"]

    if send_mode == "unicast": # machine id must exist

        sid = getSidByMachineId(machine_id)
        if action == "start":
            updateDeviceState(machine_id, 1)
        else:
            clearDeviceCourtTournamentIdSidState(machine_id)
            updateDeviceState(machine_id, 0)

        app_socketio.emit(
            f"{action}_livestream",
            {},
            to=sid
        )
        return {}, 200
    
    devices = ""
    if action == "start":
        state = 1
        devices = getDevicesByState(0)
    else:
        state = 0
        devices = getDevicesByState(1)

    for device_raw in devices:
        device = device_raw.to_dict()

        updateDeviceState(device["machine_id"], state)

    app_socketio.emit(
        f"{action}_livestream",
        {},
        to=tournament_id
    )
    return {}, 200

# DRUHY golive 
@api_bp.route("dashboard/stream", methods=["POST"])
@login_required
def api_stream():
    data = request.get_json()

    machine_id = data.get("machine_id")
    tournament_id = data.get("tournament_id")

    # action can be start or stop
    action = data["action"]

    # send mode can be broadcast or unicast
    send_mode = data["send_mode"]

    if send_mode == "unicast":
        # kontrola ci obs mam obsah
        yt = get_youtube_service()
        # get machine by machine_id and tournament_id -> to get court
        court = getDevice_CourtByMachineIdandTournamentId(machine_id, tournament_id)
        # get stream_key by tournament_id and court -> get stream keys
        stream_key = getStreamKeyByTournamentIdAndCourt(court, tournament_id)
        print("############")
        print(stream_key, court)
        # get stream_id by stream_key -> get stream_id
        stream_id = getStreamIdByStreamKey(stream_key[0])

        data_health = check_stream_health(yt, stream_id)
        # ak hej tak - zapnem stream
        status = data_health["is_receiving_data"]

        video_ids = getVideoIdsByTournamentId(tournament_id)[0]
        court = court[0]
        video_id = video_ids[0] if len(video_ids.split(" ")) == 1 else video_ids.split(" ")[court - 1] # minus jedna lebo ak je court 1 -> broadcast id je 0 (o 1 menej)
        print(video_id)
        sid = getSidByMachineId(machine_id)

        if action == "start" and status:
            start_youtube_stream(yt, video_id)
            updateDeviceState(machine_id, 2)

        elif status:
            stop_youtube_stream(yt, video_id)
            updateDeviceState(machine_id, 1)


        app_socketio.emit(
            f"{action}_stream",
            {},
            to=sid
        )
        return {}, 200
    
    devices = ""
    if action == "start":
        state = 2
        devices = getDevicesByState(1)
    else:
        state = 1
        devices = getDevicesByState(2)

    for device_raw in devices:
        device = device_raw.to_dict()

        updateDeviceState(device["machine_id"], state)
    app_socketio.emit(
        f"{action}_stream",
        {},
        to=tournament_id
    )
    return {}, 200

# TRETI go live
@api_bp.route("dashboard/tournament", methods=["POST"])
@login_required
def api_tournament():
    data = request.get_json()

    machine_id = data.get("machine_id")
    tournament_id = data.get("tournament_id")

    # action can be start or stop
    action = data["action"]

    # send mode can be broadcast or unicast
    send_mode = data["send_mode"]

    # set stream from obs to yt

    if send_mode == "unicast":
        if action == "start":
            updateDeviceState(machine_id, 3)
        else:
            updateDeviceState(machine_id, 2)

        sid = getSidByMachineId(machine_id)

        app_socketio.emit(
            f"{action}_tournament",
            {},
            to=sid
        )
        return {}, 200
    
    devices = ""
    if action == "start":
        state = 3
        devices = getDevicesByState(2)
    else:
        state = 2
        devices = getDevicesByState(3)

    for device_raw in devices:
        state = 3 if action == "start" else 2
        device = device_raw.to_dict()

        updateDeviceState(device["machine_id"], state)
    app_socketio.emit(
        f"{action}_tournament",
        {},
        to=tournament_id
    )
    return {}, 200


# TRETI go live
@api_bp.route("api/ivr/fights-won", methods=["GET"])
@login_required
def fightsWon():
    name = request.form.get("name")
    tournament_id = request.form.get("tournament_id")

    fightData = returnFightDataByNameAndTournamentId(name, int(tournament_id))

    return {"data": fightData}, 200

@api_bp.route("message/broadcast", methods=["POST"])
@login_required
def message_broadcast():
    data = request.get_json()
    message = data.get("message")
    tournament_id = data.get("tournament_id")

    app_socketio.emit(
        "stream_message_broadcast",
        {"message": message},
        to=str(tournament_id)
    )

    return {"message": "ok"}, 200