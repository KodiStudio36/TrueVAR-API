from datetime import datetime
from flask import Blueprint, request, render_template, session
import pytz
from werkzeug.security import check_password_hash
from database import GetPasswordAndIdByEmail, changeTournamentStatus, getAllDisciplines, getDevicesByTournamentId, getPlaylistLinkByTournamenId, getTournamentsByStatus, tournamentCreate, getAllDevicesData, editDevicesTableDb, getTournamentById, editTournamentDb, getVideoIdsByTournamentId, deleteTournamentDb, getAllStreamKeys, getScheduledTimesByStreamKey, insertNewCourtSchedule, deleteCourtScheduleTimesByTournamentId, getStreamIdByStreamKey
from youtube import build_broadcast_description, build_playlist_description, create_broadcast, create_playlist, delete_playlist, get_youtube_service, add_video_to_playlist, set_thumbnail, delete_broadcast, bind_broadcast_to_stream
from .decorators import login_required
from flask import send_file
from io import BytesIO
import qrcode
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

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
    tournaments_init = getTournamentsByStatus("init")
    tournaments_draft = getTournamentsByStatus("draft")
    tournaments_archived = getTournamentsByStatus("archived")
    devicesData = getAllDevicesData()
    return render_template("dashboard.html",tournamentData=tournaments_init, devicesData=devicesData, drafts=tournaments_draft, archived=tournaments_archived)

@dashboard_bp.route("/tournament/create", methods=["GET", "POST"])
@login_required
def tournamentCreatePage():
    if request.method == "GET":
        disciplines = getAllDisciplines()
        return render_template("tournament_create.html", disciplines=disciplines)
    else:
        data = {
            "name": request.form.get("name"),
            "desc": request.form.get("desc"),
            "startDate": request.form.get("startDate"),
            "startTime": request.form.get("startTime"),
            "location": request.form.get("location"),
            "courts": request.form.get("courts"),
            "discipline": request.form.get("discipline"),
            "tournament_state": "init"
        }

        # validacia vstupov
        for key, value in data.items():
            if value == None:
                return {"message": "Bad request - missing data"}, 400

        tournament_id = tournamentCreate(data)

        if tournament_id:
            return {"message": "ok"}, 200
        return {"message": "Server error"}, 500
    
@dashboard_bp.route("/tournament/edit", methods=["POST"])
@login_required
def editTournament():
    data = request.get_json()

    ALLOWED_VISIBILITY_STATUSES = ["public", "private", "unlisted"]
    if data["column"] == "tournament_visibility" and data["value"] not in ALLOWED_VISIBILITY_STATUSES:
        return {"message": "Invalid visibility status"}, 400

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
    video_ids = video_ids if len(video_ids) == 1 else video_ids[0].split(" ") # minus jedna lebo ak je court 1 -> broadcast id je 0 (o 1 menej)
    
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
        devices = getDevicesByTournamentId(id)
        return render_template("tournament_dash.html", devicesData=devices, tournament=tournament_data)

@dashboard_bp.route("/public/tournament/create", methods=["POST", "GET"])
def public_tournament_create():
    if request.method == "GET":
        disciplines = getAllDisciplines()
        return render_template("public_tournament_create.html", disciplines=disciplines)
    elif request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "desc": request.form.get("desc"),
            "startDate": request.form.get("startDate"),
            "startTime": request.form.get("startTime"),
            "location": request.form.get("location"),
            "courts": request.form.get("courts"),
            "discipline": request.form.get("discipline"),
            "tournament_state": "draft"
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
    data = getTournamentById(id).to_dict()

    if data["scheduled"]:
        yt = get_youtube_service()
        video_ids = data["video_ids"]

        tournament_link = getPlaylistLinkByTournamenId(id)
        playlist_id = tournament_link.split("?list=")[-1]
        delete_playlist(yt, playlist_id)
        
        for broadcast_id in video_ids.split(" "):
            status = delete_broadcast(yt, broadcast_id)
            # on yt error
            if not status:
                return {"message": "Server error"}, 500
        deleteCourtScheduleTimesByTournamentId(id)
    

    status = deleteTournamentDb(id)
    # deletes any connections in the Courts table

    if status:
        return {"message": "ok"}, 200
    return {"message": "Server error"}, 500

