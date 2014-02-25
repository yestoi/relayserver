#!/usr/bin/python2

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol
import pdb, datetime, re, os

LISTEN_PORT = 443 # Your callbacks should be sent here
COMMAND_PORT = 444 # Port to interact with server
NETCAT = '/bin/nc' 
PROMPT = r'# $' #default shell prompt

class Listener(LineReceiver):
	
	def __init__(self, hosts, sched, conn, jobs):
		self.hosts = hosts
		self.sched = sched
		self.conn = conn
		self.jobs = jobs
		self.nc = None
		self.job = None

	def connectionMade(self):
		host = self.transport.getPeer().host
		print "Connected: ", host

		for record in self.hosts:
			if host in record:
				self.hosts.remove(record)
		
		self.hosts.append((host, datetime.datetime.now()))

		if self.sched:
			for shost, target, port in self.sched:
				if shost == host:
					cmd = [NETCAT, target, port]
					cwd = '/tmp'
						
					self.conn.append([host, target, port])
					self.nc = ProcessProtocol(self)	
					reactor.spawnProcess(self.nc, cmd[0], cmd, {}, cwd)

		elif self.jobs:
			for shost, job, p, c in self.jobs:
				if shost == host:
					self.job = 1

		elif not self.job and not self.nc:
			self.transport.loseConnection()

		else:		
			self.transport.loseConnection()

	def dataReceived(self, data):
		if self.nc != None:
			self.nc.transport.write(data)

		if self.jobs:
			for job in self.jobs:
				shost, filename, prompt, count = job
				if shost == self.transport.getPeer().host:
					if re.search(prompt, data):
						with open(os.getcwd() + "/jobs/" + filename) as jobfile:
							for line in jobfile.readlines():
								self.sendLine(line)
						self.transport.loseConnection()
						if count == 1:
							self.jobs.remove(job)
						if count > 1:
							count -= 1
								
	def connectionLost(self, reason):
		if self.nc != None:
			self.nc.transport.loseConnection()

class ProcessProtocol(protocol.ProcessProtocol):
	
	def __init__(self, nc):
		self.nc = nc
	
	def outReceived(self, data):
		self.nc.transport.write(data)

	def processEnded(self, reason):
		if self.nc.conn:
			for record in self.nc.conn:
				if self.nc.transport.getPeer().host in record:
					self.nc.conn.remove(record)

		self.nc.transport.loseConnection()

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
		self.state = "MENU"
		self.name = "--- Super Cool Relay Server v0.1 ---\n\n"
		self.help = "show - Show last connections\nlist - List scheduled relays, active relays, and jobs\nadd - Add relay (ex. add <host> <target> <port>)\n      Add job (ex. add <host> <job> (<times to run> default forever))\ndel - Delete relay(s) (ex. del <target> or del all)\n      Delete job (ex. del <target> <job>)\nclean - Clear out last connections cache"

	def connectionMade(self):
		self.sendLine(self.name + "(type help for commands)")

	def lineReceived(self, line):
		if self.state == "MENU":
			self.handle_menu(line)

	def handle_menu(self, cmd):
		if re.match(r'quit|exit', cmd):
			self.transport.loseConnection()

		if re.match(r'clean', cmd):
			listener.hosts = []

		if re.match(r'show', cmd):
			self.hosts = listener.hosts
			if self.hosts:
				for h,d in self.hosts:
					self.sendLine(str(h) + "     -- " + d.strftime("%I:%M%p"))
			else:
				self.sendLine("No connections")

		if re.match(r'add ', cmd):
			ipregex = r'([0-9]{1,3}\.){3}[0-9]{1,3}'
			if len(cmd.split()) == 4:
				c, host, target, port = cmd.split()
				if re.match(ipregex, host) and re.match(ipregex, target) and re.match(r'[0-9]{1,5}', port):
					listener.sched.append([host, target, port])	
				elif re.match(ipregex,host) and re.match(r'[a-zA-Z0-9]+', target):
					if re.match(r'[0-9]{1,}', port):
						listener.jobs.append([host, target, PROMPT, int(port)]) #host, job, prompt, count
					else:
						listener.jobs.append([host, target, port, None]) #host, job, prompt

			if len(cmd.split()) == 3:
				c, host, job = cmd.split()
				if re.match(ipregex, host) and re.match(r'[a-zA-Z0-9]+', job):
					listener.jobs.append([host, job, PROMPT, None])

		if re.match(r'del ', cmd):
			if len(cmd.split()) == 3:
				c, host, job = cmd.split()
				for record in listener.jobs:
					if host and job in record:
						listener.jobs.remove(record)
			if len(cmd.split()) == 2:
				c, host = cmd.split()
				if re.match(r'all', host):
					listener.sched = []	
				else:
					for record in listener.sched:
						if host in record:
							listener.sched.remove(record)
			
		if re.match(r'list', cmd):
			if listener.sched:
				self.sendLine("--- Relays ---")
				for host, target, port in listener.sched:
					self.sendLine(host + " will be relayed to " + target + " on port " + port)
			if listener.conn:
				self.sendLine("\n--- Connections ---")
				for host, target, port in listener.conn:
					self.sendLine(host + " --> " + target + ":" + port)
			
			if listener.jobs:
				self.sendLine("\n--- Jobs ---")
				for host, job, p, count in listener.jobs:
					if count == None:
						self.sendLine(host + " --> " + job)
					else:
						self.sendLine(host + " --> " + job + " '" + count + "' more times")

		if re.match(r'help', cmd):
			self.sendLine(self.help)	
		
		self.sendLine("") #newline after every input. Easier to read

class ControlFactory(Factory):
	def __init__(self, listener):
		self.listener = listener

	def buildProtocol(self, addr):
		return Control(self.listener)

listener = ListenerFactory()
reactor.listenTCP(LISTEN_PORT, listener)
reactor.listenTCP(COMMAND_PORT, ControlFactory(listener))
reactor.run()
