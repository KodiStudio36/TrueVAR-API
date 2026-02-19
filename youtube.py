import pickle
import pytz
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_youtube_service():
    creds = None

    # Load saved credentials if they exist
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there are no valid credentials, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This opens browser for OAuth login
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)

            flow.redirect_uri = "http://localhost:3500/oauth2callback"
            creds = flow.run_local_server(
                host="localhost",
                port=3500,
                redirect_uri_trailing_slash=False,
                success_message="Auth complete. You can close this tab.",
            )
        # Save credentials for next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    # Return authenticated YouTube API client
    return build("youtube", "v3", credentials=creds)

def create_stream(youtube, title: str):
    """
    Creates a liveStream resource and returns:
    - stream_id (resource id for API binding)
    - ingestion_address (RTMP server)
    - stream_name (RTMP key)
    """
    request = youtube.liveStreams().insert(
        part="snippet,cdn,contentDetails,status",
        body={
            "snippet": {"title": title},
            "cdn": {
                "frameRate": "30fps",
                "resolution": "720p",
                "ingestionType": "rtmp"
            },
            "contentDetails": {
                "isReusable": True
            }
        }
    )
    resp = request.execute()

    stream_id = resp["id"]
    ingestion = resp["cdn"]["ingestionInfo"]
    ingestion_address = ingestion["ingestionAddress"]
    stream_name = ingestion["streamName"]

    return stream_id, ingestion_address, stream_name


def create_broadcast(youtube, title: str, description: str, start_time, privacy="private"):
    """
    Creates a liveBroadcast (scheduled event) and returns broadcast_id.
    Note: liveBroadcast id is also the video id.
    """
    if start_time.tzinfo is None:
        start_time = pytz.timezone("Europe/Bratislava").localize(start_time)
    start_iso = start_time.astimezone(pytz.UTC).isoformat()

    request = youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": start_iso,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            },
            "contentDetails": {
                "enableAutoStart": False,
                "enableAutoStop": False
            }
        }
    )
    resp = request.execute()
    return resp["id"]


def bind_broadcast_to_stream(youtube, broadcast_id: str, stream_id: str):
    request = youtube.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    )
    return request.execute()
