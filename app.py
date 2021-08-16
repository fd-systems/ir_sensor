#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request, \
        copy_current_request_context
from flask_socketio import SocketIO, emit
import busio
import adafruit_amg88xx
import board
import time
import json

i2c_bus = busio.I2C(board.SCL, board.SDA)
amg = adafruit_amg88xx.AMG88XX(i2c_bus)

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

_data  = dict()
def getData():
    global _data
    data = amg.pixels
    for i in range(len(data)):
        for j in range(0,7):
            data[i][j] = str(data[i][j])
    _data = json.dumps(data) 

def background_thread():
    count = 0
    while True:
        socketio.sleep(1)
        t0 = time.time()
        getData()
        t = time.time() - t0
        count += 1
        socketio.emit('my_response', {'data': _data, 'count': count, 'time':'%3.f'%t})

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': message['data'], 'count': session['receive_count']})

@socketio.event
def my_ping():
    emit('my_pong')

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
        emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('disconnect')
def test_disconnect():
    print('client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
