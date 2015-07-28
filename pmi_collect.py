# ----------------------------------------------------------------
# name  : pmi_collect.py
# object: get all the WebSphere servers PMI using wsadmin (on the DMGR)
# usage : ./wsadmin.sh -conntype SOAP -lang jython -f pmi_collect.py
# author: denis_guillemenot@fr.ibm.com / denis.guillemenot@gmail.com
# date  : 19/09/2013
# ----------------------------------------------------------------
script_name = "pmi_collect.py"
shorty_name = "pmi_collect"

# ----------------------------------------------------------------
# import needed modules
# ----------------------------------------------------------------
import os, sys, time, os.path, re, time, shutil, traceback

# ----------------------------------------------------------------
# configuration template used to generate config file if needed
# ----------------------------------------------------------------
config_file_template = """
# ----------------------------------------------------------------
# Debug option: 
#   0: off  >0: on
# ----------------------------------------------------------------
debug_on = %s

# ----------------------------------------------------------------
# Polling interval
#   polling_occurences: number of time to run the script (0: infinite loop)
#   polling_interval_sec: interval in second between each run of the script
# ----------------------------------------------------------------
polling_occurences = %s
polling_interval_sec = %s

# ----------------------------------------------------------------
# data directory
#   <dir_base>/css    contains style sheet (.css)
#   <dir_base>/js     contains javascript (.js)
#   <dir_base>/logs   contains log files (.log)
# ---------------------------------------------------------------
dir_base = %s

# ----------------------------------------------------------------
# log file generated in [<dir_base>/logs] to trace execution, appended at each execution
# The format of the first line of this file is:
#   <path to the PMI parameter, separated by '.'>.<unit in lowercase>.<value>
# ----------------------------------------------------------------
systemout_log = %s

# ----------------------------------------------------------------
# log file generated in [<dir_base>/logs] to trace all available PMI, reset at each execution
# ----------------------------------------------------------------
pmi_log = %s

# ----------------------------------------------------------------
# output files definition
# list the files to generate in [<dir_base>/logs] containing PMI metrics
# for each files, define in a multilines string the PMI metrics to collect, one PMI metric by line
#     [label[:divisor]] regex_for_one_PMI_metric
# 
# label: if omitted, the label is the regex
# divisor: can be used to reduce the value returned (ex: HeapSize in Ko / 1024 becomes Mo)
# regex: must return only one PMI metric
#
# output files content
# each time the script is run, the last files are renamed and new files are created with the first line containing
# format for first line (used to named labels in the graphs): 
#   dd/mm/yyyy hh:mm:ss;<metric1 label>;<metric2 label>;...     
# format for all others lines: 
#   dd/mm/yyyy hh:mm:ss;<metric1>;<metric2>;...
# ----------------------------------------------------------------
output_files = %s

# ----------------------------------------------------------------
# HTML generation in [<dir_base>]
# HTML prefix
# ----------------------------------------------------------------
html_on = %s
html_prefix = %s

"""

# ----------------------------------------------------------------
# template for configuring output_files variable
# defines the logs to generate and PMI the PMI to collect 
#   %(node).%(server).jvmRuntimeModule.FreeMemory
#   %(node).%(server).threadPoolModule.WebContainer.ActiveCount
#   following PMIs have been removed
#   %(node)s.%(server)s.*.WebContainer.PercentMaxed
#   %(node)s.%(server)s.*.WebContainer.ClearedThreadHangCount
#   %(node)s.%(server)s.*.WebContainer.ConcurrentHungThreadCount
#   %(node)s.%(server)s.*.UsedMemory
#    %(node)s.%(server)s.*.WebContainer.ActiveTime
# ----------------------------------------------------------------
output_files_template = { 
  'JVM.log': """ 
    %(node)s.%(server)s.JVM.FreeMemory:1024 %(node)s.%(server)s.*.FreeMemory
    %(node)s.%(server)s.JVM.HeapSize:1024   %(node)s.%(server)s.*.HeapSize
  """,
  'TPOOLS.log': """
    %(node)s.%(server)s.WebContainer.ActiveCount               %(node)s.%(server)s.*.WebContainer.ActiveCount
    %(node)s.%(server)s.WebContainer.PoolSize                  %(node)s.%(server)s.*.WebContainer.PoolSize
    %(node)s.%(server)s.WebContainer.DeclaredThreadHungCount   %(node)s.%(server)s.*.WebContainer.DeclaredThreadHungCount
  """
}

