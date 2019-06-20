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
import sys

import numpy as np
import json as js
from GrammarRules import *
from Graph import *
from time import sleep
import re
import thread
import zlib

# http://chriskiehl.com/article/parallelism-in-one-line/
#from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

# https://sebastianraschka.com/Articles/2014_multiprocessing.html
import multiprocessing as mp

class SemanticNetwork:
    """
            "inf"  : "infinitivo",
            "ger"  : "gerundio",
            "par"  : "participio",
            "ip"   : "indicativo presente" ,
            "ipi"  : "indicativo preterito imperfecto" ,
            "if"   : "indicativo futuro" ,
            "ic"   : "indicativo condicional",
            "ipps" : "indicativo preterito perfecto simple",
            "i"    : "imperativo" ,
            "sp"   : "subjuntivo presente" ,
            "spi"  : "subjuntivo preterito imperfecto" ,
            "spi2" : "subjuntivo preterito imperfecto 2" ,
            "sf"   : "subjuntivo futuro"
    """
    def __init__(self, db_file=None):
        self.dbLangRules = db_file
        self.rules = GrammarRules(db_file=self.dbLangRules)
        self.grammarTypes = ['DET', 'NOUN', 'ADJ', 'PREP', 'VERB', 'ADV', 'PRON', 'INTJ', 'CONJ', 'NUM', 'PUNC', 'AUX']
        self.verbTenses = ['inf', 'ger', 'par', 'ip', 'ipi', 'if', 'ic', 'ipps', 'i', 'sp', 'spi', 'spi2', 'sf']
        self.pronouns = ['yo', 'tu', 'el_la', 'nos', 'uds', 'ellos']
        self.nouns = ['sustPropio',   'sustSimple',   'sustCompuesto', 'sustDespectivo', 'sustDisminutivo',
                      'sustDerivado', 'sustAbstract', 'sustColectivo', 'sustAll',        'sustComun',        'undefined']
        self.workflow = Graph(name='workflow', nodeNames=self.grammarTypes)
        self.nucleous = np.zeros((len(self.grammarTypes), len(self.grammarTypes)), dtype=float)
        self.prevVerb = np.zeros((len(self.grammarTypes), len(self.verbTenses)),   dtype=float)
        self.postVerb = np.zeros((len(self.verbTenses),   len(self.grammarTypes)), dtype=float)
        self.pronVerb = np.zeros((len(self.verbTenses),   len(self.pronouns)),     dtype=float)
        self.nounVerb = np.zeros((len(self.verbTenses),   len(self.nouns)),        dtype=float)
        self.endCondition = {}
        
        self.factVerb = 0
        self.factPreVerb = 0
        self.factPosVerb = 0
        self.factPronVrb = 0
        self.factNounVrb = 0
        self.factCondition = 0
        self.fileDb = None
        self.busy = None

        self.actionList = ['null']
        self.actionFunc = Function(self)
        self.actionFunc.names = {
            'null': self.actionFunc.null
        }
        self.actionFunc.dictionary = {
            'null': 'null'
        }
        self.net = Graph(name='net') #, nodeNames=self.actionList)
        self.net.functions = self.actionFunc
        self.actions = np.chararray((1, 1), itemsize=30)
        self.actions[:] = ''
        self.text = {}
        pass

    ####################################################################
    # TODO se pretende implementar mismas funcionalidades aplicando librerias NLP de Google
    # TODO actualizar pip para python a la version 10.0.1 (pip install --upgrade pip)
    #      luego:   pip install --upgrade google-cloud-language


    #########################################################################
    # train( oracion, verbo )
    # Este algoritmo se encarga de entrenar para identificar el verbo raiz
    # usa mas de una matriz para ponderar la prevalencia y postvalencia de
    # las distintas funciones semanticas que vienen antes del verbo raiz y
    # despues del verbo raiz, generando una matriz de probabilidades donde
    # una funcion predice un verbo raiz.
    # Retorna una matriz con la probabilidad ponderada para las condiciones
    # de termino de una oracion
    #########################################################################
    def train(self, text, root):
        connects = np.zeros((len(self.grammarTypes), len(self.grammarTypes)), dtype=float)
        finnish  = np.zeros((len(self.grammarTypes), len(self.grammarTypes)), dtype=float)
        start    = np.zeros((len(self.grammarTypes), len(self.grammarTypes)), dtype=float)
        nucleous = np.zeros((len(self.grammarTypes), len(self.grammarTypes)), dtype=float)
        prevVerb = np.zeros((len(self.grammarTypes), len(self.verbTenses)),   dtype=float)
        postVerb = np.zeros((len(self.verbTenses),   len(self.grammarTypes)), dtype=float)
        pronVerb = np.zeros((len(self.verbTenses),   len(self.pronouns)),     dtype=float)
        nounVerb = np.zeros((len(self.verbTenses),   len(self.nouns)),        dtype=float)
        endCondition = {}

        self.rules.setText(text)
        tokens = self.rules.normalize(self.rules.getSyntax(text))
        length = len(tokens)
        i = 0

        verb = self.rules.getVerb(root)
        tense = self.rules.getVerbTense(verb, root)
        pron = self.rules.getVerbPron(verb, root)
        z = self.getIndexof(tense, self.verbTenses)
        w = self.getIndexof(pron, self.pronouns)
        prevType = None
        lastType = None
        prevWord = None
        lastWord = None

        for token in tokens:
            i += 1
            word = token[0]
            type = token[1]
            nextWord = tokens[i][0] if i < length else None
            nextType = tokens[i][1] if i < length else None
            #nextType = self.rules.validType(nextType, tokens[i+1][1] if i+1 < length else None)
            #type = self.rules.validType(type, nextType)

            if nextType is not None and type is not None:
                print ("m[%s,%s]   \t\t{ %s (%s), %s (%s) }") % (type, nextType, word, self.rules.getIndexFromType(type, word), nextWord, self.rules.getIndexFromType(nextType, nextWord))
                y = self.getIndexof(type, self.grammarTypes)
                x = self.getIndexof(nextType, self.grammarTypes)
                prevType = type
                lastType = nextType
                prevWord = word
                lastWord = nextWord

                connects[y, x] += 1

                if i == 1:
                    start[y, x] += 1

                if word == root:
                    print ("postVerb[%s,%s] -> %s {%s, %s(%s: %s)}") % (type, nextType, root, nextType, tense, verb, self.rules.rules['_comment'][tense])
                    nucleous[y, x] += 1
                    postVerb[x, z] += 1
                    pronVerb[z, w] += 1
                elif nextWord == root:
                    print ("prevVerb[%s,%s] -> %s {%s(%s: %s), %s}") % (type, nextType, root, tense, verb, self.rules.rules['_comment'][tense], type)
                    nucleous[y, x] += 1
                    prevVerb[z, y] += 1
                elif type == 'NOUN':
                    noun = self.rules.isNoun(word)
                    noun = 'undefined' if noun is None else noun
                    v = self.getIndexof(noun, self.nouns)
                    print ("noun[%s,%s] -> {%s (%s: %s), %s}") % (tense, noun, root, verb, self.rules.rules['_comment'][tense], pron)
                    nounVerb[z, v] += 1

        #print ("[%s,%s]") % (prevType,lastType)
        if prevType is not None and lastType is not None:
            y = self.getIndexof(prevType, self.grammarTypes)
            x = self.getIndexof(lastType, self.grammarTypes)
            finnish[y, x] += 1

            idY = self.rules.getIndexFromType(prevType, prevWord)
            idX = self.rules.getIndexFromType(lastType, lastWord)
            key = "%s_%s" % (idY, idX)
            endCondition[key] = endCondition[key] + 1.0 if key in endCondition else 1.0

        listCnt = np.concatenate((connects.sum(axis=1), connects.sum(axis=0)), axis=0)
        listFin = np.concatenate((finnish.sum(axis=1),  finnish.sum(axis=0)),  axis=0)
        listStr = np.concatenate((start.sum(axis=1),    start.sum(axis=0)),    axis=0)
        listNuc = np.concatenate((nucleous.sum(axis=1), nucleous.sum(axis=0)), axis=0)
        listPsV = np.concatenate((postVerb.sum(axis=1), postVerb.sum(axis=0)), axis=0)
        listPrV = np.concatenate((prevVerb.sum(axis=1), prevVerb.sum(axis=0)), axis=0)
        listPrn = np.concatenate((pronVerb.sum(axis=1), pronVerb.sum(axis=0)), axis=0)
        listNnV = np.concatenate((nounVerb.sum(axis=1), nounVerb.sum(axis=0)), axis=0)
        listEnd = np.array(endCondition.values())

        maxCnt = listCnt.max()
        maxFin = listFin.max()
        maxStr = listStr.max()
        maxNuc = listNuc.max()
        maxPsV = listPsV.max()
        maxPrV = listPrV.max()
        maxPrn = listPrn.max()
        maxNnV = listNnV.max()
        maxEnd = listEnd.max()

        newMatrixCnt = connects/maxCnt if maxCnt > 0 else connects
        newMatrixFin = finnish/maxFin  if maxFin > 0 else finnish
        newMatrixStr = start/maxStr    if maxStr > 0 else start
        newMatrixNuc = nucleous/maxNuc if maxNuc > 0 else nucleous
        newPrevVerb  = prevVerb/maxPrV if maxPrV > 0 else prevVerb
        newPostVerb  = postVerb/maxPsV if maxPsV > 0 else postVerb
        newPronVerb  = pronVerb/maxPrn if maxPrn > 0 else pronVerb
        newNounVerb  = nounVerb/maxNnV if maxNnV > 0 else nounVerb
        newCondition = endCondition

        if maxEnd > 0:
            for idx in endCondition.keys():
                newCondition[idx] = endCondition[idx]/maxEnd

        oldMatrixCnt = self.workflow.connects
        oldMatrixFin = self.workflow.finnish
        oldMatrixStr = self.workflow.start
        oldMatrixNuc = self.nucleous
        oldPrevVerb  = self.prevVerb
        oldPostVerb  = self.postVerb
        oldPronVerb  = self.pronVerb
        oldCondition = self.endCondition

        oldNounVerb  = self.nounVerb
        oldFactorCnt = self.workflow.factor
        oldFactorFin = self.workflow.factFinnish
        oldFactorStr = self.workflow.factStart
        oldFactorNuc = self.factVerb
        oldFactorPrV = self.factPreVerb
        oldFactorPsV = self.factPosVerb
        oldFactPrnVrb = self.factPronVrb
        oldFactNnVrb = self.factNounVrb
        oldFactCondition = self.factCondition

        if oldMatrixCnt.max() == 0:
            newFactorCnt = maxCnt
            newFactorFin = maxFin
            newFactorStr = maxStr
            newFactorNuc = maxNuc
            newFactorPrV = maxPrV
            newFactorPsV = maxPsV
            newFactPrnVrb = maxPrn
            newFactNnVrb = maxNnV
            newFactCondition = maxEnd
        else:
            newFactorCnt  = maxCnt + oldFactorCnt
            newFactorFin  = maxFin + oldFactorFin
            newFactorStr  = maxFin + oldFactorStr
            newFactorNuc  = maxNuc + oldFactorNuc
            newFactorPrV  = maxPrV + oldFactorPrV
            newFactorPsV  = maxPsV + oldFactorPsV
            newFactPrnVrb = maxPrn + oldFactPrnVrb
            newFactNnVrb  = maxNnV + oldFactNnVrb
            newFactCondition = maxEnd + oldFactCondition

            newMatrixCnt = (oldMatrixCnt * oldFactorCnt) + connects
            newMatrixFin = (oldMatrixFin * oldFactorFin) + finnish
            newMatrixStr = (oldMatrixStr * oldFactorStr) + start
            newMatrixNuc = (oldMatrixNuc * oldFactorNuc) + nucleous
            newPrevVerb  = (oldPrevVerb * oldFactorPrV)  + prevVerb
            newPostVerb  = (oldPostVerb * oldFactorPsV)  + postVerb
            newPronVerb  = (oldPronVerb * oldFactPrnVrb) + pronVerb
            newNounVerb  = (oldNounVerb * oldFactNnVrb)  + nounVerb

            for idx in oldCondition.keys():
                oldValue = oldCondition[idx] if idx in oldCondition.keys() else 0.0
                newValue = endCondition[idx] if idx in endCondition.keys() else 0.0
                newCondition[idx] = oldValue * oldFactCondition + newValue
                newCondition[idx] = newCondition[idx]/newFactCondition if newFactCondition > 0 else newCondition[idx]

            newMatrixCnt = newMatrixCnt/newFactorCnt if newFactorCnt > 0  else newMatrixCnt
            newMatrixFin = newMatrixFin/newFactorFin if newFactorFin > 0  else newMatrixFin
            newMatrixStr = newMatrixStr/newFactorStr if newFactorStr > 0  else newMatrixStr
            newMatrixNuc = newMatrixNuc/newFactorNuc if newFactorNuc > 0  else newMatrixNuc
            newPrevVerb  = newPrevVerb/newFactorPrV  if newFactorPrV > 0  else newPrevVerb
            newPostVerb  = newPostVerb/newFactorPsV  if newFactorPsV > 0  else newPostVerb
            newPronVerb  = newPronVerb/newFactPrnVrb if newFactPrnVrb > 0 else newPronVerb
            newNounVerb  = newNounVerb/newFactNnVrb  if newFactNnVrb > 0  else newNounVerb

        self.workflow.iterations += 1
        self.workflow.connects = newMatrixCnt
        self.workflow.finnish = newMatrixFin
        self.workflow.start = newMatrixStr
        self.nucleous = newMatrixNuc
        self.prevVerb = newPrevVerb
        self.postVerb = newPostVerb
        self.pronVerb = newPronVerb
        self.nounVerb = newNounVerb
        self.endCondition = newCondition
        self.workflow.factor = newFactorCnt
        self.workflow.factFinnish = newFactorFin
        self.workflow.factStart = newFactorStr
        self.factVerb = newFactorNuc
        self.factPreVerb = newFactorPrV
        self.factPosVerb = newFactorPsV
        self.factPronVrb = newFactPrnVrb
        self.factNounVrb = newFactNnVrb
        self.factCondition = newFactCondition

        if self.fileDb is not None:
            self.save(self.fileDb)

        return finnish

    ####################################################################

    def getJson(self):
        json = {
            'workflow': self.workflow.getJson(),
            'nucleous': self.nucleous.tolist(),
            'prevVerb': self.prevVerb.tolist(),
            'postVerb': self.postVerb.tolist(),
            'pronVerb': self.pronVerb.tolist(),
            'nounVerb': self.nounVerb.tolist(),
            'endCondition': self.endCondition,
            'factVerb': self.factVerb,
            'factPreVerb': self.factPreVerb,
            'factPosVerb': self.factPosVerb,
            'factPronVrb': self.factPronVrb,
            'factNounVrb': self.factNounVrb,
            'factCondition': self.factCondition
        }

        return json

    ####################################################################

    def __str__(self):
        return js.dumps(self.getJson(), sort_keys=True, indent=4, separators=(',', ': '))

    ####################################################################
    def printJson(self, var):
        return js.dumps(var, sort_keys=True, indent=4, separators=(',', ': '))

    ####################################################################

    def save(self, dbFile):
        with open(dbFile, "w") as text_file:
            text_file.write(self.__str__())

    ####################################################################

    def importJSON(self, json):
        data = js.loads(json)
        self.workflow.importData(data['workflow'])
        self.factVerb = data['factVerb']
        self.factPreVerb = data['factPreVerb']
        self.factPosVerb = data['factPosVerb']
        self.factPronVrb = data['factPronVrb']
        self.factNounVrb = data['factNounVrb']
        self.factCondition = data['factCondition']
        self.nucleous = np.array(data['nucleous'], dtype=float)
        self.prevVerb = np.array(data['prevVerb'], dtype=float)
        self.postVerb = np.array(data['postVerb'], dtype=float)
        self.pronVerb = np.array(data['pronVerb'], dtype=float)
        self.nounVerb = np.array(data['nounVerb'], dtype=float)
        self.endCondition = data['endCondition']

    ####################################################################

    def load(self, dbFile):
        self.fileDb = dbFile
        f = open(self.fileDb, 'r')
        json = f.read()
        f.close()
        self.importJSON(json)

    ####################################################################

    def addProcess(self, args={}):
        i = args['i']
        out = args['out']
        txt = args['txt']
        tokens = self.rules.normalize(self.rules.getSyntax(txt))
        struct = self.getSyntaxStruct(txt, tokens)
        out.put((i, struct))
        #print ("(%d) %s ") % (i, str(struct))


    ####################################################################
    # analize(texto)
    # Recibe una oracion, analiza su semantica y retorna una lista de posibles
    # estructuras (sugeto, nucleo y predicado)

    def analize(self, text):
        txt = re.sub(r'[.]', ' .', text)
        txt = re.sub(r'\n{2,}', ' .\r', txt)
        txt = re.sub(r'\n', ' ', txt)
        txt = re.sub(r'\r', '\n', txt)
        expr = re.compile(r'[^.]+')
        list = expr.findall(txt)
        out = mp.Queue()
        lsOut = []
        processes = []
        self.busy = 0
        pool = ThreadPool(4)

        if len(list) > 0:
            for txt in list:
                processes.append({'i': self.busy, 'out': out, 'txt': txt})
                print ("%d %s ") % (self.busy, txt)
                self.busy += 1

            results = pool.map(self.addProcess, processes)

            lsOut = [out.get() for p in results]
            lsOut.sort()
            lsOut = [o[1] for o in lsOut]
        else:
            tokens = self.rules.normalize(self.rules.getSyntax(text))
            struct = self.getSyntaxStruct(text, tokens)
            lsOut.append(struct)

        return lsOut

    ####################################################################

    def isNucleous(self, typePrev, typeNext):
        y = self.workflow.getIndexof(typePrev)
        x = self.workflow.getIndexof(typeNext)

        if x is not None and y is not None:
            if self.nucleous[y, x] > 0.0:
                return True

        return False

    ####################################################################

    def isPreVerb(self, type, tense):
        y = self.getIndexof(type, self.grammarTypes)
        x = self.getIndexof(tense, self.verbTenses)

        if x is not None and y is not None:
            if self.prevVerb[y, x] > 0.0:
                return True

        return False
        #value = self.getPreVerb(type, tense)
        #return True if value is not None and value > 0.0 else False

    ####################################################################

    def setPreVerb(self, type, tense, n):
        y = self.getIndexof(type, self.grammarTypes)
        x = self.getIndexof(tense, self.verbTenses)

        if x is not None and y is not None:
            self.prevVerb[y, x] = n

    ####################################################################

    def getPreVerb(self, type, tense):
        x = self.getIndexof(type, self.grammarTypes)
        y = self.getIndexof(tense, self.verbTenses)

        return self.prevVerb[y, x] if x is not None and y is not None else None

    ####################################################################

    def isPostVerb(self, tense, type):
        y = self.getIndexof(type, self.grammarTypes)
        x = self.getIndexof(tense, self.verbTenses)

        if x is not None and y is not None:
            if self.postVerb[y, x] > 0.0:
                return True

        return False
        #value = self.getPostVerb(type, tense)
        #return True if value is not None and value > 0.0 else False

    ####################################################################

    def setPostVerb(self, type, tense, n):
        y = self.getIndexof(tense, self.verbTenses)
        x = self.getIndexof(type, self.grammarTypes)

        if x is not None and y is not None:
            self.postVerb[y, x] = n

    ####################################################################

    def getPostVerb(self, type, tense):
        y = self.getIndexof(tense, self.verbTenses)
        x = self.getIndexof(type, self.grammarTypes)

        return self.postVerb[y, x] if x is not None and y is not None else None

    ####################################################################

    def isFinnish(self, typePrev, typeNext):
        value = self.getFinnish(typePrev, typeNext)
        return True if value is not None and value > 0.0 else False

    ####################################################################

    def getFinnish(self, typePrev, typeNext):
        y = self.getIndexof(typePrev, self.grammarTypes)
        x = self.getIndexof(typeNext, self.grammarTypes)

        if x is not None and y is not None:
            return self.workflow.getFinnish(y, x)

        return None

    ####################################################################

    def setFinnish(self, typePrev, typeNext, n):
        y = self.getIndexof(typePrev, self.grammarTypes)
        x = self.getIndexof(typeNext, self.grammarTypes)

        if x is not None and y is not None:
            self.workflow.setFinnish(y, x, n)

    ####################################################################

    def getIndexof(self, type, arr):
        try:
            idx = arr.index(type)
        except ValueError:
            idx = None

        return idx

    ####################################################################
    # getSyntaxStruct(texto, tokens)
    # Recorre una lista de tokens {palabra,tipo} donde busca y evalua la
    # identificacion del verbo nucleo y separar el sugeto del predicado.
    # retorna una lista de estructuras (sujeto, nucleo, predicado y los tokens)

    def getSyntaxStruct(self, text, tokens):
        structs = []
        lenght = len(tokens)
        instances = []
        limit = 10
        prev = None
        post = None
        prevToken = None
        postToken = None
        i = 0
        idx = 0
        #self.busy += 1

        for token in tokens:
            # TODO hacer ciclo que recorra token por token buscando probabilidad de que un flujo de proseso se cumpla
            #      y abrir mas de una instancia de proceso en caso de que un patron de inicio se detecte y descartar el
            #      resto cuando una instancia respete un flujo completo. Construir estructura y retornarla.
            post = token[1]
            word = token[0]

            if i > 0:
                beyond = tokens[i+1][1] if i+1 < lenght else None
                prev = self.rules.validType(prev, post)
                post = self.rules.validType(post, beyond)
                isStart = self.workflow.isStart(prev, post)
                postToken = token

                if isStart and idx < limit:
                    newGraph = Graph()
                    newGraph.importData(self.workflow.getJson())
                    newGraph.id = i
                    newGraph.setInit(prev)
                    newGraph.data = {
                        'text': text,
                        'root': '',
                        'subject': [prevToken],
                        'predicate': [],
                        'tokens': tokens
                    }
                    instances.append(newGraph)
                    idx = len(instances)

                for flow in instances:
                    isNext = flow.isNext(prev, post)
                    isFinnish = flow.isFinnish(prev, post) and flow.data is not None

                    if isNext:
                        flow.setNext(post)
                        if flow.data is not None:
                            if flow.data['root'] == '':
                                flow.data['subject'].append(token)
                            else:
                                flow.data['predicate'].append(token)

                        precondition = self.isNucleous(prev, post)
                        postcondition = self.isNucleous(post, beyond)
                        isNucleous = precondition and postcondition and post == 'VERB' and flow.data is not None

                        if isNucleous:
                            verb = self.rules.getVerb(word)
                            flow.data['root'] = word
                            # TODO: resolver problemas para identificar nucleo y diferenciar conjuncion de verbo para algunas palabras
                            # if verb is not None and flow.data is not None:
                            #     tense = self.rules.getVerbTense(verb, word)
                            #     pron = self.rules.getVerbPron(verb, word)
                            #     preVerb = self.getPreVerb(prev, tense)
                            #     postVerb = self.getPostVerb(beyond, tense)
                            #
                            #     # TODO: agregar condiciones de noun x verb para identificar el nucleo
                            #     if preVerb > 0 and postVerb > 0:
                            #         flow.data['root'] = word
                            #         for f in instances:
                            #             if f.data['root'] is not None:
                            #                 f.reset()
                            #                 idx -= 1
                            # pass

                        elif isFinnish:
                            axisX = self.workflow.finnish.sum(axis=1)
                            xMax = axisX.max()
                            value = flow.getFinnishByTags(prev, post)
                            isValidValue = True #if value is not None and value >= xMax else False

                            if isValidValue:
                                # TODO: limitar retorno de None, no es capaz de identificar fin de oracion, tal vez falta de vocabulario para diferenciar NOUNs de otros tipos
                                prevWord = prevToken[0]
                                postWord = postToken[0]
                                idY = self.rules.getIndexFromType(prev, prevWord)
                                idX = self.rules.getIndexFromType(post, postWord)
                                key = "%s_%s" % (idY, idX)
                                isCondition = self.endCondition[key] if key in self.endCondition.keys() else 0

                                if flow.data['root'] != '' and isCondition > 0:
                                    structs.append(flow.data)
                                    for f in instances:
                                        f.reset()
                    else:
                        flow.reset()
                        if flow.isStart(prev, post):
                            flow.setInit(prev)
                            flow.setNext(post)
                            flow.data = {
                                'text': text,
                                'root': '',
                                'subject': [prevToken, token],
                                'predicate': [],
                                'tokens': tokens
                            }
                    pass
                pass

            instances = [flow for flow in instances if flow.data is not None]

            i += 1
            prev = post
            prevToken = token

        self.busy -= 1

        return structs

    ####################################################################

    def makeSemanticNetwork(self, tokens):
        aux = None
        verb = None
        prep = None
        noun = None
        punc = None
        thisNoun = None
        prevNoun = None
        lastNoun = None
        conj = None
        det = None
        lastTag = None
        text = []
        tags = []
        words = []
        nouns = []
        #textId = 1.0 * len(self.text)
        textId = abs(round(100 * (1.0*zlib.crc32(bytes(self.text))/2**32), 4))

        # try:
        for token in tokens:
            (word, tag, type) = token
            text.append(word)

            if tag == 'DET':
                det = word
                tags.append(tag)
                words.append(word)

            if tag == 'PUNC':
                punc = word
                tags.append(tag)
                words.append(word)

            if tag == 'CONJ':
                conj = word if self.rules.isConjunction(word) == 'conjCopulative' else None
                tags.append(tag)
                words.append(word)

            if tag == 'PREP':
                prep = None if self.rules.isPreposition(word) is None else word
                tags.append(tag)
                words.append(word)

            if tag == 'AUX':
                aux = self.rules.getVerb(word)
                aux = None if self.rules.isAuxiliar(aux) is None else word
                tags.append(tag)
                words.append(word)

            if self.rules.isVerb().match(word):
                if self.rules.getVerb(word) is not None:
                    tag = 'VERB'

            if tag == 'VERB':
                verb = word
                tags.append(tag)
                words.append(word)

            if tag == 'NOUN':
                noun = "%s %s" % (lastNoun, word) if lastTag == 'NOUN' else word
                tags.append(tag)
                words.append(word)

                if thisNoun is None:
                    thisNoun = noun
                    verb = None
                    prep = None
                    aux = None
                elif punc is not None and re.search(',|:', punc):
                    nouns.append(lastNoun)
                    nouns.append(noun)
                    thisNoun = noun
                    punc = ''
                elif conj is not None and re.search('y|e', conj):
                    nouns.append(lastNoun)
                    nouns.append(noun)
                    prevNoun = thisNoun
                    thisNoun = noun
                    conj = ''
                else:
                    prevNoun = thisNoun
                    thisNoun = noun

                node = self.net.search({'name': thisNoun}) if thisNoun is not None and tag == 'NOUN' else None

                if node is not None and len(node) == 0:
                    self.addNode(thisNoun)

                lastNoun = noun

            if thisNoun is not None and prevNoun is not None and verb is not None:
                if len(nouns) > 0:
                    prevNoun = nouns.pop(0)
                    while prevNoun in nouns:
                        idx = nouns.index(prevNoun)
                        nouns.pop(idx)

                    while len(nouns) > 0:
                        thisNoun = nouns.pop(0)
                        self.connectNode(prevNoun, thisNoun, tags, words, args={
                            'det': det,
                            'noun': noun,
                            'verb': verb,
                            'prep': prep,
                            'aux': aux,
                            'conj': conj,
                            'textId': textId
                        })

                    prevNoun = None
                    thisNoun = None
                    tags = []
                    words = []
                elif self.connectNode(prevNoun, thisNoun, tags, words, args={
                    'det': det,
                    'noun': noun,
                    'verb': verb,
                    'prep': prep,
                    'aux': aux,
                    'conj': conj,
                    'textId': textId
                }):
                    prevNoun = None
                    thisNoun = None
                    tags = []
                    words = []
                else:
                    prevNoun = thisNoun
                    thisNoun = None

                det = None
                noun = None
                verb = None
                prep = None
                aux = None
                conj = None

            lastTag = tag

        txt = ' '.join(text)
        if txt not in self.text:
            self.text[str(textId)] = txt

        # except ValueError:
        #     print ("makeSemanticNetwork error: [%s]\n%s\n") % (ValueError, str(self.getSemanticNetwork()))
        pass

    ####################################################################

    def linkPlurals(self):
        l = len(self.net.nodeNames)
        for i in range(0, l):
            str1 = self.net.nodeNames[i]
            for j in range(i+1, l):
                if j < l:
                    str2 = self.net.nodeNames[j]
                    type1 = self.rules.isNoun(str1)
                    type2 = self.rules.isNoun(str2)
                    if str1 != str2 and type1 is not None and type2 is not None and type1 == type2:
                        if re.search('^'+str1, str2):
                            o = self.net.getIndexof(str2)
                            d = self.net.getIndexof(str1)
                            textId = self.net.getConnection(o, d, matrix=self.net.connects)

                            self.connectNode(str2, str1, [], [], args={
                                'det': None,
                                'noun': None,
                                'verb': 'es',
                                'prep': None,
                                'aux': None,
                                'conj': None,
                                'textId': textId
                            })
                        if re.search('^'+str2, str1):
                            o = self.net.getIndexof(str2)
                            d = self.net.getIndexof(str1)
                            textId = self.net.getConnection(o, d, matrix=self.net.connects)

                            self.connectNode(str1, str2, [], [], args={
                                'det': None,
                                'noun': None,
                                'verb': 'es',
                                'prep': None,
                                'aux': None,
                                'conj': None,
                                'textId': textId
                            })

    ####################################################################

    def connectNode(self, prevNoun, thisNoun, tags, words, args={}):
        origin = self.net.search({'name': prevNoun})
        destiny = self.net.search({'name': thisNoun})

        (prep, aux, verb, det, textId) = [args['prep'], args['aux'], args['verb'], args['det'], args['textId']]

        prep = "%s %s" % (prep, det) if re.search('PREP DET', ' '.join(tags)) else prep
        verb = "%s %s" % (aux, verb) if re.search('AUX VERB', ' '.join(tags)) else verb
        verb = "%s %s" % (verb, prep) if re.search('VERB (PREP\s?)+', ' '.join(tags)) else verb

        print (">>\t%s\n\t%s") % (' '.join(tags), ' '.join(words))
        print ("\t%s --(%s)--> %s\n") % (prevNoun, verb, thisNoun)

        if verb not in self.actionList:
            self.actionList.append(verb)
            self.actionFunc.dictionary[verb] = 'null'

        if origin is not None and destiny is not None and len(origin) > 0 and len(destiny) > 0:
            o = self.net.getIndexof(origin[0].name)
            d = self.net.getIndexof(destiny[0].name)
            self.net.setConnection(o, d, textId, matrix=self.net.connects)
            self.net.setConnection(o, d, verb, matrix=self.actions)
            return True
        else:
            return False


    ####################################################################

    def addNode(self, thisNoun):
        node = self.net.addNode(self.net, name=thisNoun)
        n = len(self.net.nodeNames)
        arr1 = np.copy(self.net.connects)
        (m, l) = arr1.shape
        self.net.connects = np.zeros((n, n), dtype=float)
        self.net.connects[:m, :l] = arr1
        arr2 = np.copy(self.actions)
        self.actions = np.chararray((n, n), itemsize=30)
        self.actions[:] = ''
        self.actions[:m, :l] = arr2

        return node

    ####################################################################

    def getSemanticNetwork(self):
        connects = []
        actions = []
        (Y, X) = self.net.connects.shape

        for y in range(0, Y):
            for x in range(0, X):
                if self.net.connects[y, x] > 0:
                    connects.append([y, x, self.net.connects[y, x]])

        for y in range(0, Y):
            for x in range(0, X):
                if self.actions[y, x] != '':
                    actions.append([y, x, self.actions[y, x]])

        copy = np.copy(self.net.connects)
        self.net.connects = np.array(())

        json = {
            'width': X,
            'height': Y,
            'net': self.net.getJson(),
            'actions': actions,
            'connects': connects,
            'contentList': self.text
        }

        self.net.connects = np.copy(copy)

        return json

    ####################################################################

    def saveSemanticNetwork(self, file):
        json = self.getSemanticNetwork()
        with open(file, "w") as text_file:
            text_file.write(js.dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))

    ####################################################################

    def loadSemanticNetwork(self, dbFile):
        self.fileDb = dbFile
        f = open(self.fileDb, 'r')
        json = f.read()
        f.close()
        self.importSemanticNetwork(json)

    ####################################################################

    def importSemanticNetwork(self, json):
        data = js.loads(json)
        self.net = Graph(name='net')
        width = data['width']
        height = data['height']
        self.text = data['contentList']
        self.actions = np.chararray((width, height), itemsize=30)
        self.actions[:] = ''
        self.net.functions = self.actionFunc
        self.net.connects = np.zeros((width, height), dtype=float)

        for node in data['net']['nodes']:
            pNode = self.net.addNode(self.net, name=node['name'])
            if pNode is not None:
                pNode.extraInfo = node['extraInfo']

        for action in data['actions']:
            (y, x, txt) = action
            self.actions[y, x] = txt

        for connect in data['connects']:
            (y, x, val) = connect
            self.net.connects[y, x] = val

    ####################################################################

    def select(self, topic, data=None):
        node = self.net.search({'name': topic})
        json = {
            'width': None,
            'height': None,
            'net': None,
            'actions': [],
            'connects': [],
            'contentList': {}
        }

        if len(node) > 0:
            inputs = self.net.getEntriesNode(node[0], self.net)
            outputs = self.net.getConnectionsNode(node[0], self.net)
            connects = []
            lstAction = []
            net = Graph(name='net')
            net.functions = self.actionFunc
            all = inputs + outputs
            all.append(node[0])

            for item in all:
                pNode = net.addNode(net, name=item.name)
                if pNode is not None:
                    pNode.extraInfo = item.extraInfo

            size = len(net.nodeNames)
            actions = np.chararray((size, size), itemsize=30)
            actions[:] = ''
            net.connects = np.zeros((size, size), dtype=float)
            json['width'] = size
            json['height'] = size

            idN = self.net.getIndexof(node[0].name)
            n = net.getIndexof(node[0].name)
            try:
                for item in inputs:
                    #print ("item: %s\n" % item.name)
                    x = net.getIndexof(item.name)
                    idX = self.net.getIndexof(item.name)
                    val = self.net.connects[idN, idX]
                    #print ("value(%s, %s): %s\n" % (idN, idX, val))
                    net.connects[n, x] = val
                    actions[n, x] = self.actions[idN, idX]

                    #if str(val) in self.text:
                    json['contentList'][str(val)] = self.text[str(val)]
            except KeyError:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print("ERROR SemanticNetwork.select()[%s]: %s; value:%s\n" % (exc_tb.tb_lineno , str(KeyError), str(val)))

            for item in outputs:
                y = net.getIndexof(item.name)
                idY = self.net.getIndexof(item.name)
                val = self.net.connects[idY, idN]
                net.connects[y, n] = val
                actions[y, n] = self.actions[idY, idN]
                json['contentList'][str(val)] = self.text[str(val)]

            for y in range(0, size):
                for x in range(0, size):
                    if net.connects[y, x] > 0.0:
                        connects.append([y, x, net.connects[y, x]])

            for y in range(0, size):
                for x in range(0, size):
                    if actions[y, x] != '':
                        lstAction.append([y, x, actions[y, x]])

            net.connects = np.array(())
            json['actions'] = lstAction
            json['connects'] = connects
            json['net'] = net.getJson()

        return js.dumps(json, sort_keys=True, indent=4, separators=(',', ': ')) if data == 'json' else json

    ####################################################################

    def selectDeep(self, topic, returns=None, deep=[]):
        data = self.select(topic, 'json')
        # TODO construir recorrido de grafo en forma recursiva
        items = deep
        items.append(topic)

        for item in data['net']['graph']['nodeNames']:
            if item not in items:
                items[item] = self.selectDeep(item, 'json')
            pass
        pass

    ####################################################################

    def combine(self, base, item, data=None):
        json = {
            'width': None,
            'height': None,
            'net': None,
            'actions': [],
            'connects': [],
            'contentList': {}
        }

        lstConnects = []
        lstAction = []
        net = Graph(name='net')
        net.functions = self.actionFunc

        if type(base) is str:
            base = js.loads(base)

        if type(item) is str:
            item = js.loads(item)

        all = base['net']['graph']['nodeNames'] + item['net']['graph']['nodeNames']

        for each in all:
            pNode = net.addNode(net, name=each.name)
            if pNode is not None:
                pNode.extraInfo = each.extraInfo

        size = len(net.nodeNames)
        actions = np.chararray((size, size), itemsize=30)
        actions[:] = ''
        net.connects = np.zeros((size, size), dtype=float)

        for i in range(0, len(base['actions'])):
            (o, d, act) = base['actions'][i]
            (o, d, val) = base['connects'][i]
            txt1 = base['net']['graph']['nodeNames'][o]
            txt2 = base['net']['graph']['nodeNames'][d]
            y = net.getIndexOf(txt1)
            x = net.getIndexOf(txt2)
            actions[y, x] = act
            net.connects[y, x] = val

        for i in range(0, len(item['actions'])):
            (o, d, act) = item['actions'][i]
            (o, d, val) = item['connects'][i]
            txt1 = item['net']['graph']['nodeNames'][o]
            txt2 = item['net']['graph']['nodeNames'][d]
            y = net.getIndexOf(txt1)
            x = net.getIndexOf(txt2)
            actions[y, x] = act
            net.connects[y, x] = val

        for y in range(0, size):
           for x in range(0, size):
              if net.connects[y, x] > 0.0:
                 lstConnects.append([y, x, net.connects[y, x]])

        for y in range(0, size):
           for x in range(0, size):
              if actions[y, x] != '':
                 lstAction.append([y, x, actions[y, x]])

        for key in base['contentList']:
            json['contentList'][key] = base['contentList'][key]

        for key in item['contentList']:
            json['contentList'][key] = item['contentList'][key]

        json['actions'] = lstAction
        json['connects'] = lstConnects
        json['net'] = net.getJson()
        json['width'] = size
        json['height'] = size

        return js.dumps(json, sort_keys=True, indent=4, separators=(',', ': ')) if data == 'json' else json
