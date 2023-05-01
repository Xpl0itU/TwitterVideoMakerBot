import pyrebaselite
from flask import Flask, render_template, send_file, after_this_request, request, redirect
from flask_socketio import SocketIO
from threading import Timer
import webbrowser
import asyncio
import os
from video_processing.final_video import generate_video, get_exported_video_path
from fixups.moviepy_fixups import moviepy_dummy
from engineio.async_drivers import threading
from firebase_info import firebase_auth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')
firebase = pyrebaselite.initialize_app(firebase_auth)
link = str()
is_loggedin = False

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            auth = firebase.auth()
            user = auth.sign_in_with_email_and_password(email, password)
            if auth.get_account_info(user['idToken']) is not None:
                # If authentication succeeds, redirect the user to their account page
                is_loggedin = True
                return redirect('/dashboard')
            else:
                # If authentication fails, render the login page with a message
                return render_template('login.html', message='Login failed')
        except:
            # If the password is invalid, render the login page with a message
            return render_template('login.html', message='Invalid email or password')
    return render_template('login.html')

@app.route('/dashboard')
def index():
    if is_loggedin:
        return render_template('dashboard.html')
    else:
        return redirect('/')

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@socketio.on('submit')
def handle_submit(data):
    global link
    link = data['text']
    asyncio.run(generate_video(link))

@app.route('/video')
def get_video():
    if len(link) and os.path.isfile(get_exported_video_path(link)):
        @after_this_request
        def delete_video(response):
            try:
                os.remove(get_exported_video_path(link))
            except Exception as ex:
                print(ex)
            return response
        return send_file(get_exported_video_path(link), as_attachment=True)
    return "No video to download"

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    moviepy_dummy()
    Timer(1, open_browser).start()
    socketio.run(app, use_reloader=False)