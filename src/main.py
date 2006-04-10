# Copyrigh 2004-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
import getopt
import sys
import os
import shutil
import time
import codecs
reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding
sys.stdout = codecs.lookup('utf-8')[-1](sys.stdout)

if __name__ == "__main__":
	print "The transport can no longer be started from main.py.  Please use"
	print "PyICQt.py from the root of the distribution instead."
	sys.exit(0)

from tlib.twistwrap import VersionNumber
if VersionNumber(sys.version[:3]) < VersionNumber("2.2"):
	print("You are using version %s of Python, at least 2.2 is required." % (sys.version[:3]))
	sys.exit(0)

import config
import xmlconfig
conffile = "config.xml"
profilelog = None
options = {}
daemonizeme = False
opts, args = getopt.getopt(sys.argv[1:], "bc:o:dDgtl:p:h", ["background", "config=", "option=", "debug", "Debug", "garbage", "traceback", "log=", "profile=", "help"])
for o, v in opts:
	if o in ("-c", "--config"):
		conffile = v
	elif o in ("-p", "--profile"):
		profilelog = v
	elif o in ("-b", "--background"):
                daemonizeme = True
	elif o in ("-d", "--debug"):
		config.debugLevel = 2
	elif o in ("-D", "--Debug"):
		config.debugLevel = 3
	elif o in ("-g", "--garbage"):
		import gc
		gc.set_debug(gc.DEBUG_LEAK|gc.DEBUG_STATS)
	elif o in ("-t", "--traceback"):
		config.debugLevel = 1
	elif o in ("-l", "--log"):
		config.debugFile = v
	elif o in ("-o", "--option"):
		var, setting = v.split("=", 2)
		options[var] = setting
	elif o in ("-h", "--help"):
		print "./PyICQt [options]"
		print "   -h                  print this help"
		print "   -b                  daemonize/background transport"
		print "   -c <file>           read configuration from this file"
		print "   -d                  print debugging output"
		print "   -D                  print extended debugging output"
		print "   -g                  print garbage collection output"
		print "   -t                  print debugging only on traceback"
		print "   -l <file>           write debugging output to file"
		print "   -o <var>=<setting>  set config var to setting"
		sys.exit(0)
#reload(debug)

#if config.extendedDebugOn:
#	from twisted.python import log
#	if debug.debugFile:
#		log.startLogging(debug.debugFile, 0)
#	else:
#		log.startLogging(sys.stdout, 0)
xmlconfig.Import(conffile, options)

def reloadConfig(a, b):
	# Reload default config and then process conf file
	reload(config)
	xmlconfig.Import(conffile, None)
	debug.reloadConfig()

# Set SIGHUP to reload the config file
if os.name == "posix":
	import signal
	signal.signal(signal.SIGHUP, reloadConfig)

selectWarning = "Unable to install any good reactors (kqueue, epoll, poll).\nWe fell back to using select. You may have scalability problems.\nThis reactor will not support more than 1024 connections +at a time.  You may silence this message by choosing 'select' or 'default' as your reactor in the transport config."
if config.reactor:
	# They picked their own reactor. Lets install it.
	del sys.modules["twisted.internet.reactor"]
	if config.reactor == "epoll":
		from twisted.internet import epollreactor
		epollreactor.install()
	elif config.reactor == "poll":
		from twisted.internet import pollreactor
		pollreactor.install()
	elif config.reactor == "kqueue":
		from twisted.internet import kqreactor
		kqreactor.install()
	elif config.reactor == "select":
		from twisted.internet import selectreactor
		selectreactor.install()
	elif config.reactor == "default":
		from twisted.internet import default
		default.install()
	elif len(config.reactor) > 0:
		print "Unknown reactor: ", config.reactor, ". Using default, select(), reactor."
else:
	# Find the best reactor
	del sys.modules["twisted.internet.reactor"]
	try:
		from twisted.internet import epollreactor as bestreactor
		#LogEvent(INFO, "", "Found and using epollreactor")
	except:
		try:
			from twisted.internet import kqreactor as bestreactor
			#LogEvent(INFO, "", "Found and using kqreactor")
		except:
			try:
				from twisted.internet import pollreactor as bestreactor
				#LogEvent(INFO, "", "Found and using pollreactor")
			except:
				try:
					from twisted.internet import selectreactor as bestreactor
					print selectWarning
				except:
					try:
						from twisted.internet import default as bestreactor
						print selectWarning
					except:
						print "Unable to find a reactor.\nExiting..."
						sys.exit(1)
	bestreactor.install()


