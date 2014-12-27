from gevent import monkey
monkey.patch_all() 
from flask import Flask, send_file, render_template, copy_current_request_context
from flask.ext.socketio import SocketIO, emit
from threading import Thread 
import time, pdb, os, argparse, gevent, socket, re

parser = argparse.ArgumentParser()
parser.add_argument("num", help="Number of teams", type=int)
parser.add_argument("ips", help="List of ips comma seperated with 'x' in place of team offset")
parser.add_argument("oct", help="Starting team octect", type=int)
args = parser.parse_args()

app = Flask(__name__)
app.debug = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
socketio = SocketIO(app)

sess_thread = None
main_thread = None
relay_server = "127.0.0.1"
relay_port = 444
teams = []   # [team, ips]
sessions = {}
hackers = [] # [hacker, ip]
hacker_colors = ('#bf5b5b', '#c6b955', '#86b460', '#3c8d88', '#a76443', '#5273aa', '#973291', '#e53e45', '#7dad13', '#066d9b', '#3b060f', '#104a3e', '#798c2a')

for x in range(1, args.num+1):
    teams.append(["Team " + str(x), args.ips.replace("x", str(x)).split(",")])

for i,_ in enumerate(teams): 
    for a, ip in enumerate(teams[i][1]):
        teams[i][1][a] = [ip, "None", None] # Setup hacker/target array

def push_data():
    prev_data = {}
    while True:
        s = socket.socket()
        s.connect((relay_server, relay_port))
        s.recv(1024)
        s.send("show relay")
        relay = s.recv(1024)
        s.send("show")
        conns = s.recv(1024)
        s.close()

        #print relay
        #print conns
        for key in sessions.keys():
            host, target = key.split("--")
            hacker = [s for s in hackers if host in s]
            if hacker:
                h, hacker_ip, color = hacker[0]
                for i, _ in enumerate(teams):
                    for a, ip in enumerate(teams[i][1]):
                        if target in teams[i][1][a]:
                            teams[i][1][a] = [ip[0], h, color]

        data = {}
        for team, ips in teams:
            for ip, hacker, color in ips:
                data[ip] = color

            if prev_data != data:
                socketio.emit('team_data', data, namespace='/sessions')
                prev_data = dict(data)

        time.sleep(5)

def push_sessions():
    prev_sessions = {}
    init_loop = 2
    while True:
        files = list(os.walk('../sessions'))[0][2]
        global sessions 

        for f in files:
            fd = open('../sessions/' + f, 'r')
            sessions[f] = "".join(fd.readlines()[-19:])
            fd.close()

        if prev_sessions != sessions or init_loop > 0:
            socketio.emit('session_data', sessions, namespace='/sessions')
            prev_sessions = dict(sessions)

            if init_loop:
                init_loop -= 1

        time.sleep(1)

@app.route('/')
def index():
    global sess_thread
    if sess_thread is None:
        sess_thread = Thread(target=push_sessions)
        sess_thread.start()
        print "STARTED THREAD"

    return render_template('index.html', teams=teams, hackers=hackers)

@app.route('/js/<path:path>')
def servejs(path):
    return send_file('static/test/' + os.path.join('js', path))

@app.route('/css/<path:path>')
def servecss(path):
    return send_file('static/test/' + os.path.join('css', path))

@socketio.on('add_hacker', namespace='/sessions')
def add_hacker(msg):
    hackers.append([msg['hacker'], msg['ip'], hacker_colors[len(hackers)]])
    emit("hacker_data", {hackers[-1][0]:hackers[-1][1] + "," +  hackers[-1][2]}, broadcast=True)

@socketio.on('shell_cmd', namespace='/sessions')
def shell_cmd(msg):
    session = re.sub(r'(?<!-)-(?!-)', ".", msg['session'])
    s = socket.socket()
    s.connect((relay_server, relay_port))
    s.sendall("tap " + session + " " + msg['cmd'])
    s.close()

if __name__ == '__main__':
    main_thread = Thread(target=push_data)
    main_thread.start()
    socketio.run(app, host="0.0.0.0")
