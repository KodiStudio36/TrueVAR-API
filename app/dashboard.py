from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, session
import pytz
from werkzeug.security import check_password_hash
from database import GetPasswordAndIdByEmail, tournamentCreate, getAllTournaments, getAllDevicesData, editDevicesTableDb
from youtube import create_broadcast, create_stream, get_youtube_service
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
    tournamentData = getAllTournaments()
    devicesData = getAllDevicesData()
    print(devicesData)
    return render_template("dashboard.html",tournamentData=tournamentData, devicesData=devicesData)

@dashboard_bp.route("/tournament/create", methods=["GET", "POST"])
@login_required
def tournamentCreatePage():
    if request.method == "GET":
        return render_template("tournament_create.html")
    else:
        data = request.get_json()
        categories = ["name", "startDate", "startTime", "location", "courts"]

        # validacia vstupov
        for i in categories:
            if not data.get(i):
                return {"message": "Bad request - missing data"}, 400
        
        # insert a new tournament
        status = tournamentCreate(data)
        assert status == True

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

@dashboard_bp.route("/golive")
@login_required
def golive():
    yt = get_youtube_service()

    start = datetime.now(pytz.timezone("Europe/Bratislava")) + timedelta(minutes=10)

    stream_id, ingest_addr, stream_name = create_stream(yt, "API Test Stream")
    broadcast_id = create_broadcast(yt, "API Test Broadcast", "Testing api", start, privacy="private")