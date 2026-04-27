from flask import json
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import Boolean, Text, delete, select, Date, Time, Integer, DateTime, ForeignKey, update, event
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError
from enum import IntEnum
import sqlalchemy as db
import secrets
import datetime


ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
GROUPS = 4
GROUP_LEN = 4

def generate_licensekey():
    return "-".join(
        "".join(secrets.choice(ALPHABET) for _ in range(GROUP_LEN))
        for _ in range(GROUPS)
    )

class Owner(IntEnum):
    ME=1
    OTHER=0

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)

class Tournaments(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    desc: Mapped[str] = mapped_column(Text, nullable=False)
    startDate: Mapped[str] = mapped_column(Date, nullable=False)
    startTime: Mapped[str] = mapped_column(Time, nullable=False)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    courts: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    video_ids: Mapped[str] = mapped_column(Text, nullable=True, default=None)
    draft: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tournament_state: Mapped[str] = mapped_column(Text, nullable=False, default="init")
    discipline: Mapped[str] = mapped_column(Text, nullable=True, default="Kyorugi")
    message: Mapped[str] = mapped_column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "desc": self.desc,
            "startDate": self.startDate.isoformat(),
            "startTime": self.startTime.isoformat(),
            "location": self.location,
            "courts": self.courts,
            "scheduled": self.scheduled,
            "video_ids": self.video_ids,
            "draft": self.draft,
            "discipline": self.discipline,
            "message": self.message
        }

class Devices(Base):
    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(Text, nullable=True)
    license_key: Mapped[str] = mapped_column(Text, primary_key=True)
    machine_id: Mapped[str] = mapped_column(Text, nullable=True)
    expiration_date: Mapped[DateTime] = mapped_column(DateTime)
    issued_at: Mapped[DateTime] = mapped_column(DateTime)
    owner: Mapped[int] = mapped_column(Integer)
    tournament_id: Mapped[int] = mapped_column(Integer, nullable=True)
    court: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    sid: Mapped[str] = mapped_column(Text, nullable=True, default=None)
    current_fight: Mapped[int] = mapped_column(Integer, nullable=True)
    state: Mapped[int] = mapped_column(Text, nullable=False, default=0)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="offline")

    def to_dict(self):
        return {
            "name": self.name,
            "license_key": self.license_key,
            "machine_id": self.machine_id,
            "expiration_date": self.expiration_date.isoformat(),
            "issued_at": self.issued_at.isoformat(),
            "owner": self.owner,
            "tournament_id": self.tournament_id,
            "court": self.court,
            "sid": self.sid,
            "current_fight": self.current_fight,
            "state": self.state,
            "status": self.status,
        }

class Fights(Base):
    __tablename__ = "fights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    blue_name: Mapped[str] = mapped_column(Text)
    red_name: Mapped[str] = mapped_column(Text)
    win: Mapped[str] = mapped_column(Text, nullable=True)
    data: Mapped[str] = mapped_column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "blue_name": self.blue_name,
            "red_name": self.red_name,
            "win": self.win,
            "data": self.data,
        }
    
class Courts(Base):
    __tablename__ = "courts"

    court_num: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stream_key: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_date: Mapped[str] = mapped_column(Date, nullable=False)
    
    def to_dict(self):
        return {
            "court_num": self.stream_key,
            "tournament_id": self.tournament_id,
            "stream_key": self.stream_key,
            "scheduled_date": self.scheduled_date,
        }
    
class Stream_keys(Base):
    __tablename__ = "stream_keys"

    stream_id: Mapped[str] = mapped_column(Text, primary_key=True)
    stream_key: Mapped[str] = mapped_column(Text, primary_key=True)

    def to_dict(self):
        return {
            "stream_key": self.stream_key,
            "stream_id": self.stream_id
        }
    
class Discipline(Base):
    __tablename__ = "discipline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


# initialize engine & SessionLocal (session local lebo readability)
engine = db.create_engine("sqlite:///app.db", future=True)

def init_db():
    # THIS is what actually creates tables/files when first needed
    Base.metadata.create_all(bind=engine)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def InsertNewUSer(email: str, password: str):
    try:
        with SessionLocal() as session:
            # generating password hash to store in db
            password = generate_password_hash(password)
            user = User(
                email=email,
                password=password
            )
            session.add(user)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Inserting new user has failed")

