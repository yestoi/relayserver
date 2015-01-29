#!/usr/bin/python2
from gevent import monkey
monkey.patch_all() 
from flask import Flask, send_file, render_template, copy_current_request_context
from flask.ext.socketio import SocketIO, emit
from threading import Thread 
import time, pdb, os, argparse, gevent, socket, re

sess_thread = None
main_thread = None
cmd_queue = []
relay_server = "127.0.0.1"
relay_port = 444
teams = []   # [team, ips]
tdata = {}
sessions = {}
jobs = [] # [job]
connects = [] # [ip]
hackers = [] # [hacker, ip]
hacker_colors = ['#86b460', '#c6b955', '#3c8d88', '#a76443', '#5273aa', 
                 '#973291', '#bf5b5b', '#7dad13', '#066d9b', '#104a3e', 
                 '#798c2a']

app = Flask(__name__)
app.debug = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
socketio = SocketIO(app)

# Threaded functions

def push_data():
    prev_tdata = {}
    prev_rdata = {}
    prev_cdata = []
    init_loop = 2
    global cmd_queue
    global jobs
    global connects
    global tdata

    while True: # Push data every 5 seconds
        s = socket.socket()
        s.connect((relay_server, relay_port))

        if cmd_queue:
            for cmd in cmd_queue:
                s.send(cmd)
            cmd_queue = []

        s.recv(1024) # Throw away initial output
        s.send("show relay")
        relay = s.recv(1024).replace("\n> ", "")[:-1]
        s.send("show")
        conns = s.recv(1024).replace("\n> ", "")[:-1]

        s.close()

        for key in sessions.keys(): 
            host, target = key.split("--")
            target = re.sub(':[0-9]+$', '', target)
            hacker = [s for s in hackers if target in s]
            if hacker:
                h, hacker_ip, color = hacker[0]
                for i, _ in enumerate(teams):
                    for a, ip in enumerate(teams[i][1]):
                        if host in teams[i][1][a]:
                            teams[i][1][a] = [ip[0], h, color] # Assign hacker color to hosts owned

        tdata = {} # Build team color data
        for team, ips in teams:
            for ip, hacker, color in ips:
                tdata[ip] = color

        rdata = {} # Build relay data
        for line in relay.split('\n'):
            if line:
                host, target, port = line.replace(' > ', ':').split(':')
                rdata[host] = target + "," + port

        cdata = [] # Build call in data
        lastline = conns.split('\n')[-1]
        if lastline != "No Connections":
            for conn in conns.split('\n'):
                cdata.append(conn)
                ip, date = conn.split(',')
                connects.append(ip) # Global varible for connections
            connects = list(set(connects)) # Make sure list stays as small as possible

        jobs = list(os.walk('../jobs'))[0][2] # Refresh jobs list

        # Emit our data if it's new
        if prev_tdata != tdata or init_loop > 0:
            socketio.emit('team_data', tdata, namespace='/sessions') 
            prev_tdata = dict(tdata)

        if prev_rdata != rdata or init_loop > 0:
            socketio.emit('relay_data', rdata, namespace='/sessions') 
            prev_rdata = dict(rdata)

            if init_loop:
                init_loop -= 1

        if prev_cdata != cdata:
            new_cdata = [j for i,j in zip(prev_cdata, cdata) if i != j]
            socketio.emit('conn_data', new_cdata, namespace='/sessions')
            prev_cdata = list(cdata)

        time.sleep(5)

def push_sessions():
    prev_sessions = {}
    init_loop = 2 #Push data 2 times initially

    while True:
        files = list(os.walk('../sessions'))[0][2]
        global sessions 

        for f in files:
            fd = open('../sessions/' + f, 'r')
            sessions[f] = "".join(fd.readlines()[-19:]) #Grab last 19 lines of session
            fd.close()

        if prev_sessions != sessions or init_loop > 0:
            socketio.emit('session_data', sessions, namespace='/sessions')
            prev_sessions = dict(sessions)

            if init_loop:
                init_loop -= 1

        time.sleep(1)

# Flask Handlers

@app.route('/')
def index():
    global sess_thread
    if sess_thread is None:
        sess_thread = Thread(target=push_sessions)
        sess_thread.start()
        print "STARTED THREAD"

    return render_template('index.html', teams=teams, hackers=hackers, conns=connects, jobs=jobs)

