import os
import pickle
from typing import Optional, Dict, Any, List

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from database import InsertStreamKey


# These scopes are accepted for liveStreams.list / liveStreams.insert.
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

            flow.redirect_uri = "http://localhost:5000/oauth2callback"
            creds = flow.run_local_server(
                host="localhost",
                port=3500,
                redirect_uri_trailing_slash=False,
                success_message="Auth complete. You can close this tab.",
            )

    # Return authenticated YouTube API client
    return build("youtube", "v3", credentials=creds)


def create_live_stream(
    youtube,
    title: str,
    description: str = "",
    resolution: str = "1080p",
    frame_rate: str = "30fps",
    ingestion_type: str = "rtmp",
    reusable: bool = True,
) -> Dict[str, Any]:
    """
    Creates a YouTube live stream and returns the stream metadata,
    including the stream key and ingest URL.
    """
    request = youtube.liveStreams().insert(
        part="snippet,cdn,contentDetails,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
            },
            "cdn": {
                "frameRate": frame_rate,
                "resolution": resolution,
                "ingestionType": ingestion_type,
            },
            "contentDetails": {
                "isReusable": reusable
            }
        }
    )

    response = request.execute()

    ingestion_info = response.get("cdn", {}).get("ingestionInfo", {})

    return {
        "youtube_stream_id": response.get("id"),
        "title": response.get("snippet", {}).get("title"),
        "stream_key": ingestion_info.get("streamName"),
        "ingestion_address": ingestion_info.get("ingestionAddress"),
        "backup_ingestion_address": ingestion_info.get("backupIngestionAddress"),
        "rtmps_ingestion_address": ingestion_info.get("rtmpsIngestionAddress"),
        "rtmps_backup_ingestion_address": ingestion_info.get("rtmpsBackupIngestionAddress"),
        "stream_status": response.get("status", {}).get("streamStatus"),
        "raw": response,
    }


def list_my_streams(youtube) -> List[Dict[str, Any]]:
    """
    Lists streams owned by the authenticated user.

    Important:
    mine=True does not list non-reusable streams.
    So use this mainly for reusable/default-like streams that are visible in list.
    """
    request = youtube.liveStreams().list(
        part="id,snippet,cdn,status",
        mine=True,
        maxResults=50
    )

    response = request.execute()
    items = response.get("items", [])

    output = []
    for item in items:
        ingestion_info = item.get("cdn", {}).get("ingestionInfo", {})
        output.append({
            "youtube_stream_id": item.get("id"),
            "title": item.get("snippet", {}).get("title"),
            "stream_key": ingestion_info.get("streamName"),
            "ingestion_address": ingestion_info.get("ingestionAddress"),
            "backup_ingestion_address": ingestion_info.get("backupIngestionAddress"),
            "stream_status": item.get("status", {}).get("streamStatus"),
            "raw": item,
        })
        InsertStreamKey(ingestion_info.get("streamName"), item.get("id"))
        

    return output


def get_stream_by_id(youtube, stream_id: str) -> Optional[Dict[str, Any]]:
    """
    Gets a specific stream by its YouTube stream ID.
    Useful for non-reusable streams if you already saved the ID.
    """
    request = youtube.liveStreams().list(
        part="id,snippet,cdn,status",
        id=stream_id
    )

    response = request.execute()
    items = response.get("items", [])

    if not items:
        return None

    item = items[0]
    ingestion_info = item.get("cdn", {}).get("ingestionInfo", {})

    return {
        "youtube_stream_id": item.get("id"),
        "title": item.get("snippet", {}).get("title"),
        "stream_key": ingestion_info.get("streamName"),
        "ingestion_address": ingestion_info.get("ingestionAddress"),
        "backup_ingestion_address": ingestion_info.get("backupIngestionAddress"),
        "stream_status": item.get("status", {}).get("streamStatus"),
        "raw": item,
    }


def build_full_rtmp_url(stream_data: Dict[str, Any]) -> Optional[str]:
    """
    Some encoders want one combined RTMP URL:
    rtmp://.../app/STREAM_KEY
    """
    address = stream_data.get("ingestion_address")
    key = stream_data.get("stream_key")

    if not address or not key:
        return None

    return f"{address}/{key}"


# Replace this with your real DB logic
def save_stream_to_db(
    tournament_id: int,
    court_number: int,
    stream_data: Dict[str, Any]
):
    """
    Example DB payload.
    Save AT LEAST:
    - youtube_stream_id
    - stream_key
    - ingestion_address
    - tournament_id
    - court_number
    """
    print("SAVE TO DB:")
    print({
        "tournament_id": tournament_id,
        "court_number": court_number,
        "youtube_stream_id": stream_data["youtube_stream_id"],
        "stream_key": stream_data["stream_key"],
        "ingestion_address": stream_data["ingestion_address"],
        "full_rtmp_url": build_full_rtmp_url(stream_data),
    })


if __name__ == "__main__":
    youtube = get_youtube_service()

    # # EXAMPLE 1:
    # # Create a stream and immediately save its key
    # stream = create_live_stream(
    #     youtube=youtube,
    #     title="valka - court 1",
    #     description="Tournament valka, court 1",
    #     resolution="1080p",
    #     frame_rate="30fps",
    #     ingestion_type="rtmp",
    #     reusable=True,
    # )

    # print("CREATED STREAM:")
    # print("Stream ID:", stream["youtube_stream_id"])
    # print("Stream key:", stream["stream_key"])
    # print("Ingest URL:", stream["ingestion_address"])
    # print("Full RTMP URL:", build_full_rtmp_url(stream))

    # save_stream_to_db(
    #     tournament_id=123,
    #     court_number=1,
    #     stream_data=stream
    # )

    # EXAMPLE 2:
    # List reusable streams visible under mine=True
    streams = list_my_streams(youtube)
    print("\nMY STREAMS:")
    for s in streams:
        print("-" * 40)
        print("Title:", s["title"])
        print("Stream ID:", s["youtube_stream_id"])
        print("Stream key:", s["stream_key"])
        print("Ingest URL:", s["ingestion_address"])
        print("Full RTMP URL:", build_full_rtmp_url(s))

    # EXAMPLE 3:
    # If you already saved a stream ID, fetch that exact stream again
    # existing = get_stream_by_id(youtube, "YOUR_STREAM_ID_HERE")
    # print(existing)