# ----------------------------------------------------------------
# Get all JavaVirtualMachine of type APPLICATION_SERVER
# wsadmin>for i in srvs: print AdminConfig.showAttribute( i, 'serverType') + " " + AdminConfig.showAttribute( i, 'serverName') + " " + i
# DEPLOYMENT_MANAGER dmgr             dmgr(cells/redhat-6Cell01DEV/nodes/redhat-6Dmgr01DEV|serverindex.xml#ServerEntry_1)
# NODE_AGENT         nodeagent        nodeagent(cells/redhat-6Cell01DEV/nodes/redhat-6Node0101DEV|serverindex.xml#ServerEntry_1378364850689)
# APPLICATION_SERVER redhat-6Srv01DEV redhat-6Srv01DEV(cells/redhat-6Cell01DEV/nodes/redhat-6Node0101DEV|serverindex.xml#ServerEntry_1378365297099)
# WEB_SERVER         testWebSrv01DEV  testWebSrv01DEV(cells/redhat-6Cell01DEV/nodes/redhat-6Node0101DEV|serverindex.xml#ServerEntry_1379315321904)
# ----------------------------------------------------------------
def get_all_servers():
  srvs = AdminConfig.list("ServerEntry").split( lineSeparator)
  servers = []
  # print "Servers: "
  for srv in srvs:
    cell_node_server = srv.split('|')[0].split('/')
    _cell = cell_node_server[1]
    _node = cell_node_server[3]
    # _serv = AdminConfig.showAttribute( srv, "serverName")
    _serv = cell_node_server[0].split('(')[0]
    _servType = AdminConfig.showAttribute( srv, 'serverType')
    if _servType == 'APPLICATION_SERVER':
      servers.append( {'cell': _cell, 'node': _node, 'server': _serv})
    # print "  [ %s: %s / %s / %s ]" % (_servType, _cell, _node, _serv)
  return servers

# ----------------------------------------------------------------
# generate config file if needed
# ----------------------------------------------------------------
def generate_config_file( filename):
  debug_on = 0
  polling_occurences = 0
  polling_interval_sec = 120
  dir_base = './data'
  systemout_log = '%s_SystemOut.log' % shorty_name
  pmi_log = '%s_allPMI.log' % shorty_name
  output_files = {}
  html_on = 1
  html_prefix = ''
  # update with current values if possible
  try:
    f = open( filename, 'w')
    try:    debug_on = conf.debug_on
    except: print "    parameter 'debug_on' was missing"
    try:    polling_occurences = conf.polling_occurences
    except: print "    parameter 'polling_occurences' was missing"
    try:    polling_interval_sec = conf.polling_interval_sec
    except: print "    parameter 'polling_interval_sec' was missing"
    try:    dir_base = conf.dir_base
    except: print "    parameter 'dir_base' was missing"
    try:    systemout_log = conf.systemout_log
    except: print "    parameter 'systemout_log' was missing"
    try:    pmi_log = conf.pmi_log
    except: print "    parameter 'pmi_log' was missing"
    try:    output_files = conf.output_files
    except: print "    parameter 'output_files' was missing"
    try:    html_on = conf.html_on
    except: print "    parameter 'html_on' was missing"
    try:    html_prefix = conf.html_prefix
    except: print "    parameter 'html_prefix' was missing"
    # initialize output_files if empty
    output_files_str = repr( output_files)
    if not output_files:
      servers = get_all_servers()
      # for output in output_files_template.keys():
      #   print "output:" + output
      #   data = ""
      #   for srv in servers:
      #     data = data + output_files_template[ output] % {'node': srv['node'], 'server': srv['server']}
      #   output_files[ output] = data
      # stringify output_files
      output_files_str = "{\n"
      num_output = len( output_files_template.keys())
      for output in output_files_template.keys():
        output_files_str = output_files_str + "  " + repr( output) + ":" + " " + '"""'
        for srv in servers:
          output_files_str = output_files_str + output_files_template[ output] % {'node': srv['node'], 'server': srv['server']}
        output_files_str = output_files_str + '"""'
        num_output = num_output - 1
        if num_output: output_files_str = output_files_str + ',' + '\n'
        output_files_str = output_files_str + '\n'
        # print "output:" + output + " / output_files_str:" + output_files_str
      output_files_str = output_files_str + '}'
    # f.write( config_file_template % ( debug_on, polling_occurences, polling_interval_sec, repr(dir_base), repr(systemout_log), repr(pmi_log), repr(output_files), html_on, repr(html_prefix)))
    f.write( config_file_template % ( debug_on, polling_occurences, polling_interval_sec, repr(dir_base), repr(systemout_log), repr(pmi_log), output_files_str, html_on, repr(html_prefix)))
    f.close()
  except:
    print "  ERROR: while generating file %s..." % filename
    print "  " + str(  sys.exc_info())
    print "Exiting."
    sys.exit(-1)

