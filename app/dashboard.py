from datetime import datetime, timedelta
from flask import Blueprint, redirect, request, render_template, session
import pytz
from werkzeug.security import check_password_hash
from database import GetPasswordAndIdByEmail, tournamentCreate, getAllRealTournaments, getAllDevicesData, editDevicesTableDb, getTournamentById, editTournamentDb, getVideoIdsByTournamentId, getAllDraftTournaments, deleteTournamentDb
from youtube import create_broadcast, create_playlist, get_youtube_service, add_video_to_playlist, set_thumbnail
from .decorators import login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        data = request.get_json()
        # nejde o riadky ide o readability takze si to takto spravim aby som sa neopakoval
        email = data["email"]
        password = data["password"]
        if not email or not password:
            return {"message": "bad request"}, 400
        
        db_password, user_id = GetPasswordAndIdByEmail(email)

        if db_password is None:
            return {"message": "user doesn't exist"}, 401

        if not check_password_hash(db_password, password):
            return {"message": "wrong password"}, 401

        session.clear()
        session["user_id"] = user_id
        session["username"] = email

        return {"message" : "ok"}, 200
    
@dashboard_bp.route("/")
@login_required
def dashboard():
    tournamentData = getAllRealTournaments()
    devicesData = getAllDevicesData()
    drafts = getAllDraftTournaments()
    return render_template("dashboard.html",tournamentData=tournamentData, devicesData=devicesData, drafts=drafts)

@dashboard_bp.route("/tournament/create", methods=["GET", "POST"])
@login_required
def tournamentCreatePage():
    if request.method == "GET":
        return render_template("tournament_create.html")
    else:
        data = {
            "name": request.form.get("name"),
            "desc": request.form.get("desc"),
            "startDate": request.form.get("startDate"),
            "startTime": request.form.get("startTime"),
            "location": request.form.get("location"),
            "courts": request.form.get("courts"),
            "scheduled": request.form.get("stream"),
            "draft": False
        }

        # validacia vstupov
        for key, value in data.items():
            if value == None:
                return {"message": "Bad request - missing data"}, 400
        
        data["scheduled"] = data["scheduled"].lower() == "true"

        if request.form.get("stream") == "true":
            date_str = data.get("startDate")
            time_str = data.get("startTime")

            start_time = datetime.strptime(
                f"{date_str} {time_str}",
                "%Y-%m-%d %H:%M"
            )
            # get images for thumbnails
            images = request.files.getlist("image")

            tz = pytz.timezone("Europe/Bratislava")
            start_time = tz.localize(start_time)
            yt = get_youtube_service()
            video_ids = []

            #creating playlist
            playlist_id = create_playlist(yt, data.get("name"), "Zapas livestream")

            for i in range(1, int(data.get("courts")) + 1):
                title = f"{data.get("name")} court {i}"
                video_id = create_broadcast(yt, title, f"Zapas livesteam z courtu {i}", start_time)
                video_ids.append(video_id)
            
            for index, video_id in enumerate(video_ids):
                # set thumbnails    
                set_thumbnail(yt, video_id, images[index], images[index].filename)
                status = add_video_to_playlist(yt, playlist_id, video_id)
                assert status


        # if this was scheduled right now, add the video id's to the db, else, put NULL there
        if data["scheduled"]:
            tempString = ""
            first = False
            for video_id in video_ids:
                if not first:
                    tempString = video_id
                    first = True
                    continue
                tempString += f" {video_id}"
            data["video_ids"] = tempString
        else:
            data["video_ids"] = None

        status = tournamentCreate(data)

        if status:
            return {"message": "ok"}, 200
        return {"message": "Server error"}, 500
    
@dashboard_bp.route("/tournament/edit", methods=["POST"])
@login_required
def editTournament():
    data = request.get_json()

    status = editTournamentDb(data["id"], data["column"], data["value"])

    if not status:
        return {"message": "Couldn't edit row (Serverside error)"}, 500
    
    return {"message": "ok"}, 200

@dashboard_bp.route("/tournament/thumbnailedit", methods=["POST"])
@login_required
def editThumbnail():
    images = request.files.getlist("image")
    tournament_id = request.form.get("tournament_id")
    video_ids = getVideoIdsByTournamentId(tournament_id)
    video_ids = video_ids.split(" ") # I did .split(" ") because the backend holds video ids in this format "[id] [id] [id]..."
    
    if not video_ids:
        return {"message": "database error - error fetching video_ids"}, 500
    yt  = get_youtube_service()

    for i in range(len(video_ids)):
        ans = set_thumbnail(yt, video_ids[i], images[i])
        if not ans:
            print(f"Error updating thumbnail {i}")
            return {"message": "Youtube error - error updating thumbnail."}, 500
    
    return {"message": "ok"}, 200
    
        
  
@dashboard_bp.route("/devices/edit", methods=["POST"])
@login_required
def editDevicesTable():
    data = request.get_json()
    ALLOWED_COLUMNS = ["license_key", "machine_id", "expiration_date", "issued_at", "owner", "tournament_id", "name"]

    if data["column"] not in ALLOWED_COLUMNS:
        return {"message": "error, invalid column"}, 400
    
    if data["value"] == "null":
        data["value"] = None

    status = editDevicesTableDb(data["license_key"], data["column"], data["value"])

    if not status:
        return {"message": "Couldn't edit row (Serverside error)"}, 500
    
    return {"message": "ok"}, 200

@dashboard_bp.route("/tournament/<int:id>")
@login_required
def tournament_dash(id):
    if request.method == "GET":
        tournament_data = getTournamentById(id=id)
        if tournament_data == None:
            tournament_data = 0
        devices = getAllDevicesData()
        return render_template("tournament_dash.html", devicesData=devices, tournament=tournament_data)

@dashboard_bp.route("/public/tournament/create", methods=["POST", "GET"])
def public_tournament_create():
    if request.method == "GET":
        return render_template("public_tournament_create.html")
    elif request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "desc": request.form.get("desc"),
            "startDate": request.form.get("startDate"),
            "startTime": request.form.get("startTime"),
            "location": request.form.get("location"),
            "courts": request.form.get("courts"),
            "draft": True
        }

        # validacia vstupov
        for key, value in data.items():
            if value == None:
                return {"message": "Bad request - missing data"}, 400
        
        data["scheduled"] = False
        data["video_ids"] = None
        
        status = tournamentCreate(data)
        if status:
            return {"message": "ok"}, 200
        return {"message": "Server error"}, 500
    
@dashboard_bp.route("/tournament/delete/<int:id>", methods=["DELETE"])
@login_required
def deleteTournament(id):
    status = deleteTournamentDb(id)
    if status:
        return {"message": "ok"}, 200
    return {"message": "Server error"}, 500