from flask import Flask, render_template, send_file, after_this_request
from flask_socketio import SocketIO
from threading import Timer
import webbrowser
import asyncio
import os
from video_processing.final_video import generate_video, get_exported_video_path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
link = str()

@app.route('/')
def index():
    return render_template('index.html')

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
    Timer(1, open_browser).start()
    socketio.run(app, debug=True, use_reloader=False)