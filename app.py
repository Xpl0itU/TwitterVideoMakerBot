import pyrebase
from flask import (
    Flask,
    render_template,
    send_file,
    after_this_request,
    request,
    redirect,
)
from flask_socketio import SocketIO
import os
from video_processing.final_video import generate_video, get_exported_video_path
from fixups.moviepy_fixups import moviepy_dummy
from firebase_info import firebase_auth
from window import MainWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, async_handlers=False)
firebase = pyrebase.initialize_app(firebase_auth)
links = list()
is_loggedin = False
text_only_mode = False
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
        return render_template(
            "dashboard.html", checked="checked" if text_only_mode else ""
        )
    return redirect("/")


@socketio.on("submit")
def handle_submit(data):
    if is_loggedin:
        global links
        links = data
        generate_video(links, text_only=text_only_mode)


@app.route("/video")
def get_video():
    if is_loggedin:
        exported_video_path = get_exported_video_path(links[0])
        if len(links) and os.path.isfile(exported_video_path):

            @after_this_request
            def delete_video(response):
                try:
                    os.remove(exported_video_path)
                except Exception as ex:
                    return ex
                return response

            return send_file(exported_video_path, as_attachment=True)
        return "No video to download"
    return redirect("/")


@socketio.on("set_text_only_mode")
def handle_set_text_only_mode(data):
    global text_only_mode
    text_only_mode = data["text"]


if __name__ == "__main__":
    moviepy_dummy()
    flask_thread = QThread()
    flask_thread.run = lambda: socketio.run(app, use_reloader=False, port=5001)
    flask_thread.start()
    app_qt = QApplication([])
    w = MainWindow()
    w.show()
    app_qt.exec()
