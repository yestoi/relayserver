#!/usr/bin/python2

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import pdb, datetime

class Listener(LineReceiver):
	delimeter = "\n"
	
	def __init__(self, hosts):
		self.hosts = hosts
		
	def connectionMade(self):
		host = self.transport.getPeer().host
		print "Connected: ", host

		for record in self.hosts:
			if host in record:
				self.hosts.remove(record)
		
		self.hosts.append((host, datetime.datetime.now()))


class ListenerFactory(Factory):

	def __init__(self):
		self.hosts = []
		
	def buildProtocol(self, addr):
		return Listener(self.hosts)

#class Relay(Protocol):
	

class Control(LineReceiver):
	delimiter = "\n"
	
	def __init__(self, listener):
		#pdb.set_trace()
		self.hosts = listener.hosts
		self.state = "MENU"

	def connectionMade(self):
		if self.hosts:
			for h,d in self.hosts:
				self.sendLine(str(h) + str(d))
		else:
			self.sendLine("No hosts")

	def lineReceived(self, line):
		if self.state == "MENU":
			self.handle_menu(line)

	def handle_menu(self, cmd):
		if cmd == "quit":
			self.transport.loseConnection()

class ControlFactory(Factory):
	def __init__(self, listener):
		self.listener = listener

	def buildProtocol(self, addr):
		return Control(self.listener)

listener = ListenerFactory()
reactor.listenTCP(443, listener)
reactor.listenTCP(444, ControlFactory(listener))
reactor.run()
	