def GetPasswordAndIdByEmail(email: str):
    try:
        with SessionLocal() as session:
            query = select(User.password, User.id).where(User.email == email)
            result = session.execute(query).first()

            # if username doesn not exist
            if result is None:
                return (None, None)
            
            return result[0], result[1]
    except SQLAlchemyError:
        raise RuntimeError("Error getting the password hash from db")
    
def tournamentCreate(data):
    for key, val in data.items():
        print(f"{key}: {val}")
    try:
        with SessionLocal() as session:
            tournament = Tournaments(
                name=data["name"],
                desc=data["desc"],
                startDate=datetime.datetime.strptime(data["startDate"], "%Y-%m-%d").date(),
                startTime=datetime.datetime.strptime(data["startTime"], "%H:%M").time(),
                location=data["location"],
                courts=int(data["courts"]),
                discipline=data["discipline"],
                draft=int(data["draft"]),
            )
            session.add(tournament)
            session.commit()
            return tournament.id
    except SQLAlchemyError:
        raise RuntimeError("Error while inserting a new tournament")
    except ValueError:
        raise RuntimeError("Invalid string to int conversion")
    
def getAllRealTournaments():
    try:
        with SessionLocal() as session:
            query = select(Tournaments).where(Tournaments.draft == 0)
            results = session.scalars(query).all()
            return results
    except SQLAlchemyError:
        raise RuntimeError("Error fetching tournaments...")

def getAllDraftTournaments():
    try:
        with SessionLocal() as session:
            query = select(Tournaments).where(Tournaments.draft == 1) # I did == True for readability
            results = session.scalars(query).all()
            return results
    except SQLAlchemyError:
        raise RuntimeError("Error fetching tournaments...")
    
def getAllTournamentsNames():
    try:
        with SessionLocal() as session:
            query = select(Tournaments)
            results = session.scalars(query).all()
            return results
    except SQLAlchemyError:
        raise RuntimeError("Error fetching tournament names...")

def getAllDevicesData():
    try:
        with SessionLocal() as session:
            query = select(Devices)
            results = session.scalars(query).all()
            return results
    except SQLAlchemyError:
        raise RuntimeError("Error fetching devices...")
    
def editDevicesTableDb(license_key: str, column: str, value: str):
    try:
        with SessionLocal() as session:
            query = update(Devices).where(Devices.license_key == license_key).values({getattr(Devices, column): value})
            session.execute(query)
            session.commit()
            return True
    except SQLAlchemyError:
        return False
    
def editTournamentDb(id: str, column, value: str):
    id = int(id)
    if column == "startTime":
        value = datetime.datetime.strptime(value, "%H:%M").time()
    elif column == "startDate":
        value = datetime.datetime.strptime(value, "%Y-%m-%d").date()
    elif column == "courts":
        value = int(value)
    try:
        with SessionLocal() as session:
            query = update(Tournaments).where(Tournaments.id == id).values({getattr(Tournaments, column): value})
            session.execute(query)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("error inserting")
    
def InsertNewDevice(expdate: DateTime, owner: int, name: str):
    try:
        with SessionLocal() as session:
            device = Devices(
                license_key=generate_licensekey(),
                expiration_date=expdate,
                issued_at=datetime.datetime.today(),
                owner=owner,
                name=name
            )
            session.add(device)
            session.commit()
            return device.license_key
    except SQLAlchemyError:
        raise RuntimeError("Error inserting a new device")
    
def getDeviceByLicenseKey(license: str):
    try:
        with SessionLocal() as session:
            query = select(Devices).where(Devices.license_key == license)
            result = session.scalars(query).first()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error inserting a new device")
    
def getTournamentByName(name: str):
    try:
        with SessionLocal() as session:
            query = select(Tournaments).where(Tournaments.name == name)
            result = session.scalars(query).first()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error getting tournament data")
    
def getTournamentById(id: str):
    try:
        with SessionLocal() as session:
            query = select(Tournaments).where(Tournaments.id == id)
            result = session.scalars(query).first()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error getting tournament data")
    
def setupMachineId(machine_id: str, license_key: str, device: Devices):
    with SessionLocal() as session:
        query = update(Devices).where(Devices.license_key == license_key).values(machine_id=machine_id)
        session.execute(query)
        session.commit()
        device = session.merge(device)
        session.refresh(device)
        return device
    return False

def checkDeviceAssignedTournament(license_key: str):
    with SessionLocal() as session:
        query = select(Devices.tournament_id).where(Devices.license_key == license_key)
        result = session.scalars(query).first()
        return result
    return False