# ----------------------------------------------------------------
# Before anything, check if we are connected with SOAP
# AdminControl object should be available
# ----------------------------------------------------------------
try:
  AdminControl.getCell()
  print("\nConnected: AdminControl object available...")
except:
  print("\nERROR: Not connected: AdminControl object not available, exiting...")
  sys.exit(-1)

# ----------------------------------------------------------------
# set error variable
#   unix: echo $?
#   windows: echo %ERRORLEVEL%
# ----------------------------------------------------------------
error = 0
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

# ----------------------------------------------------------------
# import config file OR exit
# ----------------------------------------------------------------
try:
  # import '%s_conf' % config_name as conf
  conf = __import__( '%s_conf' % shorty_name)
except:
  print "ERROR: file '%s_conf.py' is missing..." % shorty_name
  print "  Generating file '%s_conf.py'..." % shorty_name
  generate_config_file( '%s_conf.py' % shorty_name)
  print "  Generating file '%s_conf.py' finished." % shorty_name
  print "  Check if file '%s_conf.py' suits your needs and relaunch the script..." % shorty_name
  print "Exiting."
  sys.exit(-1)

try:
  conf.debug_on
  conf.polling_occurences
  conf.polling_interval_sec
  conf.dir_base
  conf.systemout_log
  conf.pmi_log
  conf.output_files
  conf.html_on
  conf.html_prefix
except:
  print "ERROR: Some needed variables are undefined !"
  print "  " + str(  sys.exc_info())
  print "Generating config file..."
  print "You can modify '%s_conf.py' using '%s_conf.py.template'..." % (shorty_name, shorty_name)
  generate_config_file( '%s_conf.py.template' % shorty_name)
  print "Exiting."
  sys.exit(-2)

if not conf.output_files:
  print "ERROR: output_files is empty !"
  print "Generating config file..."
  print "You can modify '%s_conf.py' using '%s_conf.py.template'..." % (shorty_name, shorty_name)
  generate_config_file( '%s_conf.py.template' % shorty_name)
  print "Exiting."
  sys.exit(-3)

# ----------------------------------------------------------------
# setting directories variables
# ----------------------------------------------------------------
dir_base   = conf.dir_base
dir_css    = 'css'
dir_js     = 'js'
dir_logs   = 'logs'
dir_base_css    = dir_base + os_sep + dir_css
dir_base_js     = dir_base + os_sep + dir_js
dir_base_logs   = dir_base + os_sep + dir_logs

print "\nLogs to check..."
print "  available PMIs: %s" % dir_base_logs + os_sep + conf.pmi_log
print "  systemOut.log : %s" % dir_base_logs + os_sep + conf.systemout_log

# ----------------------------------------------------------------
# checking data directories existence or create them
# ----------------------------------------------------------------
print "\nChecking directories for data..."
for dir in [ '', dir_css, dir_js, dir_logs]:
  directory = dir_base + os_sep + dir
  if os.path.exists( directory):
    print "  [%-15s] exists... ok" % directory
  else:
    try:
      os.makedirs( directory)
      print "  [%-15s] created... ok" % directory
    except:
      print "  ERROR: [%s] do not exists and can not be created, exiting..." % directory
      print str(  sys.exc_info())
      sys.exit(-1)

