[![PyPI version](https://badge.fury.io/py/udpipe-analyzer.svg)](https://badge.fury.io/py/udpipe-analyzer)

# UDPipe Parser

This parser takes a sentence, does syntax analysis using [udpipe model](https://github.com/ufal/udpipe) and returns a structure that is easy-to-use in
common NLP/NLU tasks. 

# Quickstart

```
import udpipe_parser
P = udpipe_parser.UDPipe_Parser()
exps = P.run("Я хочу материальную помощь! Как её получить?",solve_anaphora=True,logging=False)
for exp in exps:
  print(exp,'\n')

subj : я, 
pred : хотеть, 
obj : помощь материальный, 
params :  

subj : 
pred : получить, 
obj : помощь материальный, 
params : как,

exps[0].obj
[{'pos': 'NOUN', 'polarity': 'affirmative', 'case': 'Acc', 'numb': 'Sing', 'form': 'помощь материальный', 'prep': None, 'dets': []}]

```

# Metrics 

To evaluate accuracy of the parser a dataset was collected from questions and annotated in terms of predicates, subjects, objects, parameters. Examples:

![picture]https://sun9-37.userapi.com/impg/i2PkfBL8xkuHSYCpDpSSXMXCPhm4ApZNTwqWJg/NuXV83j1Ci0.jpg?size=873x244&quality=96&proxy=1&sign=3b843cfb9b5f1769d9795b471b3f596f&type=album)


# Documentation

## Expression

Expression is a class for presenting a result of analysis. It contains four items each of them has attributes.

```
class Expression:
  def __init__(self,subj=[],pred=[],obj=[],parameters=[]):
    self.subj = [] # SUBJECT
    self.pred = [] # PREDICATE
    self.obj = [] # OBJECT
    self.params = [] # PARAMETERS

```

**PREDICATE** expresses action or property of the subject

**SUBJECT** -  the person or thing performing the action expressed by predicate

**OBJECT** -  the person or thing that receives the action expressed by predicate 

**PARAMETERS** - specifications of predicates (e.g. быстро, в спешке, не выходя из дома)

Each item can have some of these attributes:

attributes:

```

'pos' : Part of speech

'polarity': Affirmative/Negative

'numb': Number

'case': Case

'tense': Tense

'voice': Active/Passive

'aspect': Imperfective/perfective

'form': word form

'prep': Preposition with it

'dets': Determiner

'modality' : Modal Verb

```


## UDPipe_Parser

Instance of this class perfomes analysis of text data. It takes a text, makes preprocessing, builds conllu-trees, solves anaphora (if needed) and parses trees.
The result is a list of Expression instances which represent trees/subtrees. Analyzer class can take dict as a parameter, it is a words or expressions that should be 
treated as proper names (hence, they can be subjects or objects). In order to provide more stable perfomance it is advisable to fill this list with out-of-dictionary words,
such as acronyms, jargon words, slang etc.

```

my_propn_nouns = ["рувд","мгу","ростех","роснефть","вычи"]
P = udpipe_parser.UDPipe_Parser(propn_nouns=my_propn_nouns)

```

Also, one can use abbreviations dictionary to convert abbreviations into normal word forms

```
abbrev_dict = {'абс.' : 'абсолютный', 'град.':'градус'}
P = udpipe_parser.UDPipe_Parser(abbrev_dict=abbrev_dict)
exps = P.run('какое абс. значение в град. Цельсия?')
print(exps[0])

subj : значение абсолютный в градус цельсий, 
pred : быть, 
obj : 
params :

```

### Solving Anaphora 

The parser can try to solve anaphora optionally:

```
>>> P = udpipe_parser.UDPipe_Parser()
>>> exps = P.run('Я заказывал кредитку. Где я могу её забрать?',solve_anaphora=True)
>>> for exp in exps:
	print(exp)

	
subj : я, 
pred : заказывать, 
obj : кредитка, 
params : 

subj : я, 
pred : забрать, 
obj : кредитка, 
params : где, 

```

### Logging 

To keep track of perfomance process use a flag 'logging':

```
P = udpipe_parser.UDPipe_Parser()
exps = P.run('Между духом и материей посредничает математика.',logging=True)

sent: Между духом и материей посредничает математика .
child of  посредничает : духом {'id': 2, 'form': 'духом', 'lemma': 'дух', 'upos': 'NOUN', 'xpos': None, 'feats': {'Animacy': 'Inan', 'Case': 'Ins', 'Gender': 'Masc', 'Number': 'Sing'}, 'head': 5, 'deprel': 'obl', 'deps': None, 'misc': None}
child of  посредничает : математика {'id': 6, 'form': 'математика', 'lemma': 'математика', 'upos': 'NOUN', 'xpos': None, 'feats': {'Animacy': 'Inan', 'Case': 'Nom', 'Gender': 'Fem', 'Number': 'Sing'}, 'head': 5, 'deprel': 'nsubj', 'deps': None, 'misc': None}
child of  посредничает : . {'id': 7, 'form': '.', 'lemma': '.', 'upos': 'PUNCT', 'xpos': None, 'feats': None, 'head': 5, 'deprel': 'punct', 'deps': None, 'misc': {'SpaceAfter': 'No'}}
[UDPipe Parser] elapsed time: 0.4530816078186035

print(exps[0])
subj : математика, 
pred : посредничать, 
obj : 
params : между дух, материя, 

```
