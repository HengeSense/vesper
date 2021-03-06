#:copyright: Copyright 2009-2010 by the Vesper team, see AUTHORS.
#:license: Dual licenced under the GPL or Apache2 licences, see LICENSE.
import unittest
from pprint import pprint,pformat

from vesper.pjson import *
from vesper.utils import pprintdiff
from vesper.data import base

def assert_json_match(expected, result, dosort=False):
    if dosort and isinstance(expected, list):
        result.sort()
        expected.sort()
    result = json.dumps(result,sort_keys=True)
    expected = json.dumps(expected, sort_keys=True)
    assert result == expected, pprint((result, '!=', expected))

def assert_stmts_match(expected_stmts, result_stmts):
    assert set(result_stmts) == set(expected_stmts), pprintdiff(
                        result_stmts,expected_stmts)

    if not base.graph_compare(expected_stmts, result_stmts):
        print 'graph_compare failed'
        ge = base.Graph(expected_stmts)
        gr = base.Graph(result_stmts)
        print pprintdiff(ge._hashtuple(), gr._hashtuple())
        #print 'expected _:2', base.Graph(expected_stmts).vhash('_:2')
        #print 'expected _:1', base.Graph(expected_stmts).vhash('_:1')
        #print 'result _:1', base.Graph(result_stmts).vhash('_:1')
        #print 'result _:2', base.Graph(result_stmts).vhash('_:2')
        assert False

def assert_json_and_back_match(src, backagain=True, expectedstmts=None, 
    includesharedrefs=False, intermediateJson=None, serializerOptions=None, 
                                                        parserOptions=None):
    global test_counter; test_counter += 1
    serializerOptions = serializerOptions or {}
    parserOptions = parserOptions or {}
    if 'serializeIdAsRefs' not in serializerOptions:
        serializerOptions['serializeIdAsRefs'] = False
    if isinstance(src, (str,unicode)):
        test_json = json.loads(src)
        if not test_json.get('pjson'):
            test_json = [test_json]
    else:
        test_json = src
    result_stmts = Parser(generateBnode='counter', **parserOptions).to_rdf( test_json)[0]
    #print 'results_stmts'
    #pprint( result_stmts)
    if expectedstmts is not None:
        assert_stmts_match(expectedstmts, result_stmts)
    
    serializer = Serializer(**serializerOptions)
    hash(serializer)
    result_json = serializer.to_pjson( result_stmts)
    if 'nameMap' not in serializerOptions:
        result_json = result_json['data']
    #pprint( result_json )
    if intermediateJson:
        test_json = intermediateJson
    assert_json_match(result_json, test_json)
    if backagain:
        test_counter -= 1
        assert_stmts_and_back_match(result_stmts,
            serializerOptions=serializerOptions, parserOptions=parserOptions)

def assert_stmts_and_back_match(stmts, expectedobj = None, 
                        serializerOptions=None, parserOptions=None):
    global test_counter; test_counter += 1                        
    serializerOptions = serializerOptions or {}
    serializer = Serializer(**serializerOptions)
    hash(serializer)    
    result = serializer.to_pjson( stmts )
    #print 'serialized', result
    if expectedobj is not None:
        if 'nameMap' not in serializerOptions:
            compare = result['data']
        else:
            compare = result
        assert_json_match(expectedobj, compare, True)
    
    parserOptions = parserOptions or {}
    result_stmts = Parser(generateBnode='counter', **parserOptions).to_rdf( result )[0]
    assert_stmts_match(stmts, result_stmts)

class SjsonTestCase(unittest.TestCase):
    def testAll(self):
        test()
        