from twisted.internet import reactor, task
from twisted.internet.defer import Deferred
import twisted.python.log
from tlib.twistwrap import component, jid, Element

from debug import LogEvent, INFO, WARN, ERROR
import debug
import xdb
import avatar
import session
import jabw
import iq
import disco
import adhoc
import pubsub
import register
import legacy
import lang
import globals



class PyTransport(component.Service):
	j2bound = 0
	def __init__(self):
		LogEvent(INFO)

		### Database prep-work
		# Open our spool
		self.xdb = xdb.XDB(config.jid)
		# We need to enable our avatar cache
		if not config.disableAvatars: self.avatarCache = avatar.AvatarCache()

		### Lets load some key/base functionality handlers
		# Service discovery support
		self.iq = iq.IqHandler(self)
		# Service discovery support
		self.disco = disco.ServiceDiscovery(self)
		# Ad-hoc commands support
		self.adhoc = adhoc.AdHocCommands(self)
		# Pubsub/PEP support
		#self.pubsub = pubsub.PublishSubscribe(self)
		# Registration support
		self.registermanager = register.RegisterManager(self)

		# Lets add some known built-in features to discovery
		self.disco.addIdentity("gateway", legacy.id, legacy.name, config.jid)
		self.disco.addFeature(globals.XHTML, None, "USER")

		# Lets load the base and legacy service plugins
		self.serviceplugins = {}
		self.loadPlugins("src/services")
		self.loadPlugins("src/legacy/services")

		# Misc tracking variables
		self.startTime = int(time.time())
		self.xmlstream = None
		self.sessions = {}
		# Message IDs
		self.messageID = 0
		
		# Routine cleanup/updates/etc
		self.loopCall = task.LoopingCall(self.loopCall)
		self.loopCall.start(60.0)
		
		# Display active sessions if debug mode is on
		#if config.debugOn:
		#	twisted.python.log.addObserver(self.exceptionLogger)


	def loadPlugins(self, dir):
		imppath = dir.replace("src/", "").replace("/", ".")
		files = os.listdir(dir);
		for i in range(len(files)):
			if files[i] == "__init__.py": continue
			if files[i].endswith(".py"):
				classname = files[i].replace(".py","")
				if self.serviceplugins.has_key(classname):
					print "Unable to load service plugin %s: Duplicate plugin???" % classname
					continue
				try:
					exec("from %s import %s" % (imppath, classname))
					exec("self.serviceplugins['%s'] = %s.%s(self)" % (classname, classname, classname))
				except Exception, e:
					print "Unable to load service plugin %s: %s" % (classname, e)


	def removeMe(self):
		LogEvent(INFO)
		for session in self.sessions.copy():
			self.sessions[session].removeMe()

	#def exceptionLogger(self, *kwargs):
	#	if len(config.debugLog) > 0:
	#		kwargs = kwargs[0]
	#		if kwargs.has_key("failure"):
	#			failure = kwargs["failure"]
	#			failure.printTraceback(debug) # Pass debug as a pretend file object because it implements the write method
	#			if config.debugLog:
	#				debug.flushDebugSmart()
	#				print "Exception occured! Check the log!"

	def makeMessageID(self):
		self.messageID += 1
		return str(self.messageID)
	
	def loopCall(self):
		numsessions = len(self.sessions)

		#if config.debugOn and numsessions > 0:
		#	debug.log("Sessions:")
		#	for key in self.sessions:
		#		debug.log("\t" + self.sessions[key].jabberID)
		#		for res in self.sessions[key].resourceList:
		#			debug.log("\t\t" + res)
        
		self.serviceplugins['Statistics'].stats["Uptime"] = int(time.time()) - self.startTime
		if numsessions > 0:
			oldDict = self.sessions.copy()
			self.sessions = {}
			for key in oldDict:
				session = oldDict[key]
				if not session.alive:
					LogEvent(WARN, "", "Ghost session found")
					# Don't add it to the new dictionary. Effectively removing it
				else:
					self.sessions[key] = session
	
	def componentConnected(self, xmlstream):
		LogEvent(INFO)
		self.xmlstream = xmlstream
		self.xmlstream.addObserver("/iq", self.iq.onIq)
		self.xmlstream.addObserver("/presence", self.onPresence)
		self.xmlstream.addObserver("/message", self.onMessage)
		self.xmlstream.addObserver("/bind", self.onBind)
		self.xmlstream.addObserver("/route", self.onRouteMessage)
		self.xmlstream.addObserver("/error[@xmlns='http://etherx.jabber.org/streams']", self.streamError)
		if config.useXCP and config.compjid:
			pres = Element((None, "presence"))
			pres.attributes["to"] = "presence@-internal"
			pres.attributes["from"] = config.compjid
			x = pres.addElement("x")
			x.attributes["xmlns"] = globals.COMPPRESENCE
			x.attributes["xmlns:config"] = globals.CONFIG
			x.attributes["config:version"] = "1"
			x.attributes["protocol-version"] = "1.0"
			x.attributes["config-ns"] = legacy.url + "/component"
			self.send(pres)
		#if config.saslUsername and config.useJ2Component:
		if config.useJ2Component:
			LogEvent(INFO, "", "J2C binding to %r" % config.jid)
			bind = Element((None,"bind"))
			#bind.attributes["xmlns"] = "http://jabberd.jabberstudio.org/ns/component/1.0"
			bind.attributes["name"] = config.jid
			self.send(bind)
		#if config.saslUsername and config.useJ2Component:
		if config.useJ2Component:
			self.j2bound = 1

		self.sendInvitations()

	def send(self, obj):
		if self.j2bound == 1 and type(obj) == Element:
			to = obj.getAttribute("to")
			route = Element((None,"route"))
			#route.attributes["xmlns"] = "http://jabberd.jabberstudio.org/ns/component/1.0"
			route.attributes["from"] = config.jid
			route.attributes["to"] = jid.JID(to).host
			route.addChild(obj)
			obj.attributes["xmlns"] = "jabber:client"
			component.Service.send(self,route.toXml())
		else:
			if type(obj) == Element:
				obj = obj.toXml()
			component.Service.send(self,obj)
	
	def componentDisconnected(self):
		LogEvent(INFO)
		self.xmlstream = None
		self.j2bound = 0

	def onRouteMessage(self, el):
		LogEvent(INFO)
		for child in el.elements():
			if child.name == "message": 
				self.onMessage(child)
			elif child.name == "presence":
				# Ignore any presence broadcasts about other XCP components
				if child.getAttribute("to") and child.getAttribute("to").find("@-internal") > 0: return
				self.onPresence(child)
			elif child.name == "iq":
				self.disco.onIq(child)
			elif child.name == "bind": 
				self.onBind(child)

	def onBind(self, el):
		LogEvent(INFO)

	def streamError(self, errelem):
		LogEvent(INFO)
		self.xmlstream.streamError(errelem)

	def streamEnd(self, errelem):
		LogEvent(INFO)
	
	def onMessage(self, el):
		fro = el.getAttribute("from")
		to = el.getAttribute("to")
		mtype = el.getAttribute("type")
		try:
			froj = jid.JID(fro)
		except Exception, e:
			LogEvent(WARN, "", "Failed stringprep")
			return
		if self.sessions.has_key(froj.userhost()):
			self.sessions[froj.userhost()].onMessage(el)
		elif mtype != "error":
			ulang = utils.getLang(el)
			body = None
			for child in el.elements():
				if child.name == "body":
					body = child.__str__()
			LogEvent(INFO, "", "Sending error response to a message outside of seession")
			jabw.sendErrorMessage(self, fro, to, "auth", "not-authorized", lang.get("notloggedin", ulang), body)
	
	def onPresence(self, el):
		fro = el.getAttribute("from")
		to = el.getAttribute("to")
		# Ignore any presence broadcasts about other JD2 components
		if to == None: return
		try:
			froj = jid.JID(fro)
			toj = jid.JID(to)
		except Exception, e:
			LogEvent(WARN, "", "Failed stringprep")
			return

		if self.sessions.has_key(froj.userhost()):
			self.sessions[froj.userhost()].onPresence(el)
		else:
			ulang = utils.getLang(el)
			ptype = el.getAttribute("type")
			if to.find('@') < 0:
				# If the presence packet is to the transport (not a user) and there isn't already a session
				if not ptype: # Don't create a session unless they're sending available presence
					LogEvent(INFO, "", "Attempting to create a new session")
					s = session.makeSession(self, froj.userhost(), ulang, toj)
					if s:
						self.sessions[froj.userhost()] = s
						LogEvent(INFO, "", "New session created")
						# Send the first presence
						s.onPresence(el)
						# Get the capabilities
						s.getCapabilities(el)
					else:
						LogEvent(INFO, "", "Failed to create session")
						jabw.sendMessage(self, to=froj.userhost(), fro=config.jid, body=lang.get("notregistered", ulang))
				
				elif ptype != "error":
					LogEvent(INFO, "", "Sending unavailable presence to non-logged in user")
					pres = Element((None, "presence"))
					pres.attributes["from"] = to
					pres.attributes["to"] = fro
					pres.attributes["type"] = "unavailable"
					self.send(pres)
					return
			
			elif ptype and (ptype.startswith("subscribe") or ptype.startswith("unsubscribe")):
				# They haven't logged in, and are trying to change subscription to a user
				# Lets log them in and then do it
				LogEvent(INFO, "", "New session created")
				s = session.makeSession(self, froj.userhost(), ulang, toj)
				if s:
					self.sessions[froj.userhost()] = s
					LogEvent(INFO, "", "New session created")
					# Tell the session there's a new resource
					s.handleResourcePresence(froj.userhost(), froj.resource, toj.userhost(), toj.resource, 0, None, None, None, None)
					# Send this subscription
					s.onPresence(el)

	def sendInvitations(self):              
		if config.enableAutoInvite:
			for jid in self.xdb.getRegistrationList():
				LogEvent(INFO, "", "Inviting %r" % jid)
				jabw.sendPresence(self, jid, config.jid, ptype="probe")
				jabw.sendPresence(self, jid, "%s/registered" % (config.jid), ptype="probe")



