# Udpipe Analyzer

This analyzer takes sentence in russian and does syntax analysis using [udpipe model](https://github.com/ufal/udpipe). The result of analysis is
represented in four items and its attributes.

PREDICATE expresses action or property of the subject

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

SUBJECT -  the person or thing performing the action expressed by predicate

attributes:
``
'pos' : Part of speech

'polarity' : Affirmative/negative

'case': Case

'numb': Number

'form': Word form of the subject

'prep': Preposition with it

'dets': Determiner
``

OBJECT -  the person or thing that receives the action expressed by predicate

attributes:
``
'pos' : Part of speech

'polarity' : Affirmative/negative

'case': Case

'numb': Number

'form': Word form of the subject

'prep': Preposition with it

'dets': Determiner
``
