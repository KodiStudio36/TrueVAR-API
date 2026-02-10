import datetime
import click
from flask.cli import with_appcontext
from database import InsertNewUSer, InsertNewDevice, Owner

@click.command("user")
@click.option("--email", required=True)
@click.option("--passwrd", required=True)
@with_appcontext
def user(email: str, passwrd: str):
    uspesnost = InsertNewUSer(email=email, password=passwrd)

    if not uspesnost:
        raise click.ClickException("Novy user nebol vytvoreny, chyba")

    click.echo(f"User {email} created")

@click.command("device")
@click.option("--expdate", required=True)
@click.option("--owner", default=Owner.ME)
@with_appcontext
def device(expdate: str, owner: str):
    dt = datetime.datetime.strptime(expdate, "%Y/%m/%d")

    uspesnost = InsertNewDevice(dt, owner)

    if not uspesnost:
        raise click.ClickException("Novy device nebol vytvoreny, chyba")

    click.echo(f"Device {uspesnost} created")