def assignDeviceToTournament(license_key: str, tournament_id: str, court: int):
    with SessionLocal() as session:
        query = update(Devices).where(Devices.license_key == license_key).values(tournament_id=int(tournament_id), court=court)
        session.execute(query)
        session.commit()
        return True
    return False

def assignDeviceSid(sid: str, license_key: str):
    with SessionLocal() as session:
        query = update(Devices).where(Devices.license_key == license_key).values(sid=sid)
        session.execute(query)
        session.commit()
        #
        query = select(Devices.tournament_id).where(Devices.license_key == license_key)
        result = session.scalars(query).first()
        return result
    return False

def getVideoIdsByTournamentId(tournament_id: str):
    with SessionLocal() as session:
        query = select(Tournaments.video_ids).where(Tournaments.id == int(tournament_id))
        result = session.scalars(query).first()
        return result
    return False

def deleteTournamentDb(id: str):
    with SessionLocal() as session:
        query = delete(Tournaments).where(Tournaments.id == int(id))
        result = session.execute(query)
        session.commit()

        if result.rowcount == 0:
            return False

        return True
    return False

def getSidByMachineId(machine_id: str):
    with SessionLocal() as session:
        query = select(Devices.sid).where(Devices.machine_id == machine_id)
        result = session.scalars(query).first()
        return result
    return False

def InsertNewFight(data):
    try:
        with SessionLocal() as session:
            fight = Fights(
                id=data["id"],
                tournament_id=data["tournament_id"],
                blue_name=data["blue_name"],
                red_name=data["red_name"],
                win=data["win"],
                data=json.dumps(data)
            )
            session.add(fight)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Inserting new fight fail")
    
def UpdateFight(id: int, data):
    try:
        with SessionLocal() as session:
            query = update(Fights).where(Fights.id == id).values(
                blue_name=data["blue_name"],
                red_name=data["red_name"],
                win=None if data["win"] == "" else data["blue_name"] if data["win"] == "blue" else data["red_name"],
                data=json.dumps(data)
            )
            session.execute(query)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Inserting new user has failed")

def getFightByTournamentIdAndId(tournament_id: int, fight_id: int):
    with SessionLocal() as session:
        query = select(Fights).where(Fights.tournament_id, tournament_id and Fights.id == fight_id)
        result = session.scalars(query).first()
        print(result)
        if not result:
            return False
        return True
    return False
def getTournamentIdByLicenseKey(license_key: str):
    with SessionLocal() as session:
        query = select(Devices.tournament_id).where(Devices.license_key == license_key)
        result = session.scalars(query).first()
        return result
    return False

def assignDeviceFightId(license_key: str, fight_id: int):
    with SessionLocal() as session:
        query = update(Devices).where(Devices.license_key == license_key).values(current_fight=fight_id)
        session.execute(query)
        session.commit()
        return True
    return False

def getCurrentFightByLicenseKey(license_key: str):
    with SessionLocal() as session:
        query = select(Devices.current_fight).where(Devices.license_key == license_key)
        result = session.scalars(query).first()
        return result
    return False

def getFightById(id: int):
    with SessionLocal() as session:
        query = select(Fights).where(Fights.id == id)
        result = session.scalars(query).first()
        return result
    return False

def getDeviceByLicenseKey(license_key: int):
    with SessionLocal() as session:
        query = select(Devices).where(Devices.license_key == license_key)
        result = session.scalars(query).first()
        return result
    return False

def getAllStreamKeys():
    try:
        with SessionLocal() as session:
            query = select(Stream_keys.stream_key)
            results = session.scalars(query).all()
            return results
    except SQLAlchemyError:
        raise RuntimeError("Error fetching stream keys...")
    
def getScheduledTimesByStreamKey(stream_key: str):
    try:
        with SessionLocal() as session:
            query = select(Courts.scheduled_date).where(Courts.stream_key == stream_key)
            results = session.scalars(query).all()
            return results
    except SQLAlchemyError:
        raise RuntimeError("Error fetching stream keys...")
    
def insertNewCourtSchedule(court_num: int, tournament_id: int, stream_key: str, scheduled_date: str):
    try:
        with SessionLocal() as session:
            court = Courts(
                court_num=court_num,
                tournament_id=tournament_id,
                stream_key=stream_key,
                scheduled_date=datetime.datetime.strptime(scheduled_date, "%Y-%m-%d").date(),
            )
            session.add(court)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Error inserting a new schedule time for a court...")
    
