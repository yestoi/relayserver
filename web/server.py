from gevent import monkey
monkey.patch_all()

from flask import Flask, send_file
from flask.ext.socketio import SocketIO, emit
import time, pdb, os, argparse

parser = argparse.ArgumentParser()
parser.add_argument("num", help="Number of teams", type=int)
parser.add_argument("ips", help="List of ips comma seperated with 'x' in place of team offset")
parser.add_argument("oct", help="Starting team octect", type=int)
args = parser.parse_args()

teams = {}
for x in range(1, args.num+1):
    teams["Team " + str(x)] = args.ips.replace("x", str(x))

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'r3dteam'
socketio = SocketIO(app)

@app.route('/')
def index():
    return send_file('static/test/index.html')

@app.route('/js/<path:path>')
def servejs(path):
    return send_file('static/test/' + os.path.join('js', path))

@app.route('/css/<path:path>')
def servecss(path):
    return send_file('static/test/' + os.path.join('css', path))

@socketio.on('connect', namespace='/sessions')
def sess_connect():
    emit('team_data', teams)

    while True:
        files = list(os.walk('../sessions'))[0][2]
        sessions = {}

        for f in files:
            fd = open('../sessions/' + f, 'r')
            sessions[f] = "".join(fd.readlines()[-19:])
            fd.close()
        time.sleep(1)

        emit('session_data', sessions)

if __name__ == '__main__':
    socketio.run(app)
