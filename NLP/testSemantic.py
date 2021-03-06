import sys
import re
import multiprocessing
import time
import numpy as np

from SemanticNetwork import *

LANGUAGE_RULES = 'spanishRules.json'

start_time = time.time()

s = SemanticNetwork(LANGUAGE_RULES)

# ejemplo: python testSemantic.py train '' ''
if sys.argv[1] == 'train':
    train = sys.argv[2] if sys.argv[2] is not None and sys.argv[2] != '' else 'semanticTrainer.txt'
    dbFile = sys.argv[3] if sys.argv[3] is not None and sys.argv[3] != '' else 'semanticNet.json'

    s.load(dbFile)
    text = sp.check_output(['sh', "%s/%s" % (s.rules.path, s.rules.fromFile), train])
    patterns = re.compile('((\w+|[ ,.;?()"])+\S)\s+\((\w+)\)')
    list = text.split("\n")

    for line in list:
        expr = patterns.search(line)
        if expr:
            (frase, verb) = expr.group(1, 3)
            print ("\nRAW: %s => [%s]") % (frase, verb)
            try:
                tokens = s.rules.getSyntax(frase)
                syntax = s.rules.normalize(tokens)
                print ("1) tokens: %s") % str(tokens)
                print ("2) syntax: %s") % str(syntax)
                print ("3) train:")
                s.train(frase, verb)
                list = s.analize(frase)
                print ("4) test: %s\n") % str(list)
                for item in list[0]:
                    print ("%03d) texto:%s\n     nucleo:%s\n     sujeto:{%s}\n     predicado:{%s}\n") % (
                    0, item['text'], item['root'], str(item['subject']), str(item['predicate']))

            except ValueError:
                print(ValueError)
                continue


# ejemplo: python testSemantic.py web https://definicion.de/taoismo '' 'taoismo.json'
if sys.argv[1] == 'web':
    url = 'https://raw.githubusercontent.com/miguelotemagno/imagestion/imagestion_1.0/NLP/grammarTest.txt'
    if sys.argv[2] != '':
        url = sys.argv[2]

    dbFile = sys.argv[3] if sys.argv[3] is not None and sys.argv[3] != '' else 'semanticNet.json'
    s.load(dbFile)

    s.rules.loadFromWeb(url)
    #tokens = s.rules.getSyntax(s.rules.text)
    #normalize = s.rules.normalize(tokens)

    list = s.analize(s.rules.text)
    for y in xrange(0, len(list)-1):
        if len(list[y]) > 0:
            for item in list[y]:
                print ("%03d) texto:%s\n     nucleo:%s\n     sujeto:{%s}\n     predicado:{%s}\n     tokens:{%s}\n") % (y, item['text'], item['root'], str(item['subject']), str(item['predicate']), str(item['tokens']))
                s.makeSemanticNetwork(item['tokens'])

    s.linkPlurals()

    file = "redSemantica.json"
    if sys.argv[4] != '':
        file = sys.argv[4]

    #s.makeSemanticNetwork(normalize)
    s.saveSemanticNetwork(file)

    print ("connects:\n")
    print (s.net.connects)
    print ("\nactions:\n")
    print (s.actions)


# ejemplo: python testSemantic.py file taoismo.txt '' taoismo.json
if sys.argv[1] == 'file':
    file = "grammarTest.txt"
    if sys.argv[2] != '':
        file = sys.argv[2]

    dbFile = sys.argv[3] if sys.argv[3] is not None and sys.argv[3] != '' else 'semanticNet.json'
    s.load(dbFile)

    s.rules.loadFromFile(file)
    #tokens = s.rules.getSyntax(s.rules.text)
    #normalize = s.rules.normalize(tokens)
    #print "TOKENS: %s\n" % str(tokens)
    #print "NORMALIZE: %s\n" % str(normalize)
    
    
    list = s.analize(s.rules.text)

    for y in xrange(0, len(list)-1):
        if len(list[y]) > 0:
            for item in list[y]:
                print ("%03d) texto:%s\n     nucleo:%s\n     sujeto:{%s}\n     predicado:{%s}\n     tokens:{%s}\n") % (y, item['text'], item['root'], str(item['subject']), str(item['predicate']), str(item['tokens']))
                s.makeSemanticNetwork(item['tokens'])

    s.linkPlurals()

    file = "redSemantica.json"
    if sys.argv[4] != '':
        file = sys.argv[4]

    #s.makeSemanticNetwork(normalize)
    s.saveSemanticNetwork(file)

    print ("connects:\n")
    print (s.net.connects)
    print ("\nactions:\n")
    print (s.actions)


if sys.argv[1] == 'clean':
    dbFile = sys.argv[2] if sys.argv[2] is not None and sys.argv[2] != '' else 'semanticNet.json'
    s.save(dbFile)


if sys.argv[1] == 'add-verb':
    verb = sys.argv[2]
    first = verb[0]
    s.rules.registerVerb(first, verb)

if sys.argv[1] == 'import-verbs':
    for car in range(ord('a'), ord('z')+1):
        first = chr(car)
        for verb in s.rules.rules[first].keys():
            print("%s %s" % (first, verb))
            s.rules.registerVerb(first, verb, rules=s.rules.getJsonFrom(s.rules.rules[first][verb]))


if sys.argv[1] == 'select':
    query = sys.argv[2]
    dbFile = sys.argv[3] if sys.argv[3] is not None and sys.argv[3] != '' else 'semanticNet.json'
    dbSemantic = sys.argv[4] if sys.argv[4] is not None and sys.argv[4] != '' else 'redSemantica.json'
    s.load(dbFile)
    s.loadSemanticNetwork(dbSemantic)

    print(s.select(query, data='json'))


if sys.argv[1] == 'select-deep':
    query = sys.argv[2]
    dbFile = sys.argv[3] if sys.argv[3] is not None and sys.argv[3] != '' else 'semanticNet.json'
    dbSemantic = sys.argv[4] if sys.argv[4] is not None and sys.argv[4] != '' else 'redSemantica.json'
    s.load(dbFile)
    s.loadSemanticNetwork(dbSemantic)

    print(s.selectDeep(query, returns='json'))


if sys.argv[1] == 'combine':
    txt1 = sys.argv[2]
    txt2 = sys.argv[3]
    dbFile = sys.argv[4] if sys.argv[4] is not None and sys.argv[4] != '' else 'semanticNet.json'
    dbSemantic = sys.argv[5] if sys.argv[5] is not None and sys.argv[5] != '' else 'redSemantica.json'
    s.load(dbFile)
    s.loadSemanticNetwork(dbSemantic)

    base = s.select(txt1)
    #print ("%s : %s\n" % (txt1, str(base)))
    item = s.select(txt2)
    #print ("%s : %s\n" % (txt2, str(item)))

    print(s.combine(base, item, data='json'))


print ('Done! Time taken: %f sec for %d CPUs') % (time.time() - start_time, multiprocessing.cpu_count())
