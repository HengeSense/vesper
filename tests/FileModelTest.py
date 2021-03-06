#:copyright: Copyright 2009-2010 by the Vesper team, see AUTHORS.
#:license: Dual licenced under the GPL or Apache2 licences, see LICENSE.
"""
    File model unit tests
"""
import unittest
import subprocess, tempfile, os, sys, traceback
import string, random, shutil, time

import modelTest 
from vesper.data.base import Statement
from vesper.data.store.basic import FileStore, TransactionFileStore, IncrementalNTriplesFileStore, IncrementalNTriplesFileStoreBase

class FileModelTestCase(modelTest.BasicModelTestCase):
    
    EXT = 'json' #also supported: rdf, nt, nj, yaml, mjson
    
    persistentStore = True
    
    def getModel(self):
        #print 'opening', self.tmpfilename
        #sys.stdout.flush()
        model = FileStore(self.tmpfilename)
        return model #self._getModel(model)

    def getTransactionModel(self):
        model = FileStore(self.tmpfilename)
        return model #self._getModel(model)

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="vespertest."+self.EXT)
        self.tmpfilename = os.path.join(self.tmpdir, 'test.'+self.EXT) 
        
    def tearDown(self):
        #print 'tear down removing', self.tmpdir
        shutil.rmtree(self.tmpdir)

    def testCommitFailure(self):
        "test commit transaction isolation across 2 models"
        modelA = self.getTransactionModel()

        #include spaces in value so it looks like a literal, not a resource
        statements = [Statement("one", "equals", " one "),
                      Statement("two", "equals", " two "),
                      Statement("three", "equals", " three ")]

        # confirm models are empty
        r1a = modelA.getStatements()
        self.assertEqual(set(), set(r1a))

        # add statements and confirm A sees them and B doesn't
        modelA.addStatements(statements)
        r2a = modelA.getStatements()
        self.assertEqual(set(r2a), set(statements))

        # commit A and confirm both models see the statements
        modelA.commit()

        more =  [
        Statement('s', 'p1', 'o2', 'en-1', 'c1'),
        Statement('s', 'p1', 'o1', 'en-1', 'c2'),
        Statement('s2', 'p1', 'o2', 'en-1', 'c2'),
        ]
        modelA.addStatements(more)
        
        try:
            #make commit explode            
            modelA.serializeOptions = dict(badOption=1)
            modelA.commit()
        except:
            self.assertTrue("got expected exception")
        else:
            self.assertFalse('expected exception during commit')

        #reload the data, should be equal to first commit (i.e. file shouldn't have been corrupted)
        modelC = self.getTransactionModel()
        r3c = modelC.getStatements()
        self.assertEqual(set(statements), set(r3c))
    
    def testExternalChange(self):
        model = self.getModel()
        model.getStatements() #begin a txn
        overwriteString = '{"id":"foo","hello":"world"}'
        def overwrite():
            f = open(model.path, 'w')
            f.write(overwriteString)
            f.close()
        overwrite() 
        model.addStatement(Statement('a', 'a', ''))
        try:
            model.commit()
        except:            
            self.assertTrue("got expected exception")
        else:
            self.assertFalse('expected exception during commit')

        model.reload()        
        stmts = model.getStatements()
        #should be from the overwritten file
        self.assertEqual(stmts, [Statement('foo', 'hello', 'world')])
        model.addStatement(Statement('b', 'b', ''))
        #add some whitespace to change the file size because some file systems 
        #(e.g. HFS+ and FAT) have low resolution (1 and 2 second) last modified times
        overwriteString = '{"id":"foo","hello":"world" }'
        overwrite()
        try:
            model.commit()
        except:
            self.assertTrue("got expected exception")
        else:
            self.assertFalse('expected exception during commit')
        self.assertEqual(open(model.path).read(), overwriteString)
        
class MultipartJsonFileModelTestCase(FileModelTestCase):
    EXT = 'mjson' 

