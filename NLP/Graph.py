# +-----------------------------------------------------------------------+
# | IMAGESTION                                                            |
# |                                                                       |
# | Copyright (C) 2010-Today, GNUCHILE.CL  -  Santiago de Chile           |
# | Licensed under the GNU GPL                                            |
# |                                                                       |
# | Redistribution and use in source and binary forms, with or without    |
# | modification, are permitted provided that the following conditions    |
# | are met:                                                              |
# |                                                                       |
# | o Redistributions of source code must retain the above copyright      |
# |   notice, this list of conditions and the following disclaimer.       |
# | o Redistributions in binary form must reproduce the above copyright   |
# |   notice, this list of conditions and the following disclaimer in the |
# |   documentation and/or other materials provided with the distribution.|
# | o The names of the authors may not be used to endorse or promote      |
# |   products derived from this software without specific prior written  |
# |   permission.                                                         |
# |                                                                       |
# | THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS   |
# | "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT     |
# | LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR |
# | A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT  |
# | OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, |
# | SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT      |
# | LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, |
# | DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY |
# | THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT   |
# | (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE |
# | OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  |
# |                                                                       |
# +-----------------------------------------------------------------------+
# | Author: Miguel Vargas Welch <miguelote@gmail.com>                     |
# +-----------------------------------------------------------------------+

import json as js
from Node import *
from Function import *
import numpy as np