# ----------------------------------------------------------------
# copying javascript and css files
# ----------------------------------------------------------------
print "\nCopying javascript and CSS files..."

def copy_files( src_dir):
  for f in os.listdir( src_dir):
    src = '.' + os_sep + src_dir + os_sep + f
    dst = dir_base + os_sep + src_dir + os_sep + f
    try:
      shutil.copyfile( src, dst)
      print "  [%-30s] copy to [%-30s]... ok" % ( src, dst)
    except:
      print "  ERROR: while copying directory [%-30s] to [%-30s], exiting..." % ( src, dst)
      print str(  sys.exc_info())
      sys.exit(-1)

copy_files( dir_css)
copy_files( dir_js)

# ----------------------------------------------------------------
# copying javascript and css files
# ----------------------------------------------------------------
print "\nMoving existing output_files..."

def init_output_files():
  current_time = time.strftime('.%Y%m%d-%H%M%S')
  for f in conf.output_files.keys():
    filename = dir_base_logs + os_sep + f
    if os.path.exists( filename):
      try:
        print "  [%-30s] move to [%-30s]" % (filename, filename + current_time)
        os.rename( filename, filename + current_time)
      except:
        print "  ERROR: cannot move file %s..." % filename

init_output_files()


# ----------------------------------------------------------------
# if needed then initialize HTML templates
# ----------------------------------------------------------------
if conf.html_on:
    # ----------------------------------------------------------------
    # define template for HTML generation
    # ----------------------------------------------------------------

    html_index_template="""
    <html>
      <header> 
        <title>Index of %s</title> 

        <link rel="stylesheet" href="css/morris.css" />
        <link rel="stylesheet" href="css/csv_log_viewer.css" />
    
	<script type="text/javascript" src="js/jquery-1.8.3.min.js"></script>
	<script type="text/javascript" src="js/raphael-min.js"></script>
	<script type="text/javascript" src="js/morris.min.js"></script>
	<script type="text/javascript" src="js/csv_log_viewer.js"></script>
      </header>

      <body>
        <div class="title">
            <h1 > %s  </h1>

        <div id="filename" class="files_selection_selectedfile">
        </div>

        <div id="localfiles" class="files_selection_localfiles">
          <input type="file" id="files" name="file" multiple/>
        </div>

        <div id="logfiles" class="files_selection_remotefiles">
          <select id="logfile" name="lofgile" size="1">
           %s
         </select>

        </div>

        </div>

        <div class="files_selection">
        <div class="files_selection_date_picker">
                <!-- <p class="button">Select date to show</p> -->
                <button id="prev" class="button" type="button"> &lt&lt </button>
                <!-- <select id="date_picker" onChange="updateGraph();"> -->
                <select id="date_picker">
                </select>
                <button id="next" class="button" type="button"> &gt&gt </button>
        </div>

        </div>

        <div id="graph" class="graph"></div>

        <div id="msg" class="msg"></div>

        <div id="log" class="log">
                <div class="center"> <p class="button">Log content (click to view)</p> </div>
                <code id="log_content"> </code>
        </div>


        <!-- Retrieve and Display log content -->
        <script type="text/javascript">
          documentReady( '%s');
        </script>

      </body>
    </html>
    """
    html_index_line_template = """<option value='%s'> %s </option>"""

def print_and_write( f, s):
  print(s)
  f.write(s + '\n')

def generate_html():
    # parse dir_base_logs and generate HTML file:
    #   - index.html
    #   - <output>.html
    #   - <date>.html
    
    list_all_files_by_output = []    
    list_all_logfiles = []
    # generate one file for each conf.output_files
    # for output in conf.output_files.keys():
    for output in os.listdir( dir_base_logs):
      if ( output.find( shorty_name) != 0):
        list_all_logfiles.append( output)
    
    # generate the index of all HTML files
    filename = dir_base + os_sep + conf.html_prefix + "index.html"
    list_all_logfiles.sort()
    html_body_by_output = [ html_index_line_template % ( dir_logs + os_sep + chart, chart) for chart in list_all_logfiles]
    f = open( filename, 'w')
    f.write( html_index_template % (shorty_name, shorty_name, "\n".join( html_body_by_output), ''))
    f.close()
    
    # returns the number of files generated
    return len( html_body_by_output)    
    
    

