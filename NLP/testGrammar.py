import sys
import re
from GrammarRules import *

g = GrammarRules()

if sys.argv[1] == 'web':
	url = 'https://raw.githubusercontent.com/miguelotemagno/imagestion/imagestion_1.0/NLP/grammarTest.txt'
	if sys.argv[2] != '':
		url = sys.argv[2]

	g.loadFromWeb(url)
	print g.text

	tokens = g.word_tokenize(g.text)
	#print tokens
	list = g.pos_tag(tokens, False)
	print list

if sys.argv[1] == 'file':
	file = "grammarTest.txt"
	if sys.argv[2] != '':
		file = sys.argv[2]

	g.loadFromFile(file)
	tokens = g.word_tokenize(g.text)
	list = g.pos_tag(tokens, False)
	print list

