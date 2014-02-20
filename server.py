#!/usr/bin/python2

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import pdb

class Listener(LineReceiver):
	delimeter = "\n"
	
	def __init__(self, hosts):
		self.hosts = hosts
		
	def connectionMade(self):
		self._peer = self.transport.getPeer().host
		print "Connected: ", self._peer
		self.hosts.append(self._peer)


class ListenerFactory(Factory):
	protocol = Listener

	def __init__(self):
		self.hosts = []
		
	def buildProtocol(self, addr):
		return Listener(self.hosts)

class Relay(LineReceiver):
	delimiter = "\n"
	
	def __init__(self, listener):
		#pdb.set_trace()
		self.hosts = listener.hosts
		self.state = "MENU"

	def connectionMade(self):
		if self.hosts:
			for h in self.hosts:
				self.sendLine(h)
		else:
			self.sendLine("No hosts")

	def lineReceived(self, line):
		if self.state == "MENU":
			self.handle_menu(line)

	def handle_menu(self, cmd):
		if cmd == "quit":
			self.transport.loseConnection()

class RelayFactory(Factory):
	def __init__(self, listener):
		self.listener = listener

	def buildProtocol(self, addr):
		return Relay(self.listener)

lf = ListenerFactory()
reactor.listenTCP(443, lf)
reactor.listenTCP(444, RelayFactory(lf))
reactor.run()
	
