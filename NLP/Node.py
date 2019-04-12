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

from  json import dumps
import numpy as np

class Node:
    def __init__(self, parent, name='', id='', function=None):
        self.id = id
        self.name = name
        self.parent = parent
        self.functionName = function
        self.function = self.parent.functions.names[function] if function is not None else self.null
        self.extraInfo = []
        pass

    ####################################################################

    def __str__(self):
        js = self.getJson()
        return dumps(js, sort_keys=True,indent=4, separators=(',', ': '))

    ####################################################################

    def getJson(self):
        js = {
            'id': self.id,
            'name': self.name,
            'function': self.functionName,
            'extraInfo': self.extraInfo
        }
        return js

    ####################################################################

    def isMyself(self, type):
        return self if self.function({'type': type}) else None

    ####################################################################

    def nextStep(self, type):
        node = None
        myPlace = self.parent.getIndexof(self.name)
        max = 0.0
        pos = None

        # TODO hacer ciclo for para inferir nodo candidato a retornar
        for idx in self.parent.nodes:
            if self.parent.markovPrc[myPlace, idx.id] > max and self.parent.connects[myPlace, pos] != 0:
                max = self.parent.markovPrc.item[myPlace, idx.id]
                pos = idx.id

        if pos is not None:
            node = self.parent.nodes[pos]

        return node

    ####################################################################

def null(self):
        return None