class App:
	def __init__(self):
		# Check that there isn't already a PID file
		if config.pid:
			if os.path.isfile(config.pid):
				try:
					pf = open(config.pid)
					pid = int(str(pf.readline().strip()))
					pf.close()
					if os.name == "posix":
						try:
							os.kill(pid, signal.SIGHUP)
							self.alreadyRunning()
						except OSError:
							# The process is still up
							pass
					else:
						self.alreadyRunning()
				except ValueError:
					# The pid file doesn't have a pid in it
					pass

			# Create a PID file
			pid = str(os.getpid())
			pf = file(config.pid,'w')
			pf.write("%s\n" % pid);
			pf.close()

		# Initialize debugging
		debug.reloadConfig()

		jid = config.jid
		if config.useXCP and config.compjid: jid = config.compjid

		if config.saslUsername:
			import sasl
			self.c = sasl.buildServiceManager(jid, config.saslUsername, config.secret, "tcp:%s:%s" % (config.mainServer, config.port))
		else:
			self.c = component.buildServiceManager(jid, config.secret, "tcp:%s:%s" % (config.mainServer, config.port))
		self.transportSvc = PyTransport()
		self.transportSvc.setServiceParent(self.c)
		self.c.startService()

		reactor.addSystemEventTrigger('before', 'shutdown', self.shuttingDown)

	def alreadyRunning(self):
		print "There is already a transport instance running with this configuration."
		print "Exiting..."
		sys.exit(1)

	def shuttingDown(self):
		self.transportSvc.removeMe()
		if config.pid:
			def cb(ignored=None):
				os.remove(config.pid)
			d = Deferred()
			d.addCallback(cb)
			reactor.callLater(3.0, d.callback, None)
			return d



def main():
	if daemonizeme:
		import daemonize
		if len(config.debugFile) > 0:
			daemonize.daemonize(stdout=config.debugFile,stderr=config.debugFile)
		else:
			daemonize.daemonize()

	# Do any auto-update stuff
	xdb.housekeep()

	app = App()
	if config.webport:
		try:
			from nevow import appserver
			import web
			site = appserver.NevowSite(web.WebInterface(pytrans=app.transportSvc))
			reactor.listenTCP(config.webport, site)
			LogEvent(INFO, "", "Web interface activated")
		except:
			LogEvent(WARN, "", "Unable to start web interface.  Either Nevow is not installed or you need a more recent version of Twisted.  (>= 2.0.0.0)")
	reactor.run()
