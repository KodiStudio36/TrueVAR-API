import os
from dotenv import load_dotenv
from flask import render_template, session
from app import create_app
load_dotenv()

app = create_app()

@app.route("/")
def index():
    print("hello world")
    return render_template("index.html", username=session.get("username"))

@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html", username=session.get("username"))

if __name__ == "__main__":
    PORT = int(os.getenv("PORT"))
    app.run(port=PORT, debug=True)