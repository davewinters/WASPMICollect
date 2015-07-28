# ----------------------------------------------------------------
# name  : simpleHTTPServer.py
# object: Simple MultiThreaded Web Server
# usage:  python SimpleHTTPServer [port] / default port: 8080
# author: denis_guillemenot@fr.ibm.com / denis.guillemenot@gmail.com
# date  : 19/09/2013
# ----------------------------------------------------------------

import sys

# Use default or provided port
print
if ( len( sys.argv) > 0):
  msg = "provided"
  try:
    cause = "must be an integer"
    port = int( sys.argv[0])
    if ( port < 1024): 
      cause = "must be =< 1024"
      raise
  except:
    print "ERROR: %s port:%s %s... exiting" % (msg, sys.argv[0], cause)
    sys.exit( 1)
else:
  msg = "default"
  port = 8080

print "Using %s port:%d" % ( msg, port)

import SocketServer, BaseHTTPServer, sys, os, CGIHTTPServer, os, os.path
# port = 8080
class ThreadingCGIServer( SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  pass

# set os separator
try:
  os_sep = os.path.os.sep
  False = 0
  True = 1
except:
  try:
    os_sep = os.path.sep
  except:
    print("ERROR: can not set os.separator, exiting...")
    sys.exit(-1)

# set rootdir
currdir = os.getcwd()
# rootdir = currdir + os_sep + 'data'
# if ( os.path.exists( rootdir)): os.chdir( rootdir)

# start HTTP Server
server = ThreadingCGIServer( ('', port), CGIHTTPServer.CGIHTTPRequestHandler)

print "Server started on port %s." % port
try:
  while 1:
    sys.stdout.flush()
    server.handle_request()
except keyboardInterrupt:
  if ( os.path.exists( currdir)): os.chdir( currdir)
  print "Server stopped."

