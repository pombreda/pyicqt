# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.web.microdom import parseXMLString, Element
import os
import os.path
import config
import debug

SPOOL_UMASK = 0177

class XDB:
	"""
	Class for storage of data. Compatible with xdb_file from Jabberd1.4.x
	Allows other transports to be compatible with this implementation
	
	All XML must be in the format of twisted.web.microdom
	
	Create one instance of the class for each XDB 'folder' you want.
	Call request()/set() with the xdbns argument you wish to retrieve
	"""
	def __init__(self, name, mangle=False):
		""" Creates an XDB object. If mangle is True then any '@' signs in filenames will be changed to '%' """
		self.name = config.spooldir + '/' + name
		if not os.path.exists(self.name):
			os.makedirs(self.name)
		self.mangle = mangle
	
	def __getFile(self, file):
		if(self.mangle):
			file = file.replace('@', '%')
		
		# Read the file
		f = open(self.name + "/" + file + ".xml")
		lines = f.readlines()
		f.close()
		file = ""
		for line in lines:
			file += line
		
		document = parseXMLString(file)
		
		return document.firstChild() # Strip the <?xml version = "1.0"?> tag
	
	def __writeFile(self, file, text):
		if(self.mangle):
			file = file.replace('@', '%')
		
		prev_umask = os.umask(SPOOL_UMASK)
		f = open(self.name + "/" + file + ".xml", "w")
		f.write(text)
		f.close()
		os.umask(prev_umask)
	
	
	def request(self, file, xdbns):
		""" Requests a specific xdb namespace from the XDB 'file' """
		try:
			document = self.__getFile(file)
			for child in document.childNodes:
				if(child.attributes["xdbns"]== xdbns):
					return child
		except:
			return None
	
	def set(self, file, xdbns, element):
		""" Sets a specific xdb namespace in the XDB 'file' to element """
		try:
			element.attributes["xdbns"] = xdbns
			try:
				document = self.__getFile(file)
			except IOError:
				document = Element("xdb")
			
			# Remove the existing node (if any)
			for child in document.childNodes:
				if(child.attributes["xdbns"] == xdbns):
					document.removeChild(child)
			# Add the new one
			document.appendChild(element)
			
			self.__writeFile(file, document.toprettyxml())
		except:
			debug.log("XDB error writing entry %s to file %s" % (xdbns, file))
			raise
	
	def remove(self, file):
		""" Removes an XDB file """
		file = self.name + "/" + file + ".xml"
		if(self.mangle):
			file = file.replace('@', '%')
		try:
			os.remove(file)
		except:
			debug.log("XDB error removing file " + file)
			raise

