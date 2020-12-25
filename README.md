# Udpipe Analyzer

This analyzer takes sentence in russian and does syntax analysis using [udpipe model](https://github.com/ufal/udpipe) and returns a structer that is easy-to-use in
common NLP/NLU tasks. 


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

attributes:

```

'pos' : Part of speech

'polarity': Affirmative/negative

'numb': Number

'tense': Tense

'voice': Active/Passive

'aspect': Imperfective/perfective

'form': word form of the predicate 

```

**SUBJECT** -  the person or thing performing the action expressed by predicate

attributes:
```
'pos' : Part of speech

'polarity' : Affirmative/negative

'case': Case

'numb': Number

'form': Word form of the subject

'prep': Preposition with it

'dets': Determiner
```

**OBJECT** -  the person or thing that receives the action expressed by predicate 

attributes:
```
'pos' : Part of speech

'polarity' : Affirmative/negative

'case': Case

'numb': Number

'form': Word form of the subject

'prep': Preposition with it

'dets': Determiner
```

**PARAMETERS** - specifications of predicates (e.g. быстро, в спешке, не выходя из дома)
```
'pos' : Part of speech

'polarity' : Affirmative/negative

'numb': Number

'form': Word form of the parameter

'prep': Preposition with it

'dets': Determiner
```

# Get Started

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

```