def test():
    global test_counter;
    
    dc = 'http://purl.org/dc/elements/1.1/'
    r1 = "http://example.org/book#1";     
    r2 = "http://example.org/book#2"; 
    stmts = [
    Statement(r1, dc+'title', u"SPARQL - the book",OBJECT_TYPE_LITERAL,''),
    Statement(r1, dc+'description', u"A book about SPARQL",OBJECT_TYPE_LITERAL,''),
    Statement(r2, dc+'title', u"Advanced SPARQL",OBJECT_TYPE_LITERAL,''),
    ]
    
    expected =[{'http://purl.org/dc/elements/1.1/description': 'A book about SPARQL',
            'http://purl.org/dc/elements/1.1/title': 'SPARQL - the book',
            'id': '@http://example.org/book#1'},
            {'http://purl.org/dc/elements/1.1/title': 'Advanced SPARQL',
            'id': '@http://example.org/book#2'}]
    
    assert_stmts_and_back_match(stmts, expected)
        
    stmts.extend( 
        [Statement("http://example.org/book#2", 'test:sequelto' , 'http://example.org/book#1', OBJECT_TYPE_RESOURCE),]
    )

    expected = [{"http://purl.org/dc/elements/1.1/title": "Advanced SPARQL",
    "id": "@http://example.org/book#2",
    "test:sequelto": {
        "http://purl.org/dc/elements/1.1/description": "A book about SPARQL",
        "http://purl.org/dc/elements/1.1/title": "SPARQL - the book",
        "id": "@http://example.org/book#1"
        }
    }]
    assert_stmts_and_back_match(stmts, expected)
    assert_stmts_and_back_match(stmts, parserOptions=dict(addOrderInfo=False))

    src = '''
    { "id" : "atestid",
       "foo" : { "id" : "bnestedid", "prop" : "value" }
    }'''
    assert_json_and_back_match(src)

    src = '''
    { "id" : "atestid2",
       "foo" : { "id" : "bnestedid", "prop" : "@ref" }
    }'''
    assert_json_and_back_match(src)

    src = '''
    { "id" : "testid", 
    "foo" : ["1","3"],
     "bar" : [],
     "baz" : {  "id": "_:j:e:object:testid:1", 
                "nestedobj" : { "id" : "anotherid", "prop" : "value" }}
    } 
    '''
    assert_json_and_back_match(src)
    
    src = '''
    { "id" : "testid",
    "baz" : { "id": "_:j:e:object:testid:1", 
               "nestedobj" : { "id" : "anotherid", "prop" : "value" }},
    "foo" : ["1","3"],
     "bar" : []
    } 
    '''
    assert_json_and_back_match(src)

    #test nested lists and dups
    src = '''
    { "id" : "testid",
    "foo" : [1,  1, ["nested1",
                       { "id": "nestedid", "nestedprop" : [ "nested3" ] },
                    "nested2"], 1,
            3],
    "bar" : [ [] ],
    "one" : [1]
    }
    '''
    assert_json_and_back_match(src)

    #test numbers and nulls
    src = '''
    { "id" : "test",
    "float" : 1.0,
      "integer" : 2,
      "null" : null,
      "list" : [ 1.0, 2, null, 0, -1],
      "created": 1262662188016
    }
    '''
    assert_json_and_back_match(src)

    #test circular references
    src = '''
    { "id" : "test",
      "circular" : "@test",
      "not a reference" : "test",
      "circularlist" : ["@test", "@test"],
      "circularlist2" : [["@test"],["@test", "@test"]]
    }
    '''
    assert_json_and_back_match(src)

    #test a custom ref pattern 
    #and then serialize with the same pattern
    #they should match
    src = r'''
    { "pjson" : "%s",
    "namemap" : { "refpattern" : "ref:(\\w+)"},
    "data" :[{ "id" : "test",
     "circular" : "ref:test",
     "not a reference" : "@test",
      "circularlist" : ["ref:test", "ref:test"],
      "circularlist2" : [["ref:test"],["ref:test", "ref:test"]]
        }]
    }
    ''' % VERSION
    serializerNameMap={ "refpattern" : "ref:(\\w+)"}
    assert_json_and_back_match(src, 
            serializerOptions= {'nameMap' : serializerNameMap})

    #add statements that are identical to the ones above except they have
    #different object types (they switch a resource (object reference) for literal
    #and vice-versa)
    stmts.extend( 
        [Statement("http://example.org/book#2", 'test:sequelto' , 
            'http://example.org/book#1', OBJECT_TYPE_LITERAL),
         Statement(r2, dc+'title', u"Advanced SPARQL",OBJECT_TYPE_RESOURCE,''),
        ]
    )
    
    assert_stmts_and_back_match(stmts, parserOptions=dict(addOrderInfo=False))
    
    src = dict(namemap = dict(id='itemid', namemap='jsonmap'),
    itemid = 1,
    shouldBeARef = '@hello', #default ref pattern is @(URIREF)
    value = dict(jsonmap=dict(id='anotherid', refpattern=''), #disable matching
            anotherid = 2,
            #XXX fix assert key != self.ID, (key, self.ID) when serializing
            #id = 'not an id', #this should be treated as a regular property
            innerobj = dict(anotherid = 3, shouldBeALiteral='@hello2'),
            shouldBeALiteral='@hello')
    )
    #expect different output because we nested namemaps when serializing
    #and because ids are coerced to strings
    intermediateJson = [{"id": "1", "shouldBeARef": "@hello", 
            "value": {"id": "2", 
                "innerobj": {"id": "3", 
                            "shouldBeALiteral": {"datatype": "json", "value": "@hello2"}
                            }, 
                "shouldBeALiteral": {"datatype": "json", "value": "@hello"}
                }
            }]
    assert_json_and_back_match(src, intermediateJson=intermediateJson)

    namemap = {
        "id" : "itemid",
        "$ref" : "ref"
    }
    src = { "pjson" : "%s" % VERSION,
    "namemap" : namemap,
    "data" :[{ "itemid" : "1", "foo" : { 'ref' : "1"}
    }]
    }     
    assert_json_and_back_match(src, serializerOptions= dict(nameMap=namemap,
                                                    explicitRefObjects = True))

    #test ref defaults when a regex and replace pattern isn't specified:
    namemap = { 
        "refpattern" : { 'rdf:' : 'http://www.w3.org/1999/02/22-rdf-syntax-ns#' }
    }    
    src = { "pjson" : "%s" % VERSION,
    "namemap" : namemap,
    "data" :[{ "id" : "1", "type" : 'rdf:List' }]
    }
    expectedStmts = [Statement("1", "type", "http://www.w3.org/1999/02/22-rdf-syntax-ns#List",OBJECT_TYPE_RESOURCE,'')]
    assert_json_and_back_match(src, expectedstmts=expectedStmts, serializerOptions= dict(nameMap=namemap))

    #test props 
    namemap = { 
        "sharedpatterns" : { 'rdf:' : 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',          
         },         
         "propertypatterns" : { '': 'http://myschema.com#' },
         "idpatterns" : { '': 'http://example.com/instanceA#' },
         "refpattern": "@((::)?URIREF)"
    }
    src = { "pjson" : "%s" % VERSION,
    "namemap" : namemap,
    "data" :[
        { 
        "id" : "1", 
        'myprop' : "a",
        "rdf:type" : '@::foo',
        "::rdf:type" : '@b',
        "::::doublecolonprop" : "c"
        }
    ]
    }
    expectedStmts = [
        Statement("http://example.com/instanceA#1", "http://myschema.com#myprop", 'a', OBJECT_TYPE_LITERAL,''),
        Statement("http://example.com/instanceA#1", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",'foo', OBJECT_TYPE_RESOURCE,''),
        Statement("http://example.com/instanceA#1", "rdf:type", 'http://example.com/instanceA#b', OBJECT_TYPE_RESOURCE,''),
        Statement("http://example.com/instanceA#1", "::doublecolonprop", 'c', OBJECT_TYPE_LITERAL,''),
    ]
    assert_json_and_back_match(src, expectedstmts=expectedStmts, serializerOptions= dict(nameMap=namemap))
    
    stmts = [
       Statement("1", "id", "a property, not an id", "L")
    ]
    src = [{ "id" : "1", 
            "::id" : "a property, not an id"}]
    assert_json_and_back_match(src, expectedstmts=stmts)

    namemap = { 
      "id" : "oid",
       "refpattern": "@((::)?URIREF)"
    }    
    src = { "pjson" : "%s" % VERSION,
    "namemap" : namemap,
    "data" :[ { "oid" : "1", 
                 "id" : "a property, not an id"}]
    }
    assert_json_and_back_match(src, expectedstmts=stmts, serializerOptions= dict(nameMap=namemap))
    
    namemap = { 
    "sharedpatterns" : { '(type|List)': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#' },
    "refpattern": "<(URIREF)>",
    }
    src = { "pjson" : "%s" % VERSION,
    "namemap" : namemap,    
    "data" : [{
        'id' : '1',
        'type' : '<List>'
        }]
    }
    stmts = [Statement("1", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
     'http://www.w3.org/1999/02/22-rdf-syntax-ns#List', OBJECT_TYPE_RESOURCE,'')]
    assert_json_and_back_match(src, expectedstmts=stmts, serializerOptions= dict(nameMap=namemap))
    
    namemap = { 
    "refpattern": "<(URIREF)>",
    "propertypatterns" : { 
        '': 'http://myschema.com#',
        'a()' : "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" },
    }
    src = { "pjson" : "%s" % VERSION,
    "namemap" : namemap,        
    "data" : [{
        'id' : '1',
        'a' : '<foo>',
        'another' : "bar"
        }]
    }
    stmts = [Statement('1', 'http://myschema.com#another', 'bar', 'L', ''),
     Statement('1', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'foo', 'R', '')]
    assert_json_and_back_match(src, expectedstmts=stmts, serializerOptions= dict(nameMap=namemap))

    #test id parsing
    result_stmts = tostatements('{"id":"@::foo", "a":"b"}')
    assert_stmts_match(result_stmts, [('foo', 'a', 'b', 'L', '')])

    result_stmts = tostatements('{"id":"::@foo", "a":"b"}')
    assert_stmts_match(result_stmts, [('@foo', 'a', 'b', 'L', '')])

    result_stmts = tostatements('{"id":"@foo", "a":"b"}')
    assert_stmts_match(result_stmts, [('foo', 'a', 'b', 'L', '')])
    
    src = [{
     'id' : '::@1',
     'self_ref' : { '$ref' : '::@1' }
    }]
    expectedStmts =  [Statement('@1', 'self_ref', '@1', 'R', '')]
    assert_json_and_back_match(src, expectedstmts=expectedStmts)    
    #############################################
    ################ scope/context tests
    #############################################
    
    src = [{"id": "1",
      "context" : "context1",
      "prop1": 1,
      "prop2": ["@a_ref", "a value"]
    }]
    
    stmts = set([('1', 'pjson:schema#propseq', 'bnode:j:proplist:1;prop2', 'R', 'context1'),
    ('1', 'prop1', u'1', 'http://www.w3.org/2001/XMLSchema#integer', 'context1'),
    StatementWithOrder('1', 'prop2', 'a value', 'L', 'context1', (1,)),
    StatementWithOrder('1', 'prop2', 'a_ref', 'R', 'context1', (0,)),
    ('bnode:j:proplist:1;prop2', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#_1', 'a_ref', 'R', 'context1'),
    ('bnode:j:proplist:1;prop2', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#_2', 'a value', 'L', 'context1'),
    ('bnode:j:proplist:1;prop2', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#Seq', 'R', 'context1'),
    ('bnode:j:proplist:1;prop2', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'pjson:schema#propseqtype', 'R', 'context1'),
    ('bnode:j:proplist:1;prop2', 'pjson:schema#propseqprop', 'prop2', 'R', 'context1'),
    ('bnode:j:proplist:1;prop2', 'pjson:schema#propseqsubject', '1', 'R', 'context1')])
        
    assert set(Parser().to_rdf(src)[0]) == stmts
    assert_json_and_back_match(src)

    src = [{"id": "1",
      "context" : "context1",
      "prop1": 1,
      "prop2": ["a_ref", 
                { 'context' : 'context2', 'prop3' : None, "id": "_:j:e:object:1:1"}
               ],
     'prop4' : { 'datatype' : 'json', 'value' : 'hello', 'context' : 'context3'}
    }]
    assert_json_and_back_match(src)

    src = [{
      "pjson": "0.9", 
      "namemap": {
        "refpattern": "@(URIREF)"
      },
      'context' : 'scope1'
    },
    {
      'id' : 'id1',
      'prop1': 1,
      'prop2': "@ref"
    },
    {
      "pjson": "0.9", 
      'context' : ''
    },    
    {
      'id' : 'id1', #note: same id
      'prop1': 1,
      'prop2': "@ref"
    },    
    ]
    assert_json_and_back_match(src, False, 
    [('id1', 'prop1', u'1', 'http://www.w3.org/2001/XMLSchema#integer', 'scope1'),
     ('id1', 'prop2', 'ref', 'R', 'scope1'),
     ('id1', 'prop1', u'1', 'http://www.w3.org/2001/XMLSchema#integer', ''),
      ('id1', 'prop2', 'ref', 'R', '')     
     ],    
    intermediateJson=[{"id": "id1", "prop1": [1, {"context": "scope1", 
        "datatype": "json",         
        "value": 1}], 
      "prop2": [ "@ref", {"context": "scope1", "$ref": "ref"}]
      }],
     parserOptions=dict(checkForDuplicateIds=False)
    )

    src = [{
       'id' : 'resource1',
       "value" : "not in a scope",
      "type":         
        {          
          "context": "context:add:context:txn:http://pow2.local/;0A00001;;", 
          "$ref": "post"
        }
      , 
      "content-Type":         
        {
          "datatype": "json", 
          "context": "context:add:context:txn:http://pow2.local/;0A00001;;", 
          "value": "text/plain"
        }      
     }]
    #XXX note intermediateJson: not ideal but correct   
    assert_json_and_back_match(src, intermediateJson=[{
    "content-Type": "text/plain", 
    "context": "context:add:context:txn:http://pow2.local/;0A00001;;", 
    "id": "resource1", 
    "type": "@post", 
    "value": {"context": "", "datatype": "json", "value": "not in a scope"}}]) 

    #test duplicate statements but in different scopes
    src = [{ 'id' : 'id1', 
       "value" : "not in a scope",
      "type": [
        "@post", 
        {
          "context": "context:add:context:txn:http://pow2.local/;0A00001;;", 
          "$ref": "post"
        }
      ], 
      "content-Type": [
        "text/plain", 
        {
          "datatype": "json", 
          "context": "context:add:context:txn:http://pow2.local/;0A00001;;", 
          "value": "text/plain"
        }
      ]
     }]
    assert_json_and_back_match(src) 
        
    #test exclude
    src = [
     {
      "pjson": "0.9", 
      "namemap": {
         'exclude' : ['prop1']
      }
    },
    {
      'id' : "1",
      'prop1': 1,
      'prop2': 2
    },    
    ]
    intermediateJson = [{ 'id' : "1", 'prop2': 2 }]
    assert_json_and_back_match(src, intermediateJson=intermediateJson)

    namemap = {
        "datatypepatterns" : { "date" : r'(\d\d\d\d-\d\d-\d\d)' },
         "refpattern": "@((::)?URIREF)"
    }
    src = {
        "pjson": "0.9",
        "namemap": namemap,
        "data" : [ {
            "id" : "1", 
            "property1" : "2010-04-01",
            "property2" : "not a date"
        } ] 
    }
    expectedStmts =  [Statement('1', 'property1', '2010-04-01', 'pjson:date', ''),
        Statement('1', 'property2', 'not a date', 'L', '')]            
    assert_json_and_back_match(src, serializerOptions=dict(nameMap=namemap), 
                                                expectedstmts=expectedStmts)

    #assert_stmts_and_back_match(stmts, addOrderInfo=False)

    #these statements are from a model where an empty propseq list was hiding a statement
    stmts = [Statement(*t) for t in [('bnode:j:proplist:tag:another%20tag;subsumedby', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 
    u'http://www.w3.org/1999/02/22-rdf-syntax-ns#Seq', 'R', ''), 
    ('bnode:j:proplist:tag:another%20tag;subsumedby', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'pjson:schema#propseqtype', 'R', ''), 
    ('bnode:j:proplist:tag:another%20tag;subsumedby', 'pjson:schema#propseqprop', 'subsumedby', 'R', ''),
    ('bnode:j:proplist:tag:another%20tag;subsumedby', 'pjson:schema#propseqsubject', 'tag:another%20tag', 'R', ''), 
    ('scrapple', 'label', 'scrapple', 'L', ''), 
    ('scrapple', 'type', 'tag', 'R', ''), 
    ('tag:another%20tag', 'label', 'another tag', 'L', ''), 
    ('tag:another%20tag', 'pjson:schema#propseq', 'bnode:j:proplist:tag:another%20tag;subsumedby', 'R', ''),
    ('tag:another%20tag', 'subsumedby', 'tag:more%20tagging', 'R', ''), 
    ('tag:another%20tag', 'type', 'tag', 'R', ''), 
    ('tag:more%20tagging', 'label', 'more tagging', 'L', ''), 
    ('tag:more%20tagging', 'type', 'tag', 'R', '')]]
    assert tojson(stmts, onlyEmbedBnodes=True) == {'pjson': '0.9',
    'namemap': {'refpattern': '@((::)?URIREF)'},
    'data':  [
    {'subsumedby': '@tag:more%20tagging', 'type': '@tag', 'id': '@tag:another%20tag', 'label': 'another tag'},
    {'type': '@tag', 'id': '@scrapple', 'label': 'scrapple'}, {'type': '@tag', 'id': '@tag:more%20tagging', 'label': 'more tagging'}] 
    }
    
    #similar to the previous test but add two unlisted statements with a non-empty propseq list 
    #instead of one statement with an emtpy list
    json = {
      "id" : "1",
      "prop" : [1,2,3,4]
    }
    stmts = tostatements(json)
    stmts.append( Statement('1', 'prop', 'foo', 'R', '')  )
    stmts.append( Statement('1', 'prop', 'bar', 'R', '')  )
    assert tojson(stmts, asList=True) == [{'pjson': '0.9', 'namemap': {'refpattern': '@((::)?URIREF)'}}, {'id': '@1', 'prop': [1, 2, 3, 4, '@bar', '@foo']}]
    
    src = [
     {
      "pjson": "0.9", 
      "namemap": {
         "refpattern": "@(URIREF)"
      }
    },
    {
      'id' : "1",
      'prop1': "@"
    },    
    ]
    intermediateJson = [{ 'id' : "1", 'prop1': "@" }]
    assert_json_and_back_match(src, intermediateJson=intermediateJson)
    
    src = [{
      'id' : "duplicate1",
      'prop1': 'test'
    },
    { 'id' : '2', 
    'nested' : {
      'id' : "duplicate1",
      'prop2': 'test'
    }
    }]
    try:
        assert_json_and_back_match(src)
    except:
        pass
    else:
        assert 0, "duplicate id detection failed"

    #test that serialize still works even if there are missing propseq statements
    # this statement is missing from the statement below:
    # _:j:proplist:uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a;tags <http://www.w3.org/1999/02/22-rdf-syntax-ns#_2> <tag:tag1> .      
    import StringIO
    stream = StringIO.StringIO('''<uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a> <tags> <tag:tag1> .
<uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a> <type> <post> .
<uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a> <pjson:schema#propseq> _:j:proplist:uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a;tags .
_:j:proplist:uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a;tags <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/1999/02/22-rdf-syntax-ns#Seq> .
_:j:proplist:uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a;tags <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <pjson:schema#propseqtype> .
_:j:proplist:uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a;tags <pjson:schema#propseqprop> <tags> .
_:j:proplist:uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a;tags <pjson:schema#propseqsubject> <uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a> .
_:j:proplist:uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a;tags <http://www.w3.org/1999/02/22-rdf-syntax-ns#_1> <tag:tag2> .
<uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a> <tags> <tag:tag2> .''')
    stmts = base.NTriples2Statements(stream)
    
    assert tojson( stmts )['data'] == [{'id': '@uuid:1eb500bb-ce42-49b2-a0dd-af5abb7d520a', 
                  'tags': ['@tag:tag2', '@tag:tag1'],
                  'type': '@post'
          }]
    test_counter += 1
    
    print 'ran %d tests, all pass' % test_counter
    
test_counter = 0

if __name__  == "__main__":
    test()
