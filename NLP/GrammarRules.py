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

import re
import json
import subprocess as sp
import os
import sqlite3

class GrammarRules:
    def jsonLoad(self, dbFile):
        f = open(dbFile, 'r')
        jsRules = f.read();
        f.close()
        return json.loads(jsRules)
        
    ####################################################################
    
    def __init__(self, db_file=None):
        self.dbFile   = "spanishRules-original.json" if db_file is None else db_file
        self.rules    = self.jsonLoad(self.dbFile)
        self.fromFile = self.rules['readFromFile']     #'loadFromFile2.sh'
        self.fromWeb  = self.rules['readFromWeb']      #'loadFromWeb3.sh'
        self.fromVerb = self.rules['readFromVerb']     #'loadFromWeb3.sh'
        self.path = os.getcwd()
        self.text = ""
        self.DB_PATH = "%s/%s.db" % (os.path.dirname(__file__), self.dbFile)

        for car in range(ord('a'), ord('z')+1):
            char = chr(car)
            if char not in self.rules.keys():
                self.rules[char] = {}

        conn = self.sqliteConnect()
        c = conn.cursor()
        getVerbs = "select first, verb, rule from verbs order by first, verb"

        for row in c.execute(getVerbs):
            (char, verb, hash) = row
            self.rules[char][verb] = json.loads(hash)

        conn.close()

    ####################################################################
    
    def isVerb(self):
        items = self.rules['verb']
        expr = '^(' + '|'.join(items) + ')$'
        return re.compile(expr)

    ####################################################################

    def isAuxiliar(self, text):
        items = self.rules['auxiliar']
        expr = '^(' + '|'.join(items) + ')$'
        eval = re.compile(expr)
        if eval.match(text):
            return 'auxiliar'

        return None

    ####################################################################

    def isNumber(self, text):
        items = self.rules['number']
        expr = '^(' + '|'.join(items) + ')$'
        eval = re.compile(expr)
        if eval.match(text):
            return 'number'
    
        return None

    ####################################################################

    def isPunctuation(self, text):
        items = self.rules['punctuation']
        expr = '^(' + '|'.join(items) + ')$'
        eval = re.compile(expr)
        if eval.match(text):
            return 'punctuation'

        return None

    ####################################################################

    def isDeterminer(self, text):
        for type, list in self.rules['determiner'].iteritems():
            expr = '^('+'|'.join(list)+')$'
            eval = re.compile(expr)
            if eval.match(text):
                return type

        return None

    ####################################################################
    
    def isAdjetive(self, text):
        for type, list in self.rules['adjetive'].iteritems():
            expr = '^(' + '|'.join(list) + ')$'
            eval = re.compile(expr)
            if eval.match(text):
                return type

        return None

    ####################################################################
    
    def isNoun(self, text):
        for type, list in self.rules['noun'].iteritems():
            expr = '^(' + '|'.join(list) + ')$'
            eval = re.compile(expr)
            if eval.match(text):
                return type

        return None

    ####################################################################
    
    def isPreposition(self, text):
        for type, list in self.rules['preposition'].iteritems():
            expr = '^(' + '|'.join(list) + ')$'
            eval = re.compile(expr)
            if eval.match(text):
                return type

        return None

    ####################################################################
    
    def isAdverb(self, text):
        for type, list in self.rules['adverb'].iteritems():
            expr = '^(' + '|'.join(list) + ')$'
            eval = re.compile(expr)
            if eval.match(text):
                return type

        return None

    ####################################################################
    
    def isPronom(self, text):
        for type, list in self.rules['pronom'].iteritems():
            expr = '^(' + '|'.join(list) + ')$'
            eval = re.compile(expr)
            if eval.match(text):
                return type

        return None

    ####################################################################

    def isInterjection(self, text):
        for type, list in self.rules['interjection'].iteritems():
            expr = '^(' + '|'.join(list) + ')$'
            eval = re.compile(expr)
            if eval.match(text):
                return type

        return None

    ####################################################################

    def isConjunction(self, text):
        for type, list in self.rules['conjunction'].iteritems():
            expr = '^(' + '|'.join(list) + ')$'
            eval = re.compile(expr)
            if eval.match(text):
                return type

        return None

    ####################################################################

    def getVerb(self, text):
        if text != "":
            char = text[0]
            if char in self.rules:
                for verb, hash in self.rules[char].iteritems():
                    try:
                        expr = '^('+'|'.join(hash.values())+')$'
                        #print ("%s {%s}") % (text, expr)
                        eval = re.compile(expr)
                    except ValueError:
                        print ("ERROR getVerb(%s): {%s} %s") % (text, expr, ValueError)

                    if eval.match(text):
                        return verb

        return None

    ####################################################################
        
    def getVerbTense(self, verb, text):
        char = text[0]
        isIn = re.compile('^(ger|par|i([cpf]|nf|pi|pps)?|sp[i]?[2]?|sf)$')

        try:
            if char in self.rules:
                for tense, hash in self.rules[char][verb].iteritems():
                    if isIn.match(tense):
                        expr = '^'+hash+'$'
                        eval = re.compile(expr)
                        if eval.match(text):
                            return tense
        except ValueError, e:
            print("ERROR getVerbTense(%s,%s): %s\n" % (verb, text, str(e)))
        except IndexError, e:
            print("ERROR getVerbTense(%s,%s): %s\n" % (verb, text, str(e)))
        except KeyError, e:
            print("ERROR getVerbTense(%s,%s): %s\n" % (verb, text, str(e)))

        return None

    ##########################################################################
        
    def getVerbPron(self, verb, text):
        char = text[0]
        isIn = re.compile('^(yo|tu|el_la|nos|uds|ellos)$')

        try:
            if char in self.rules:
                for pron, hash in self.rules[char][verb].iteritems():
                    if isIn.match(pron):
                        expr = '^'+hash+'$'
                        eval = re.compile(expr)
                        if eval.match(text):
                            return pron
        except ValueError:
            print("ERROR getVerbTense(%s,%s): %s\n" % (verb, text, str(ValueError)))
        except IndexError:
            print("ERROR getVerbTense(%s,%s): %s\n" % (verb, text, str(IndexError)))
        except KeyError:
            print("ERROR getVerbTense(%s,%s): %s\n" % (verb, text, str(KeyError)))

        return None

    ##########################################################################

    def getNltkType(self, idx):
        type = self.rules["NLTK"][idx] if idx in self.rules["NLTK"] else idx
        return type

    ##########################################################################

    def setText(self, text):
        self.text = text

    ##########################################################################

    def loadFromFile(self,source):
        print ("=> loadFromFile (%s)\n") % (source)
        self.text = sp.check_output(['sh', "%s/%s" % (self.path,self.fromFile), source])

    ##########################################################################

    def loadFromWeb(self,source):
        print ("=> loadFromWeb (%s)\n") % (source)
        print ("   sh  %s/%s %s\n") % (self.path, self.fromWeb, source)
        self.text = sp.check_output(['sh', "%s/%s" % (self.path,self.fromWeb), source])

    ##########################################################################

    def loadFromVerb(self, verb):
        print ("=> loadFromVerb (%s)\n") % (verb)
        print ("   perl  %s/%s %s\n") % (self.path, self.fromVerb, verb)
        return sp.check_output(['perl', "%s/%s" % (self.path, self.fromVerb), verb])

    ##########################################################################

    def word_tokenize(self, text):
        punct = '('+self.rules['punctuation'][0]+')'
        text = re.sub(punct, r' \1 ', text)
        tokens = re.split('\s+', text)
        return tokens

    ##########################################################################

    def pos_tag(self, tokens, simple=None):
        list = []

        for token in tokens:
            tags = []
            type = "??"

            verb = self.getVerb(token)
            if verb is not None:
                type = self.getVerbTense(verb, token)
                aux = self.isAuxiliar(verb)
                if type is not None and self.getNltkType(type) is not None:
                    type = self.getNltkType(type) if simple is not None else type
                    tags.append(self.getNltkType(type))
                if aux is not None:
                    aux = self.getNltkType(aux) if simple is not None else aux
                    tags.append(self.getNltkType(aux))


            pron = self.isPronom(token)
            if pron is not None:
                pron = self.getNltkType(pron) if simple is not None else pron
                tags.append(self.getNltkType(pron))

            num = self.isNumber(token)
            if num is not None:
                num = self.getNltkType(num) if simple is not None else num
                tags.append(self.getNltkType(num))

            punct = self.isPunctuation(token)
            if punct is not None:
                punct = self.getNltkType(punct) if simple is not None else punct
                tags.append(self.getNltkType(punct))

            adj = self.isAdjetive(token)
            if adj is not None:
                adj = self.getNltkType(adj) if simple is not None else adj
                tags.append(self.getNltkType(adj))

            adv = self.isAdverb(token)
            if adv is not None:
                adv = self.getNltkType(adv) if simple is not None else adv
                tags.append(self.getNltkType(adv))

            prep = self.isPreposition(token)
            if prep is not None:
                prep = self.getNltkType(prep) if simple is not None else prep
                tags.append(self.getNltkType(prep))

            sust = self.isNoun(token)
            if sust is not None:
                sust = self.getNltkType(sust) if simple is not None else sust
                tags.append(self.getNltkType(sust))

            conj = self.isConjunction(token)
            if conj is not None:
                conj = self.getNltkType(conj) if simple is not None else conj
                tags.append(self.getNltkType(conj))

            det = self.isDeterminer(token)
            if det is not None:
                det = self.getNltkType(det) if simple is not None else det
                tags.append(self.getNltkType(det))

            intj = self.isInterjection(token)
            if intj is not None:
                intj = self.getNltkType(intj) if simple is not None else intj
                tags.append(self.getNltkType(intj))

            if len(tags) > 0:
                type = '|'.join(tags)

            if token is not None and token != '':
                list.append((token, type))

        return list

    ####################################################################

    def validType(self, type, nextType=None):
        if type is None:
            return None

        if '|' in type:
            if 'DET' in type and nextType in ['NOUN', 'CONJ', 'ADJ', 'VERB', 'PREP', 'NUM']:
                type = 'DET'
            elif 'NOUN' in type and nextType in ['VERB']:
                type = 'NOUN'
            elif 'PRON' in type and nextType in ['NOUN', 'ADJ']:
                type = 'PRON'
            elif 'PREP' in type and nextType in ['NOUN', 'ADJ', 'PRON', 'DET', 'ADV', 'PRON']:
                type = 'PREP'
            elif 'ADV' in type and nextType in ['ADJ', 'ADV']:
                type = 'ADV'
            elif 'ADJ' in type and nextType in ['NOUN', 'VERB', 'CONJ', 'DET', 'PRON', 'PUNCT']:   #'PREP',
                type = 'ADJ'
            elif 'CONJ' in type and nextType in ['VERB', 'DET', 'ADV', 'PRON']:
                type = 'CONJ'
            #elif 'ADJ' in type and ('ADV' in type or 'NOUN' in type):
            #    type = 'NOUN'
            elif 'ADV' in type and ('CONJ' in type or 'NOUN' in type):
                type = 'ADV'
            elif 'AUX' in type and nextType in ['VERB']:
                type = 'AUX'
            elif 'VERB' in type:
                type = 'VERB'
            if '|' in type:
                type = re.sub('(\w+[|])+', '', type)
        elif '??' in type:
            type = 'NOUN'

        return type

    ####################################################################

    def normalize(self, tokens):
        list = []
        nexType = None

        for pos in xrange(len(tokens)-1, -1, -1):
            token = tokens[pos]
            word = token[0]
            type = token[1]
            #print ("%d (%s, %s)") % (pos, word, type)
            normType = self.validType(type, nexType)
            newToken = (word, normType, self.getIndexFromType(normType, word))
            list.insert(0, newToken)
            nexType = normType

        return list

    ####################################################################

    def getSyntax(self, text):
        tokens = self.word_tokenize(text)
        syntax = self.pos_tag(tokens, False)
        return syntax

    ##########################################################################

    def getCorpus(self, text):
        pass

    ####################################################################

    def getIndexFromType(self, type, word):
        types = {
            'DET':  self.isDeterminer,  #(word),
            'NOUN': self.isNoun,        #(word),
            'ADJ':  self.isAdjetive,    #(word),
            'PREP': self.isPreposition, #(word),
            'VERB': self.getVerbTense,  #(verb, word),
            'ADV':  self.isAdverb,      #(word),
            'PRON': self.isPronom,      #(word),
            'INTJ': self.isInterjection,#(word),
            'CONJ': self.isConjunction, #(word),
            'NUM':  self.isNumber,      #(word),
            'PUNC': self.isPunctuation, #(word),
            'AUX':  self.isAuxiliar     # (word),
        }

        try:
            if type == 'VERB':
                verb = self.getVerb(word)
                return types[type](verb, word) if verb is not None else None
            else:
                return types[type](word)
        except KeyError, e:
            print ("ERROR getIndexFromType(%s,%s): %s" % (type, word, e))
            pass

    ####################################################################

    def registerVerb(self, first, verb, rules=None):
        try:
            conn = self.sqliteConnect()
            c = conn.cursor()
            select = "select count(*) from verbs where first=? and verb=?"
            c.execute(select, (first, verb))
            count = c.fetchone()[0]

            if count == 0:
                rule = rules if rules is not None else "{\n%s\n}" % self.loadFromVerb(verb)
                data = (verb, first, rule)
                insert = "insert into verbs (verb, first, rule) values (?, ?, ?)"
                c.execute(insert, data)

            conn.commit()
            conn.close()
        except Exception, e:
            print "ERROR: %s" % (e)
        pass

    ####################################################################

    def sqliteConnect(self):
        conn = sqlite3.connect(self.DB_PATH)
        c = conn.cursor()
        table = """
            CREATE TABLE IF NOT EXISTS verbs (
                verb    VARCHAR(30),
                first   VARCHAR(1),
                rule    VARCHAR(1000),
                PRIMARY KEY(first, verb)
            )
        """
        c.execute(table)
        return conn

    def getJsonFrom(self, data):
        return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
