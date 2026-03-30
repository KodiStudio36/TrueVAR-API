from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import Boolean, Text, delete, select, Date, Time, Integer, DateTime, ForeignKey, update, event
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError
import secrets
import datetime
from datetime import date
import sqlalchemy as db
from enum import IntEnum


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
    draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tournament_state: Mapped[str] = mapped_column(Text, nullable=False, default="init")

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
            "draft": self.draft
        }

class Devices(Base):
    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(Text, nullable=True)
    license_key: Mapped[str] = mapped_column(Text, primary_key=True)
    machine_id: Mapped[str] = mapped_column(Text, nullable=True)
    expiration_date: Mapped[DateTime] = mapped_column(DateTime)
    issued_at: Mapped[DateTime] = mapped_column(DateTime)
    owner: Mapped[int] = mapped_column(Integer)
    tournament_id: Mapped[int] = mapped_column(Integer, ForeignKey("tournaments.id"), ForeignKey("fights.tournament_id"), nullable=True)
    court: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    sid: Mapped[str] = mapped_column(Text, nullable=True, default=None)
    current_fight: Mapped[int] = mapped_column(Integer, ForeignKey("fights.id"))

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
            "current_fight": self.current_fight
        }

class Fights(Base):
    __tablename__ = "fights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    hit_level: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(Text)
    clock: Mapped[str] = mapped_column(Text)
    round: Mapped[int] = mapped_column(Integer)
    blue_name: Mapped[str] = mapped_column(Text)
    blue_flag: Mapped[str] = mapped_column(Text)
    red_name: Mapped[str] = mapped_column(Text)
    red_flag: Mapped[str] = mapped_column(Text)
    blue_points: Mapped[str] = mapped_column(Text)
    red_points: Mapped[str] = mapped_column(Text)
    blue_penalty: Mapped[str] = mapped_column(Text)
    red_penalty: Mapped[str] = mapped_column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "title": self.title,
            "category": self.category,
            "hit_level": self.hit_level,
            "state": self.state,
            "clock": self.clock,
            "round": self.round,
            "blue_name": self.blue_name,
            "blue_flag": self.blue_flag,
            "red_name": self.red_name,
            "red_flag": self.red_flag,
            "blue_points": self.blue_points,
            "red_points": self.red_points,
            "blue_penalty": self.blue_penalty,
            "red_penalty": self.red_penalty
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
    try:
        with SessionLocal() as session:
            tournament = Tournaments(
                name=data["name"],
                desc=data["desc"],
                startDate=datetime.datetime.strptime(data["startDate"], "%Y-%m-%d").date(),
                startTime=datetime.datetime.strptime(data["startTime"], "%H:%M").time(),
                location=data["location"],
                courts=int(data["courts"]),
                scheduled=data["scheduled"], 
                video_ids=data["video_ids"],
                draft=data["draft"]
            )
            session.add(tournament)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Error while inserting a new tournament")
    except ValueError:
        raise RuntimeError("Invalid string to int conversion")
    
def getAllRealTournaments():
    try:
        with SessionLocal() as session:
            query = select(Tournaments).where(Tournaments.draft == False)
            results = session.scalars(query).all()
            return results
    except SQLAlchemyError:
        raise RuntimeError("Error fetching tournaments...")

def getAllDraftTournaments():
    try:
        with SessionLocal() as session:
            query = select(Tournaments).where(Tournaments.draft == True) # I did == True for readability
            results = session.scalars(query).all()
            return results
    except SQLAlchemyError:
        raise RuntimeError("Error fetching tournaments...")
    
def getAllTournamentsNames():
    try:
        with SessionLocal() as session:
            query = select(Tournaments.name)
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
                title=data["title"],
                category=data["category"],
                hit_level=data["hit_level"],
                state=data["state"],
                clock=data["clock"],
                round=data["round"],
                blue_name=data["blue_name"],
                blue_flag=data["blue_flag"],
                red_name=data["red_name"],
                red_flag=data["red_flag"],
                blue_points=" ".join(map(str, data["blue_points"])),
                red_points=" ".join(map(str, data["red_points"])),
                blue_penalty=" ".join(map(str, data["blue_penalty"])),
                red_penalty=" ".join(map(str, data["red_penalty"]))
            )
            session.add(fight)
            session.commit()
            return True
    except SQLAlchemyError:
        raise RuntimeError("Inserting new user has failed")
    
def UpdateFight(id: int, data):
    try:
        with SessionLocal() as session:
            query = update(Fights).where(Fights.id == id).values(
                tournament_id=data["tournament_id"],
                title=data["title"],
                category=data["category"],
                hit_level=data["hit_level"],
                state=data["state"],
                clock=data["clock"],
                round=data["round"],
                blue_name=data["blue_name"],
                blue_flag=data["blue_flag"],
                red_name=data["red_name"],
                red_flag=data["red_flag"],
                blue_points=" ".join(map(str, data["blue_points"])),
                red_points=" ".join(map(str, data["red_points"])),
                blue_penalty=" ".join(map(str, data["blue_penalty"])),
                red_penalty=" ".join(map(str, data["red_penalty"])),
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

        if result.rowcount == 0:
            return True
        return False
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
