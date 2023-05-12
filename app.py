import pyrebaselite
from flask import (
    Flask,
    render_template,
    send_file,
    after_this_request,
    request,
    redirect,
)
from flask_socketio import SocketIO
import asyncio
import os
import multiprocessing
from video_processing.final_video import generate_video, get_exported_video_path
from fixups.moviepy_fixups import moviepy_dummy
from firebase_info import firebase_auth
from window import MainWindow
from PyQt5.QtWidgets import QApplication
from engineio.async_drivers import threading
import platform
import webbrowser
from threading import Timer

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, async_mode="threading")
firebase = pyrebaselite.initialize_app(firebase_auth)
links = list()
is_loggedin = False
# Fix for macOS crash
os.environ["no_proxy"] = "*"


@app.route("/", methods=["GET", "POST"])
def login():
    global is_loggedin
    if is_loggedin:
        return redirect("/dashboard")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            auth = firebase.auth()
            user = auth.sign_in_with_email_and_password(email, password)
            if auth.get_account_info(user["idToken"]) is not None:
                # If authentication succeeds, redirect the user to their account page
                is_loggedin = True
                return redirect("/dashboard")
            else:
                # If authentication fails, render the login page with a message
                return render_template("login.html", message="Login failed")
        except:
            # If the password is invalid, render the login page with a message
            return render_template("login.html", message="Invalid email or password")
    return render_template("login.html")


@app.route("/dashboard")
def index():
    if is_loggedin:
        return render_template("dashboard.html")
    else:
        return redirect("/")


@socketio.on("submit")
def handle_submit(data):
    global links
    links = data
    asyncio.run(generate_video(links))


@app.route("/video")
def get_video():
    global links
    if len(links) and os.path.isfile(get_exported_video_path(links[0])):

        @after_this_request
        def delete_video(response):
            try:
                os.remove(get_exported_video_path(links[0]))
            except Exception as ex:
                return ex
            return response

        return send_file(get_exported_video_path(links[0]), as_attachment=True)
    return "No video to download"


if __name__ == "__main__":
    moviepy_dummy()
    if platform.system() == "Windows":
        Timer(1, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
        socketio.run(app, use_reloader=False)
    else:
        multiprocessing.set_start_method("fork")
        server = multiprocessing.Process(target=app.run, kwargs={"use_reloader": False})
        server.start()
        app_qt = QApplication([])
        w = MainWindow()
        w.show()
        app_qt.exec_()
        server.terminate()
        server.join()