def InsertStreamKey(stream_key: str, stream_id: str):
    try:
        with SessionLocal() as session:
            row = Stream_keys(
                stream_id=stream_id,
                stream_key=stream_key
            )
            session.add(row)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Error inserting a new schedule time for a court...")
    
def deleteCourtScheduleTimesByTournamentId(tournament_id: int):
    try:
        with SessionLocal() as session:
            query = delete(Courts).where(Courts.tournament_id == tournament_id)
            session.execute(query)
            session.commit()

            return True
    except SQLAlchemyError:
        raise RuntimeError("Error deleting court schedule time...")
    
def updateDeviceState(machine_id: int, state: int):
    try:
        with SessionLocal() as session:
            query = update(Devices).where(Devices.machine_id == machine_id).values(state=state)
            session.execute(query)
            session.commit()

            return True
    except SQLAlchemyError:
        raise RuntimeError("Error deleting court schedule time...")
    
def getDevicesByState(state: int):
    try:
        with SessionLocal() as session:
            query = select(Devices).where(Devices.state == state)
            result = session.scalars(query).all()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error deleting court schedule time...")
    
def getStreamKeyByTournamentIdAnCourt(tournament_id: int, court: int):
    try:
        with SessionLocal() as session:
            query = select(Courts.stream_key).where(Courts.court_num == court and Courts.tournament_id == tournament_id)
            result = session.scalars(query).first()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error deleting court schedule time...")
    
def getStreamIdByStreamKey(stream_key: str):
    try:
        with SessionLocal() as session:
            query = select(Stream_keys.stream_id).where(Stream_keys.stream_key == stream_key)
            result = session.scalars(query).first()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error deleting court schedule time...")

def getDevice_CourtByMachineIdandTournamentId(machine_id: str, tournament_id: int):
    try:
        with SessionLocal() as session:
            query = select(Devices.court).where(Devices.machine_id == machine_id and Devices.tournament_id == tournament_id)
            result = session.scalars(query).all()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error")
    
def getStreamKeyByTournamentIdAndCourt(court: int, tournament_id: int):
    print(court, tournament_id)
    court = court[0]
    try:
        with SessionLocal() as session:
            query = select(Courts.stream_key).where(Courts.tournament_id == tournament_id,Courts.court_num == court)
            result = session.scalars(query).all()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error")
    
def getVideoIdsByTournamentId(tournament_id: int):
    try:
        with SessionLocal() as session:
            query = select(Tournaments.video_ids).where(Tournaments.id == tournament_id)
            result = session.scalars(query).all()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error")
    
def clearDeviceCourtTournamentIdSidState(machine_id: str):
    try:
        with SessionLocal() as session:
            query = update(Devices).where(Devices.machine_id == machine_id).values(court=None,tournament_id=None,sid=None,state=0)
            session.execute(query)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Error")
    
def getDevicesByTournamentId(tournament_id: int):
    try:
        with SessionLocal() as session:
            query = select(Devices).where(Devices.tournament_id == tournament_id)
            result = session.scalars(query).all()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error")
    
def setMachineStatus(machine_id: str, status: str):
    try:
        with SessionLocal() as session:
            query = update(Devices).where(Devices.machine_id == machine_id).values(status=status)
            session.execute(query)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Error updating device state")
    
def getMachineIdBySid(sid: str):
    try:
        with SessionLocal() as session:
            query = select(Devices.machine_id).where(Devices.sid == sid)
            result = session.scalars(query).first()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error getting machine_id by sid")
    
def returnFightDataByNameAndTournamentId(name: str, tournament_id: int):
    try:
        with SessionLocal() as session:
            query = select(Fights.data).where(Fights.win == name and Fights.tournament_id == tournament_id)
            result = session.scalars(query).first()
            return result
    except SQLAlchemyError:
        raise RuntimeError("Error getting machine_id by sid")
    
def InsertNewDiscipline(name: str):
    try:
        with SessionLocal() as session:
            discipline_row = Discipline(name=name)
            session.add(discipline_row)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Error inserting a new discipline")
    
def getAllDisciplines():
    try:
        with SessionLocal() as session:
            query = select(Discipline)
            r = session.scalars(query).all()
            print(r)
            return r
    except SQLAlchemyError:
        raise RuntimeError("Error getting all disciplines")