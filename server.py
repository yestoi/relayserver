#!/usr/bin/python2

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol
import pdb, datetime, re

LISTEN_PORT = 443 # Your callbacks should be sent here
COMMAND_PORT = 444 # Port to interact with server
NETCAT = '/bin/nc' 

class Listener(LineReceiver):
	
	def __init__(self, hosts, sched):
		self.hosts = hosts
		self.sched = sched
		self.nc = None

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
						
					self.nc = ProcessProtocol(self)	
					reactor.spawnProcess(self.nc, cmd[0], cmd, {}, cwd)
		else:		
			#Kill it if nothing is scheduled
			self.transport.loseConnection()

	def dataReceived(self, data):
		if self.nc != None:
			self.nc.transport.write(data)

	def connectionLost(self, reason):
		if self.nc != None:
			self.nc.transport.loseConnection()

class ProcessProtocol(protocol.ProcessProtocol):
	
	def __init__(self, nc):
		self.nc = nc
	
	def outReceived(self, data):
		self.nc.transport.write(data)

	def processEnded(self, reason):
		self.nc.transport.loseConnection()

class ListenerFactory(Factory):

	def __init__(self):
		self.hosts = []
		self.sched = []
		
	def buildProtocol(self, addr):
		return Listener(self.hosts, self.sched)


class Control(LineReceiver):
	delimiter = "\n"
	
	def __init__(self, listener):
		self.hosts = listener.hosts
		self.state = "MENU"
		self.name = "--- Super Cool Relay Server v0.1 ---\n\n"
		self.help = "Commands:\nshow - Show last connections\nlist - List scheduled relays\nadd - Add relay (ex. add <host> <target> <port>)\ndel - Delete relay(s) (ex. del <target> or del all)\nclean - Clear out last connections cache\n"

	def connectionMade(self):
		self.sendLine(self.name + self.help)

	def lineReceived(self, line):
		if self.state == "MENU":
			self.handle_menu(line)

	def handle_menu(self, cmd):
		if re.match(r'quit', cmd):
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
			c, host, target, port = re.split(r' ', cmd)
			if re.match(r'([0-9]{1,3}\.){3}[0-9]{1,3}', host) and re.match(r'([0-9]{1,3}\.){3}[0-9]{1,3}', target) and re.match(r'[0-9]{1,5}', port):
				listener.sched.append([host, target, port])	

		if re.match(r'del ', cmd):
			c, host = re.split(r' ', cmd)
			if host == "all":
				listener.sched = []	
			else:
				for record in listener.sched:
					if host in record:
						listener.sched.remove(record)
			
		if re.match(r'list', cmd):
			if listener.sched:
				for host, target, port in listener.sched:
					self.sendLine(host + " will be relayed to " + target + " on port " + port)

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