class SerializationOptions(unittest.TestCase):
    
    def testEmbeddedBnodeSerialization(self):
        tmpdir = tempfile.mkdtemp(prefix="vespertest")
        try:
            tmpfilename = os.path.join(tmpdir, 'test.json') 
            pjsonfile = open(tmpfilename,'w')
            pjsonfile.write('''
            [{
            "id" : "foo",
            "prop" : { "id" : "bnode:j:e:object:foo:x07c332751f8043a49c5b091768e97c375", 
                        "label" : "test1" 
                     }
            },
            {
              "id": "bnode:j:t:object:x07c332751f8043a49c5b091768e97c371", 
              "tags": [
                {             
                  "id": "bnode:j:e:object:bnode:j:t:object:x07c332751f8043a49c5b091768e97c371:x07c332751f8043a49c5b091768e97c372", 
                  "label": "test2"
                }
              ]
            }]
            ''')
            pjsonfile.close()
            model = FileStore(tmpfilename)
            model.addStatement(Statement('foo', 'prop2', ''))
            model.commit()
            contents = open(tmpfilename).read()
            expected = ('{"pjson": "0.9", "data": [{"id": "@bnode:j:t:object:x07c332751f8043a49c5b091768e97c371", '
            '"tags": [{"label": "test2"}]}, {"id": "@foo", "prop2": "", "prop": {"label": "test1"}}],'
            ' "namemap": {"refpattern": "@((::)?URIREF)"}}')
            self.assertEqual(expected, contents)
        finally:
            shutil.rmtree(tmpdir)

try:
    import rdflib
    from vesper.data.store.rdflib_store import RDFLibFileModel, TransactionalRDFLibFileModel

    class RDFFileModelTestCase(FileModelTestCase):
        EXT = 'rdf' 

        def getModel(self):
            #print 'opening', self.tmpfilename
            #sys.stdout.flush()
            model = RDFLibFileModel(self.tmpfilename)
            return model 

        def getTransactionModel(self):
            model = TransactionalRDFLibFileModel(self.tmpfilename)
            return model 

        def testExternalChange(self):
            pass #XXX store should support this functionality

        def testCommitFailure(self):
            pass #XXX enable this test (need a different way to force commit to fail)

except ImportError:
    print 'skipping rdflib store tests, rdflib not installed'
    
class TransactionFileModelTestCase(FileModelTestCase):

    def getTransactionModel(self):
        model = TransactionFileStore(self.tmpfilename)
        return model#self._getModel(model)

class IncrementalFileModelTestCase(FileModelTestCase):

    EXT = 'nt' #XXX EXT = 'json' fails because model uses the default writeTriples
    
    def getModel(self):
        #print 'opening', self.tmpfilename
        #sys.stdout.flush()
        model = IncrementalNTriplesFileStoreBase(self.tmpfilename)
        return model#self._getModel(model)

    def getTransactionModel(self):
        model = IncrementalNTriplesFileStoreBase(self.tmpfilename)
        return model#self._getModel(model)
    
    def testCommitFailure(self):
        pass #this test needs to be disabled for IncrementalNTriplesFileStore

    def testExternalChange(self):
        pass #XXX override overwriteString in test with one compatible with this model
    
    def testLogfileRecovery(self):
        model = self.getModel()
        stmts = [Statement('s', 'p1', 'o1')]
        model.addStatements(stmts)
        model.commit() #create the file
        f = open(model.path)
        expectedFileContents = '<s> <p1> "o1" .'
        self.assertEqual(expectedFileContents, f.read().strip()) #strip trailing newline
        f.close()
        
        model.addStatement(Statement('s', 'p2', 'o2'))
        #make comitting explode right when we are writing to disk:
        changelist = model._getChangeList()
        changelist.append((0,1,3)) 
        try:
            model.commit()
        except:
            self.assertTrue("got expected exception")
        else:
            self.assertFalse('expected exception during commit')
        
        #make sure old contents is preserved in file
        f = open(model.path)
        self.assertEqual(expectedFileContents, f.read().strip()) #strip trailing newline
        f.close()        
        
class TransactionIncrementalFileModelTestCase(IncrementalFileModelTestCase):

    def getModel(self):
        model = IncrementalNTriplesFileStore(self.tmpfilename)
        return model#self._getModel(model)

    def getTransactionModel(self):
        model = IncrementalNTriplesFileStore(self.tmpfilename)
        return model#self._getModel(model)

if __name__ == '__main__':
    modelTest.main(FileModelTestCase)