class Graph:
    # node names example: nodeNames = ['DET', 'NOUN', 'ADJ', 'PREP', 'VERB', 'ADV', 'PRON', 'INTJ', 'CONJ', 'NUM', 'PUNC', 'AUX']
    def __init__(self, name='', nodes=0, id='', nodeNames=[], firstNode=0):
        n = len(nodeNames) if len(nodeNames) > 0 else nodes
        self.functions = Function(self)
        self.name = name
        self.id = id
        self.nodeNames = ["Node%d" % (x) for x in range(n)] if n > 0 else []
        self.nodeNames = nodeNames if len(nodeNames) > 0 else self.nodeNames

        self.nodes = [Node(self, id=x,
                           name="%s" % (self.nodeNames[x]),
                           function=self.getFunctionName(self.nodeNames[x]))
                      for x in range(len(self.nodeNames))] if len(self.nodeNames) > 0 else []

        self.firstNode = firstNode
        self.iterations = 0
        self.width = len(self.nodeNames)
        self.height = len(self.nodeNames)
        self.connects = np.zeros((n, n), dtype=float)
        self.factor = 0
        self.finnish = np.zeros((n, n), dtype=float)
        self.factFinnish = 0
        self.start = np.zeros((n, n), dtype=float)
        self.factStart = 0
        self.flow = []
        self.data = None

    ####################################################################

    def addNode(self, parent, name='', function='null'):
        id = None

        if not (name in self.nodeNames):
            n = len(self.nodeNames)
            id = "%s_%s" % (name, n)
            self.nodeNames.append(name)
            self.nodes.append(Node(parent, name, id, function))

        return id

    ####################################################################

    def search(self, args=None):
        #print "search: %s\n" % str(args)   #/**/
        found = []

        try:
            if args is not None and 'id' in args.keys():
                for node in self.nodes:
                    if node is not None and node.id == args['id']:
                        return [node]

            if args is not None and 'name' in args.keys():
                nodes = self.nodes if len(found) == 0 else found
                for node in nodes:
                    if node is not None and node.name == args['name']:
                        found.append(node)

            if args is not None and 'function' in args.keys():
                nodes = self.nodes if len(found) == 0 else found
                for node in nodes:
                    if node is not None and node.functionName == args['function']:
                        found.append(node)
        except ValueError:
            #print "search error: [%s]\n" % ValueError   # /**/
            return None

        return found

    ####################################################################

    def getFunctionName(self, x):
        try:
            idx = self.nodeNames.index(x)
        except ValueError:
            idx = -1

        return self.functions.dictionary[self.nodeNames[idx]] if idx is not None else 'null'

    ####################################################################

    def getIndexof(self, type):
        try:
            idx = self.nodeNames.index(type)
        except ValueError:
            idx = None

        return idx

    ####################################################################

    def goStart(self):
        node = self.nodes[self.firstNode]
        return node

    ####################################################################

    def isStart(self, typePrev, typeNext):
        y = self.getIndexof(typePrev)
        x = self.getIndexof(typeNext)

        if x is not None and y is not None:
            if self.start[y, x] > 0.0:
                return True

        return False

    ####################################################################

    def isNext(self, typePrev, typeNext):
        y = self.getIndexof(typePrev)
        x = self.getIndexof(typeNext)

        if x is not None and y is not None:
            if self.connects[y, x] > 0.0:
                return True

        return False

    ####################################################################

    def isFinnish(self, typePrev, typeNext):
        y = self.getIndexof(typePrev)
        x = self.getIndexof(typeNext)

        if x is not None and y is not None:
            if self.finnish[y, x] > 0.0:
                return True

        return False

    ####################################################################

    def getFinnishByTags(self, typePrev, typeNext):
        y = self.getIndexof(typePrev)
        x = self.getIndexof(typeNext)

        if x is not None and y is not None:
            return self.finnish[y, x]

        return None

    ####################################################################

    def reset(self):
        self.flow = []
        self.data = None

    ####################################################################

    def setInit(self, type):
        self.flow = [type]

    ####################################################################

    def setNext(self, type):
        self.flow.append(type)

    ####################################################################

    def load(self, dbFile):
        f = open(dbFile, 'r')
        json = f.read()
        f.close()
        self.importJSON(json)
        pass

    ####################################################################

    def save(self, dbFile):
        with open(dbFile, "w") as text_file:
            text_file.write(self.__str__())
        pass

    ####################################################################

    def __str__(self):
        json = self.getJson()
        return js.dumps(json, sort_keys=True, indent=4, separators=(',', ': '))

    ####################################################################

    def getConnection(self, y, x, matrix=None):
        return self.connects.item((y, x)) if matrix is None else matrix.connects.item((y, x))

    ####################################################################

    def setConnection(self, y, x, val, matrix=None):
        #print "setConnection(%d, %d)\n" % (y, x)   #/**/
        if matrix is not None:
            matrix.itemset((y, x), val)
        else:
            self.connects.itemset((y, x), val)

    ####################################################################

    def getConnectRow(self, y, matrix=None):
        return self.connects[y, :] if matrix is None else matrix.connects[y, :]

    ####################################################################

    def getConnectColumn(self, x, matrix=None):
        return self.connects[:, x] if matrix is None else matrix.connects[:, x]

    ####################################################################

    def getStart(self, y, x):
        return self.start.item((y, x))

    ####################################################################

    def setStart(self, y, x, val):
        self.start.itemset((y, x), val)

    ####################################################################

    def getStartRow(self, y):
        return self.start[y, :]

    ####################################################################

    def getStartColumn(self, x):
        return self.start[:, x]

    ####################################################################

    def getFinnish(self, y, x):
        return self.finnish.item((y, x))

    ####################################################################

    def getFinnishRow(self, y):
        return self.finnish[y, :]

    ####################################################################

    def getFinnishColumn(self, x):
        return self.finnish[:, x]

    ####################################################################

    def setFinnish(self, y, x, val):
        self.finnish.itemset((y, x), val)

    ####################################################################

    def getConnectionsNode(self, node, matrix=None):
        col = self.getConnectColumn(node.id, matrix)
        nodes = []

        for i in xrange(col):
            if col[i] > 0:
                nodes.append(self.nodes[i])

        return nodes

    ####################################################################

    def getEntriesNode(self, node, matrix=None):
        row = self.getConnectRow(node.id, matrix)
        nodes = []

        for i in xrange(row):
            if row[i] > 0:
                nodes.append(self.nodes[i])

        return nodes

    ####################################################################

    def getJson(self):
        json = {
            'graph': {
                'id': self.id,
                'name': self.name,
                'nodeNames': self.nodeNames,
                'first': self.firstNode,
                'factor': self.factor,
                'factorFinnish': self.factFinnish,
                'factorStart': self.factStart,
                'iterations': self.iterations,
                'width': self.width,
                'height': self.height,
                'connects': self.connects.tolist(),
                'finnish': self.finnish.tolist(),
                'start': self.start.tolist(),
                'nodes': [node.id for node in self.nodes]
            },
            'functions': [self.functions.getJson()],
            'nodes': [node.getJson() for node in self.nodes]
        }
        return json

    ####################################################################

    def importJSON(self, json):
        data = js.loads(json)
        self.importData(data)

    ####################################################################

    def importData(self, data):
        self.id = data['graph']['id']
        self.name = data['graph']['name']
        self.firstNode = data['graph']['first']
        self.iterations = data['graph']['iterations']
        self.factor = data['graph']['factor']
        self.factFinnish = data['graph']['factorFinnish']
        self.factStart = data['graph']['factorStart']
        self.width = data['graph']['width']
        self.height = data['graph']['height']
        self.connects = np.array(data['graph']['connects'], dtype=float)
        self.finnish = np.array(data['graph']['finnish'], dtype=float)
        self.start = np.array(data['graph']['start'], dtype=float)
        self.nodeNames = data['graph']['nodeNames']
        self.nodes = [Node(self, id=node['id'], name=node['name'], 
                           function=self.getFunctionName(node['name']))
                           for node in data['nodes']
                     ] if len(self.nodeNames) > 0 else []
