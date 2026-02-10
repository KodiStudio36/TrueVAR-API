import base64
from datetime import datetime
from flask import Blueprint, json, request, session
from .decorators import license_required
from database import Devices
from cryptography.hazmat.primitives.asymmetric import ed25519
api_bp = Blueprint("api", __name__)

PRIVATE_KEY_HEX = "6420814ddfdc89a74847db945bc34564132ca842eca3dcde9c9e07c3c5c5ad13"
private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(PRIVATE_KEY_HEX))



@api_bp.route("ivr/fetch", methods=["POST"])
@license_required
def ivrFetch(device: Devices):
    license_data = {
                    "license_key": device.license_key,
                    "machine_id": device.machine_id,
                    "issued_at": int(device.issued_at.timestamp()),
                    "expires_at": int(device.expiration_date.timestamp())
                }
    data_string = json.dumps(license_data, sort_keys=True)
    signature = private_key.sign(data_string.encode())
    return {"status" : "OK",
            "license_blob" : {
                "data" : license_data,
                "signature": base64.b64encode(signature).decode('utf-8')
            }
        }, 200