# ----------------------------------------------------------------
# print the stats of the Stats object passed in parameter
# params:
#       node: node name (String)
#       srv : server name (String)
#       obj : stat object to analyze
#       stats_array: array to populate with PMI datas
# ----------------------------------------------------------------
def getStats( node, srv, obj, stats):
  '''
    This function takes two arguments:
      node: node name (string) for output
      srv : server name (string) for output
      obj : stat object to analyze
      stats_array : list of stats to update
  '''
  #== get SubStats for this Stat Object
  for i in obj.getSubStats():
    #== print number of statistics
    # print "\n%s.%s:%s:%s " % (node, srv, i.getName(), i.numStatistics()),
    # if there is some statistics then display them
    if i.numStatistics() > 0:
      #== get the full statistic object
      # print i.getJ2EEStatistics()
      #== for each available statistic name
      for j in i.listStatisticNames():
        # print "%s:%s:" % (srv, i.getName()),
        #== get the statistic object
        k = i.getJ2EEStatistic( j)
        #== try to print the statistic object depending on the available methods
        try:
          # print "%s.%s.%s.%s.%s.%s.%s" % (srv, i.getName(), j, k.getUnit().lower(), k.getLowerBound(), k.getUpperBound(),  k.getCurrent())
          # print "%s.%s.%s.%s.%s" % (srv, i.getName(), j, k.getUnit().lower(), k.getCurrent())
          stats_array.append( "%s.%s.%s.%s.%s.%s" % (node, srv, i.getName(), j, k.getUnit().lower(), k.getCurrent()))
        except:
          try:
            # print "%s.%s.%s.%s.%s" % (srv, i.getName(), j, k.getUnit().lower(), k.getCurrent())
            stats.append( "%s.%s.%s.%s.%s.%s" % (node, srv, i.getName(), j, k.getUnit().lower(), k.getCurrent()))
          except:
            try:
              # print "%s.%s.%s.%s.%s" % (srv, i.getName(), j, k.getUnit().lower(), k.getCount())
              stats.append( "%s.%s.%s.%s.%s.%s" % (node, srv, i.getName(), j, k.getUnit().lower(), k.getCount()))
            except:
              stats.append( "%s.%s.%s.%s ???" % (node, srv, i.getName(), j))
    # recursively analyze next level of stats (substats)
    getStats( node, srv+'.'+i.getName(), i, stats)

# ----------------------------------------------------------------
# retrieve all PMI data available
# loop for all available servers and call getStats()
# ----------------------------------------------------------------
def getAllPMI( stats):
  sigs = ['javax.management.ObjectName', 'java.lang.Boolean']
  # ----------------------------------------------------------------
  # print Cell, Nodes, Servers informations
  # ----------------------------------------------------------------
  # print "Cell:%s" % AdminControl.getCell()
  # print "Node:%s" % AdminControl.getNode()
  
  # print "Servers:" % AdminConfig.list( 'Server')
  try: 
    servers = {}
    for srv in AdminControl.queryNames( 'type=Server,*').split( lineSeparator): 
      obj = AdminControl.makeObjectName( srv)
      name = obj.getKeyProperty('name')
      node = obj.getKeyProperty('node')
      if node in servers.keys(): servers[ node].append( name)
      else: servers[ node] = [ name]
      # servers.append( AdminControl.getAttribute( s, 'name'))
    for node in servers.keys():
      # print "Servers:%s" % servers
      for server in servers[ node]: 
        # print( "found %s:%s" % ( node, server))
        # ----------------------------------------------------------------
        # Print PMI of all Servers
        # ----------------------------------------------------------------
        try:
          # get Perf MBean object name (String format)
          perfName=AdminControl.queryNames( 'type=Perf,process='+server+',*')
          # get Perf MBean object name (ObjectName format)
          perfOName = AdminControl.makeObjectName( perfName)
           
          # get server MBean object name (String format)
          srvName = AdminControl.completeObjectName ('type=Server,node=%s,process=%s,*' % (node,server))
           
          # define the params to pass to the 'getStatsObject' method: 1) srvOName 2) true (recursive mode)
          params = [AdminControl.makeObjectName( srvName), java.lang.Boolean ('true')]
          # define the types of all params
          # sigs = ['javax.management.ObjectName', 'java.lang.Boolean']
           
          # get all stats for the server using the Perf MBean
          srvStats = AdminControl.invoke_jmx (perfOName, 'getStatsObject', params, sigs)
           
          # print the stats
          getStats( node, server, srvStats, stats)
        except:
          # print_and_write( systemout, str(  sys.exc_info()))
          # traceback.print_stack()
          # traceback.print_exc(10)
          # print "%s:No stat." % server
          # stats.append( "%s:No stat." % server)
          stats.append( "----------------------------------------")
          # pass
  except:
    print_and_write( systemout, str(  sys.exc_info()))
    traceback.print_stack()
    traceback.print_exc(10)