@app.route('/js/<path:path>')
def servejs(path):
    return send_file('static/' + os.path.join('js', path))

@app.route('/css/<path:path>')
def servecss(path):
    return send_file('static/' + os.path.join('css', path))

# SocketIO Handlers

hcount = 0 # Hacker Count
@socketio.on('add_hacker', namespace='/sessions')
def add_hacker(msg):
    global hcount
    hackers.append([msg['hacker'].strip(), msg['ip'], hacker_colors[hcount]])
    hcount += 1

    data = {}
    for hacker in hackers:
        (host, ip, color) = hacker
        data[host] = ip + "," + color
    emit("hacker_data", data, broadcast=True)

@socketio.on('del_hacker', namespace='/sessions')
def del_hacker(msg):
    hacker = [s for s in hackers if msg['ip'] in s][0]
    hcolor = hacker[2]
    hackers.remove(hacker)

    for i, _ in enumerate(teams): # Wipe hacker colors
        for a, record in enumerate(teams[i][1]):
            if hcolor in record:
                teams[i][1][a] = [record[0], None, "#777"]

    hacker_colors.append(hcolor) # Put retired color back on stack

    data = {}
    for hacker in hackers:
        (host, ip, color) = hacker
        data[host] = ip + "," + color
    emit("hacker_data", data, broadcast=True)

@socketio.on('refresh_teams', namespace='/sessions')
def refresh_teams(msg):
    socketio.emit('team_data', tdata, namespace='/sessions') 

@socketio.on('add_tag', namespace='/sessions')
def tag_ip(msg):
    for i, _ in enumerate(teams):
        for a, record in enumerate(teams[i][1]):
            if msg['ip'] in record:
                teams[i][1][a] = [record[0], None, msg['color']]

    socketio.emit('team_data', tdata, namespace='/sessions')

@socketio.on('rm_tag', namespace='/sessions')
def rm_tag(msg):
    for i, _ in enumerate(teams):
        for a, record in enumerate(teams[i][1]):
            if msg['ip'] in record:
                teams[i][1][a] = [record[0], None, "#777"]

    socketio.emit('team_data', tdata, namespace='/sessions')

@socketio.on('add_relay', namespace='/sessions')
def add_relay(msg):
    cmd_queue.append("add " + msg['host'] + " " + msg['target'] + " " + msg['port'])

@socketio.on('get_job', namespace='/sessions')
def get_job(msg):
    fd = open('../jobs/' + msg['job'].lower(), 'r')
    emit("job_data", {msg['job'].lower(): "".join(fd.readlines())})
    fd.close()

@socketio.on('new_job', namespace='/sessions')
def new_job(msg):
    fd = open('../jobs/' + msg['job'], 'w+')
    fd.write(msg['data'])
    fd.close()

@socketio.on('add_job', namespace='/sessions')
def add_job(msg):
    cmd_queue.append("add job " + msg['host'] + " " + msg['job'])

@socketio.on('shell_cmd', namespace='/sessions')
def shell_cmd(msg):
    session = re.sub(r'(?<!-)-(?!-)', ".", msg['session'])
    session = session[0:session.rfind(".")] + ":" + session[session.rfind(".")+1:]
    s = socket.socket()
    s.connect((relay_server, relay_port))
    s.sendall("tap " + session + " " + msg['cmd'])
    s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("num", help="Number of teams", type=int)
    parser.add_argument("ips", help="List of ips comma seperated with 'x' in place of team offset")
    parser.add_argument("octet", help="Starting team octet", type=int)
    args = parser.parse_args()

    i = 0
    for x in range(args.octet, args.octet+args.num): #Build Team structure
        i += 1
        teams.append(["Team " + str(i), args.ips.replace("x", str(x)).split(",")])

    for i,_ in enumerate(teams): 
        for a, ip in enumerate(teams[i][1]):
            teams[i][1][a] = [ip, None, "#777"] # Setup hacker/target array

    jobs = list(os.walk('../jobs'))[0][2]
    
    main_thread = Thread(target=push_data)
    main_thread.start()
    socketio.run(app, host="0.0.0.0")
