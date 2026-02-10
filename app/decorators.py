from datetime import date, datetime
from functools import wraps
from flask import redirect, session, request
from database import getDeviceByLicenseKey, Devices, setupMachineId, Owner

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/dashboard/auth/login")
        return view(*args, **kwargs)
    return wrapped

def license_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        data = request.get_json()

        if not data.get("license_key") or not data.get("machine_id"):
            return {"status": "error", "message" : "Invalid license"}, 401
        
        device:Devices = getDeviceByLicenseKey(data["license_key"])

        if not device or (device.machine_id and data["machine_id"] != device.machine_id):
            return {"status": "error", "message" : "Invalid license"}, 401
        
        if not device.machine_id:
            device = setupMachineId(data["machine_id"], data["license_key"], device=device)

            if not device:
                return {"status": "error", "message" : "Server error"}, 500
            
        if device.owner == Owner.ME:
            print("device owner is truevar")
            return view(*args,device=device, **kwargs)
        else:
            today = date.today()


            print(device.expiration_date)
            if device.expiration_date >= today:
                print("exp date is valid")
                return view(*args,device=device, **kwargs)
            else:
                return {"status": "error", "message" : "License expired"}, 401
    return wrapped
                 

        