# ----------------------------------------------------------------
# Prepare to loop according to conf.polling_occurences
# ----------------------------------------------------------------
if conf.polling_occurences > 0:
  polling_occurence = conf.polling_occurences
  polling_occurence_str = str( conf.polling_occurences)
else:
  polling_occurence = 1
  polling_occurence_str = "till the end of time..."
while polling_occurence > 0:
  # ----------------------------------------------------------------
  # initialize timer
  # ----------------------------------------------------------------
  time_start = time.time()
  # ----------------------------------------------------------------
  # open systemout_log
  # ----------------------------------------------------------------
  try: 
    systemout = open( dir_base_logs + os_sep + conf.systemout_log, 'a')
    # systemout.write('%s %s\n' % ( time.strftime('%d/%m/%Y %H:%M:%S'), '*** begin processing ***'))
    print
    print_and_write( systemout, '%s %s' % ( time.strftime('%d/%m/%Y %H:%M:%S'), '*** begin processing ***'))
    print_and_write( systemout, '%s %s (%d / %s)' % ( time.strftime('%d/%m/%Y %H:%M:%S'), '*** polling occurence', conf.polling_occurences - polling_occurence + 1, polling_occurence_str))
  except:
    print( str(  sys.exc_info()))
    error = -3
    sys.exit( error)

  # ----------------------------------------------------------------
  # retrieve PMI datas 
  # ----------------------------------------------------------------
  try:
    print_and_write( systemout, '%s %s' % ( time.strftime('%d/%m/%Y %H:%M:%S'), 'retrieving all available PMI datas started'))
    stats_all = []
    getAllPMI( stats_all)
    print_and_write( systemout, '%s %s' % ( time.strftime('%d/%m/%Y %H:%M:%S'), 'retrieving all available PMI datas finished'))
  except:
    print_and_write( systemout, '%s %s' % ( time.strftime('%d/%m/%Y %H:%M:%S'), str(  sys.exc_info())))
    error = -4
    sys.exit( error)
   
  if error == 0:
    # for stat in stats_all: print stat
    # ----------------------------------------------------------------
    # open pmi_log
    # ----------------------------------------------------------------
    # systemout.write('%s %s\n' % ( time.strftime('%d/%m/%Y %H:%M:%S'), 'output_files writing started'))
    print_and_write( systemout, '%s %s' % ( time.strftime('%d/%m/%Y %H:%M:%S'), 'output_files writing started'))

    pmi = open( dir_base_logs + os_sep + conf.pmi_log, 'w')
    systemout.write( '%s %s\n' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output ' + conf.pmi_log + " writing started"))
    for stat in stats_all: 
      pmi.write('%s\n' % stat)
      # print( stat)
    systemout.write( '%s %s\n' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output ' + conf.pmi_log + " writing finished"))
    systemout.flush()
    pmi.close()
    # -----------------------------------------------------------------------------------------------------------------------------
    # Output files according to config file
    # -----------------------------------------------------------------------------------------------------------------------------
    current_time = time.strftime('%d/%m/%Y %H:%M:%S')
    # print conf.output_files
    # try:
    #   for output in conf.output_files.keys():
    #     print("output: %s" % output)
    # except:
    #   print_and_write( systemout, str(  sys.exc_info()))
    #   traceback.print_stack()
    #   traceback.print_exc(10)
    for output in conf.output_files.keys():
      systemout.write( '%s %s\n' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output: ' + output + " starting treatment"))
      systemout.flush()
      add_header = False
      if os.path.isfile( dir_base_logs + os_sep + output) == False: add_header = True
      try:
        systemout.write( '%s %s\n' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output ' + output + ": opening file"))
        f = open( dir_base_logs + os_sep + output, 'a')
        # evaluate regex expression on multilines
        output_regex = [ regex.strip().split()[-1] for regex in conf.output_files[ output].split('\n') if regex.strip() != '']
        # evaluate label for regex expression on multilines
        output_label = [ regex.strip().split()[0] for regex in conf.output_files[ output].split('\n') if regex.strip() != '']
        systemout.write( '%s %s\n' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output ' + output + ": regex_list: " + ",".join(output_regex)))
        if add_header == True: 
          systemout.write( '%s %s\n' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output ' + output + ": adding header"))
          f.write( current_time + ";" + ";".join(output_label) + '\n')
        f.flush()
        output_pmi_list = []
        for regex in output_regex:
          systemout.write( '%s %s\n' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output ' + output + ": regex: " + regex))
          # f.write( current_time + ":" + regex + '\n')
          stats = [ x for x in stats_all if re.compile(regex, re.IGNORECASE).search(x) >= 0]
          systemout.write( '%s %s\n' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output ' + output + ": regex [" + regex + "] returns " + str( len(stats)) + " PMI"))
          if len( stats) == 1: output_pmi_list.append( stats[0].split('.')[-1])
          else : 
            output_pmi_list.append( '')
            print_and_write( systemout, '%s %s' % (time.strftime('%d/%m/%Y %H:%M:%S'), 'output ' + output + ": regex [" + regex + "] returns " + str( len(stats)) + " PMI, skipping output... WARNING check your config !"))
        # write PMI list in one line
        if len( output_pmi_list) > 0: f.write( current_time + ";" + ";".join(output_pmi_list) + '\n')
      except:
        print_and_write( systemout, str(  sys.exc_info()))
        traceback.print_stack()
        traceback.print_exc(10)
        error = -5
        sys.exit( error)
      # finally:
      f.close()
    # systemout.write('%s %s\n' % ( time.strftime('%d/%m/%Y %H:%M:%S'), 'output_files writing finished'))
    print_and_write( systemout, '%s %s' % ( time.strftime('%d/%m/%Y %H:%M:%S'), 'output_files writing finished'))

    if conf.html_on:
      # ----------------------------------------------------------------
      # check charts directory
      # ----------------------------------------------------------------
      # generate HTML files
      print_and_write( systemout, '%s %s' % ( time.strftime('%d/%m/%Y %H:%M:%S'), 'HTML files generation started'))
      try:
        total_htmls = generate_html()
      except:
        print_and_write( systemout, str(  sys.exc_info()))
        traceback.print_stack()
        traceback.print_exc(10)
      print_and_write( systemout, '%s %s (files: %d)' % ( time.strftime('%d/%m/%Y %H:%M:%S'), 'HTML files generation finished', total_htmls + 1))
    
  exec_time = time.time() - time_start          
  # systemout.write('%s %s\n' % ( time.strftime('%d/%m/%Y %H:%M:%S'), '*** end processing ***'))
  print_and_write( systemout, '%s %s (exec_time:%.2f sec)' % ( time.strftime('%d/%m/%Y %H:%M:%S'), '*** end processing***', exec_time))
  
  # ----------------------------------------------------------------
  # decrease polling_occurence and manage sleep time according to conf.polling_interval_sec
  # ----------------------------------------------------------------
  if conf.polling_occurences > 0: polling_occurence = polling_occurence - 1
  if polling_occurence > 0: 
      print_and_write( systemout, '%s %s (sleep_time:%d sec)' % ( time.strftime('%d/%m/%Y %H:%M:%S'), '...zzz... sleeping ...zzz...', conf.polling_interval_sec))
  systemout.close()
  if polling_occurence > 0: time.sleep( conf.polling_interval_sec)
    
# ----------------------------------------------------------------
# exit
# ----------------------------------------------------------------
sys.exit( error)	
