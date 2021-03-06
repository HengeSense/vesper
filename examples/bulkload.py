#!/usr/bin/env python
#:copyright: Copyright 2009-2010 by the Vesper team, see AUTHORS.
#:license: Dual licenced under the GPL or Apache2 licences, see LICENSE.
import raccoon
from optparse import OptionParser
from datetime import datetime

try:
    import json
except ImportError:
    import simplejson as json

_LOAD=None
_DUMP=None

QUERY = "{*}"
# QUERY = """{
# 'installid' : <appdir:installation_id>,
# 'name': <appdir:name>,
# 'value': <appdir:value>,
# groupby(<appdir:installation_id>)
# }
# """

@raccoon.Action
def testaction(kw, retval):
    datastore = kw['__server__'].dataStore
    
    starttime = datetime.now()
    try:
        if _LOAD:
            f = open(_LOAD, 'r')
            data = json.load(f)
            datastore.add(data) # update is very slow for this use case
            print "data loaded from", _LOAD
        else:
            print "opening", _DUMP
            f = open(_DUMP, 'w')
            data = datastore.query(QUERY)
            if 'errors' in data:
                print " ERROR "
                for x in data['errors']:
                    print x
            res = data['results']
            json.dump(res, f, sort_keys=True, indent=4)
            f.close()
            print "data dumped to", _DUMP

    except Exception, e:
        raise e

    elapsed = datetime.now() - starttime
    print "operation completed in %s" % str(elapsed)
    return 'foo'

actions = {
  'run-cmds' : [testaction]
}

parser = OptionParser("usage: %prog [options] storage_url")
parser.add_option("-l", "--load", dest="load", help="load data from file")
parser.add_option("-d", "--dump", dest="dump", help="dump data to file")
(options, args) = parser.parse_args()

if len(args) > 0:
    storage_url = args[0]
else:
    parser.error("storage_url required")
    
_LOAD=options.load
_DUMP=options.dump
if not _LOAD and not _DUMP:
    parser.error("Must specify either a load or a dump file")

CONF = {
    'storage_url':storage_url,
    'actions':actions,
    'exec_cmd_and_exit': True
}

app = raccoon.createApp(**CONF).run()
