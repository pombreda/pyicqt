import test_domish
import test_icq
import os

# Runs selected unit tests against Twisted to ensure that we're using a good version

def runICQTests():
	pass

def runXMLTests():
	t = test_domish.DomishStreamTestCase()
	t.testExpatStream()
	t.testSuxStream()


try:
	runICQTests()
	runXMLTests()
except:
	print "You are using a non-patched version of Twisted. Please download the patched version from http://msn-transport.jabberstudio.org"
	os.abort()