@dashboard_bp.route("/tournament/schedule", methods=["POST"])
@login_required
def schedule():
    tournament_id = request.form.get("id")
    tournament_visibility = request.form.get("tournament_visibility")
    data = {
        "name": request.form.get("name"),
        "desc": request.form.get("desc"),
        "startDate": request.form.get("startDate"),
        "startTime": request.form.get("startTime"),
        "location": request.form.get("location"),
        "courts": request.form.get("courts")
    }
    date_str = data["startDate"]
    # validacia vstupov
    for key, value in data.items():
        if value == None:
            return {"message": "Bad request - missing data"}, 400
        
    # yt section
    data["startTime"] = data["startTime"][:5]
    start_time = datetime.strptime(
        f"{data["startDate"]} {data["startTime"]}",
        "%Y-%m-%d %H:%M"
    )

    images = request.files.getlist("image")
    tz = pytz.timezone("Europe/Bratislava")
    start_time = tz.localize(start_time)
    yt = get_youtube_service()
    video_ids = []

    playlist_desc = build_playlist_description(data)
    # creating playlist
    playlist_id = create_playlist(yt, data.get("name"), playlist_desc, privacy=tournament_visibility)

    for i in range(1, int(data.get("courts")) + 1):
        court_set = False
        title = f"{data.get("name")} Court {i}"
        livestream_desc = build_broadcast_description(data, i)

        video_id = create_broadcast(yt, title, livestream_desc, start_time, privacy=tournament_visibility)
        video_ids.append(video_id)
        # court num
        # get all stream keys and iterate over them
        stream_keys = getAllStreamKeys()
        print("PRITING DATA FOR LOOP")
        print(f"COURT: {i}")

        for stream_key in stream_keys:
            stream_id = getStreamIdByStreamKey(stream_key)
        # iterate over rows in table courts, check if stream key is occupied on start_date of this tournament
            stream_key_schedule_times = getScheduledTimesByStreamKey(stream_key)
            # iterate over schedule times and check if it occupied
            if not stream_key_schedule_times and not court_set:
                try:
                    insertNewCourtSchedule(i, tournament_id, stream_key, date_str)
                    bind_broadcast_to_stream(yt, video_id, stream_id)
                except RuntimeError:
                    print("Tried to insert the same info or db inserting failed.")
                    continue
                court_set = True
                continue
            if court_set:
                break
            for time_str in stream_key_schedule_times:
                string_time_str = time_str.strftime("%Y-%m-%d")
                if string_time_str == date_str:
                    continue
                else:
                    try:
                        insertNewCourtSchedule(i, tournament_id, stream_key, date_str)
                        bind_broadcast_to_stream(yt, video_id, stream_id)
                    except RuntimeError:
                        print("Tried to insert the same info or db inserting failed.")
                        continue
                    court_set = True
            
            if court_set:
                break
        if court_set:
            continue
                    
            # if is scheduled -> skip
            # if not -> assign this court this stream key (insert a row in courts table)    
    
    for index, video_id in enumerate(video_ids):
        # set thumbnails    
        set_thumbnail(yt, video_id, images[index], images[index].filename)
        status = add_video_to_playlist(yt, playlist_id, video_id)
        assert status
    
    tempString = ""
    first = False
    for video_id in video_ids:
        if not first:
            tempString = video_id
            first = True
            continue
        tempString += f" {video_id}"
    data["video_ids"] = tempString
    data["scheduled"] = True
    for key, value in data.items():
        editTournamentDb(tournament_id, key, value)

    editTournamentDb(tournament_id, "playlist_link", f"https://www.youtube.com/playlist?list={playlist_id}")

    return {"message": "ok"}, 200

@dashboard_bp.route("/tournament/playlist-qr/<int:tournament_id>")
@login_required
def playlist_qr_pdf(tournament_id):
    playlist_url = getPlaylistLinkByTournamenId(int(tournament_id))

    # Path to your poster image
    poster_path = "app/static/livestream-poster.png"
    # Load poster to get aspect ratio
    poster = PILImage.open(poster_path)
    poster_width_px, poster_height_px = poster.size
    # Use poster size as PDF size
    # 1 pixel = 1 PDF point here
    page_width = poster_width_px
    page_height = poster_height_px

    pdf_buffer = BytesIO()

    c = canvas.Canvas(pdf_buffer, pagesize=(page_width, page_height))

    # Draw poster over the full PDF page
    c.drawImage(
        poster_path,
        0,
        0,
        width=page_width,
        height=page_height
    )
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2
    )
    qr.add_data(playlist_url)
    qr.make(fit=True)
    qr_img = qr.make_image(
        fill_color="black",
        back_color="white"
    ).convert("RGB")

    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    qr_reader = ImageReader(qr_buffer)

    # QR placement
    # ReportLab coordinates start from BOTTOM LEFT, not top left.
    #
    # For your uploaded poster, approximate values:
    qr_size = 430
    qr_x = 310
    qr_y = 420

    c.drawImage(
        qr_reader,
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size
    )

    c.showPage()
    c.save()

    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="playlist_qr_code.pdf"
    )

@dashboard_bp.route("/tournament/archive", methods=["POST"])
@login_required
def archive():
    data = request.get_json()
    tournament_id = data.get("id")

    status = changeTournamentStatus(tournament_id, "archived")

    if not status:
        return {}, 500

    return {}, 200

@dashboard_bp.route("/tournament/promote", methods=["POST"])
@login_required
def promote():
    data = request.get_json()
    tournament_id = data.get("id")

    status = changeTournamentStatus(tournament_id, "init")

    if not status:
        return {}, 500

    return {}, 200
