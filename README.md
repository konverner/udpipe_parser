[![PyPI version](https://badge.fury.io/py/udpipe-analyzer.svg)](https://badge.fury.io/py/udpipe-analyzer)

# Udpipe Analyzer

There is a great models for syntax analysis of natural language data. This analyzer takes sentence in russian and does syntax analysis using [udpipe model](https://github.com/ufal/udpipe) and returns a structer that is easy-to-use in
common NLP/NLU tasks. 

# Quickstart

```
import udpipe_analyzer
A = udpipe_analyzer.Analyzer()
exps = A.run("Я хочу материальную помощь! Как её получить?",solve_anaphora=True,logging=False)
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

'polarity': Affirmative/negative

'numb': Number

'case': Case

'tense': Tense

'voice': Active/Passive

'aspect': Imperfective/perfective

'form': word form

'prep': Preposition with it

'dets': Determiner

```


## Analyzer

Instance of this class perfomes analysis of text data. It takes a text, makes preprocessing, builds conllu-trees, solves anaphora (if needed) and parses trees.
The result is a list of Expression instances which represent trees/subtrees. Analyzer class can take dict as a parameter, it is a words or expressions that should be 
treated as proper names (hence, they can be subjects or objects). In order to provide more stable perfomence it is advaisable to fill this list with out-of-dictionary words,
such as abbreviations, jargon words, slang etc.

```
my_propn_nouns = {"рувд" : "'рувд'", "локалка" : "'локалка'"} 
A = udpipe_analyzer.Analyzer(propn_nouns=my_propn_nouns)
```
