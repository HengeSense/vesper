import unittest
import random
import time
import multiprocessing
import json
from urllib2 import urlopen
from urllib import urlencode

import morbid
from twisted.internet import reactor

import raccoon, rx.replication, rx.route


def invokeAPI(name, data, where=None, port=8000):
    "make a rhizome api call"
    url = "http://localhost:%d/api/%s" % (port, name)
    
    if isinstance(data, dict):
        data = json.dumps(data)
        
    post = {
        "data":data
    }
    if where:
        post['where'] = where
        
    tmp = urlopen(url, data=urlencode(post)).read()
    return json.loads(tmp)


def startMorbidQueue(port):
    print "starting morbid queue on port %d" % port
    options = {
    	'config':None,
    	'port':port,
    	'interface':'',
    	'auth':'',
    	'restq':'',
    	'verbose':True
    }
    stomp_factory = morbid.get_stomp_factory(cfg=options)
    reactor.listenTCP(options['port'], stomp_factory, interface=options['interface'])
    reactor.run()

def startRhizomeInstance(nodeId, port, queuePort, channel):
    print "creating rhizome instance:%s (%d)" % (nodeId, port)
    conf = {
        'STORAGE_URL':"mem://",
        'saveHistory':True,
        'branchId':nodeId,
        'REPLICATION_HOSTS':[('localhost', queuePort)],
        'REPLICATION_CHANNEL':channel
        
    }
    rep = rx.replication.get_replicator(nodeId, conf['REPLICATION_CHANNEL'], hosts=conf['REPLICATION_HOSTS'], autoAck=True)
    conf['DOM_CHANGESET_HOOK'] = rep.replication_hook
    
    @raccoon.Action
    def startReplication(kw, retVal):
        # print "startReplication callback!"
        rep.start(kw.__server__)
        
    conf['actions'] = {
        'http-request':rx.route.gensequence,
        'load-model':[startReplication]    
    }

    raccoon.createApp('miniserver.py',model_uri = 'test:', PORT=port, **conf).run()
    # blocks forever
    

class BasicReplicationTest(unittest.TestCase):
    
    def setUp(self):
        self.morbidQ_port   = random.randrange(5000,9999)
        self.replicationTopic = "UNITTEST" + str(random.randrange(100,999))
        self.rhizomeA_port = random.randrange(5000,9999)
        self.rhizomeB_port = random.randrange(5000,9999)
        
        self.morbidProc = multiprocessing.Process(target=startMorbidQueue, args=(self.morbidQ_port,))
        self.morbidProc.start()
        self.rhizomeA   = multiprocessing.Process(target=startRhizomeInstance, args=("AA", self.rhizomeA_port, self.morbidQ_port, self.replicationTopic))
        self.rhizomeA.start()
        self.rhizomeB   = multiprocessing.Process(target=startRhizomeInstance, args=("BB", self.rhizomeB_port, self.morbidQ_port, self.replicationTopic))
        self.rhizomeB.start()
        time.sleep(1) # XXX
        
    def tearDown(self):
        self.rhizomeA.terminate()
        self.rhizomeB.terminate()
        self.morbidProc.terminate()        
    
    def testSingleMessage(self):
        "testing single-message replication"
        # post an add to rhizomeA
        sample = {"id":"1234", "foo":"bar"}
        r = invokeAPI("add", sample, port=self.rhizomeA_port)
        
        time.sleep(1) # XXX
        # do a query on rhizomeB
        r2 = invokeAPI("query", "{*}", port=self.rhizomeB_port)
        self.assertEquals([sample], r2['results'])
        
    def testMessageSequence(self):
        "testing a simple sequence of messages"
        samples = [
            ('add', {"id":"123", "foo":"bar"}, None),
            ('add', {"id":"456", "value":"four hundred fifty six"}, None),
            ('update', {"foo":"baz"}, 'id="123"'),
            ('add', {"id":"789", "foo":"bar", "color":"green"}, None),
        ]
        expected = [{u'foo': u'baz', u'id': u'123'}, {u'color': u'green', u'foo': u'bar', u'id': u'789'}, {u'id': u'456', u'value': u'four hundred fifty six'}]
        
        # post an add to rhizomeA
        for (action, data, where) in samples:
            r = invokeAPI(action, data, where=where, port=self.rhizomeA_port)

        time.sleep(1) # XXX
        # do a query on rhizomeB
        r2 = invokeAPI("query", "{*}", port=self.rhizomeB_port)
        self.assertEquals(expected, r2['results']) # XXX is this order predictable?
        
    """
    def testClientAck(self):
        import stomp
        client_id = "testclient-" + str(random.randrange(100,999))
        
        conn = stomp.Connection([('localhost', self.morbidQ_port)])
        conn.start()
        conn.connect(headers={'client-id':client_id})
        headers = {
            'persistent':'true',
            'clientid':client_id
        }
        conn.send("foo", destination='/topic/%s' % self.replicationTopic, headers=headers)
    """
        
        
        

if __name__ == '__main__':
    unittest.main()