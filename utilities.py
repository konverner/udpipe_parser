import re

from difflib import SequenceMatcher
from dicts import *
#from .dicts import *
from morpholog import Morpholog

morph = Morpholog()


# Approximate string matching in array
def approx_match(string, array):
    for element in array:
        if is_similar(string, element):
            return element


def is_similar(a, b):
    return SequenceMatcher(None, a, b).ratio() > 0.65


# check case parameter of udpipe node
def is_a_case(node, case):
    if is_a_tag(node, 'X'):
        return True
    if 'feats' in node.token.keys():
        if node.token['feats'] is not None:
            if 'Case' in node.token['feats'].keys():
                if case in node.token['feats']['Case']:
                    return True
                else:
                    return False
        else:
            return False
    return True


# utility function for checking pos-tag of udpipe node
def is_a_tag(node, tag):
    return tag == node.token['upostag'] or tag == node.token['upos']


def is_a_deprel(node, deprel):
    return deprel == node.token['deprel']


# check if node contains at least one of attributes.
# if name of attribute has upper case this is a POS tag
# if name of attribute is capitalized then this is a case tag
# else it is a deprel tag
def one_of_these(node, attributes):
    for attrib in attributes:
        if attrib.upper() == attrib:
            if is_a_tag(node, attrib):
                return True
        elif attrib.capitalize() == attrib:
            if is_a_case(node, attrib):
                return True
        else:
            if is_a_deprel(node, attrib):
                return True
    return False


def each_of_these(node, attributes):
    score = 0
    for attrib in attributes:
        if attrib.upper() == attrib:
            if is_a_tag(node, attrib):
                score += 1
        elif attrib.capitalize() == attrib:
            if is_a_case(node, attrib):
                score += 1
        else:
            if is_a_deprel(node, attrib):
                score += 1
    if score == len(attributes):
        return True
    return False


# check voice parameter of udpipe node
def is_passive_voice(node):
    try:
        if 'feats' in node.token.keys():
            if 'Voice' in node.token['feats'].keys():
                if 'Pass' in node.token['feats']['Voice']:
                    return True
                else:
                    return False
        return False
    except:
        return False


# check transitivity of the verb
def is_trans(node):
    form = node.token['form']
    if form[-2:] == 'ся':
        return False
    parsed = morph.parse(form)
    for word in parsed:
        if 'intr' in word.tag:
            return False

    return True

def is_modal_verb(node):
    return node.token['lemma'] in modal_verbs


# make dict for a word from udpipe node
def make_word(node, form, prep=None, dets=[], modal_verb=None):
    w = dict()

    if form == 'нет' or 'нет быть' in form:
        w['polarity'] = 'negative'
        form = 'не быть'

    if re.findall('^не ', form) != [] or re.findall(' ' + 'не' + ' ', form) != []:
        w['polarity'] = 'negative'
    else:
        w['polarity'] = 'affirmative'

    if node is not None:
        w['pos'] = node.token['upostag']
        if 'feats' in node.token.keys():
            if node.token['feats'] is not None:
                if 'Case' in node.token['feats'].keys():
                    w['case'] = node.token['feats']['Case']
                if 'Fem' in node.token['feats'].keys():
                    w['gender'] = node.token['feats']['Fem']
                if 'Number' in node.token['feats'].keys():
                    w['numb'] = node.token['feats']['Number']
                if 'Tense' in node.token['feats'].keys():
                    w['tense'] = node.token['feats']['Tense']
                if 'Voice' in node.token['feats'].keys():
                    w['voice'] = node.token['feats']['Voice']
                if 'Aspect' in node.token['feats'].keys():
                    w['aspect'] = node.token['feats']['Aspect']
    w['form'] = form.lower()
    if prep is not None:
        w['form'] = ' '.join(form.split(' ')[1:]).lower()
    if modal_verb is not None and modal_verb[:-2] in form:
        if modal_verb not in w['form']:
            w['form'] = str(
                form[:form.index(modal_verb[:-2])] + form[form.index(modal_verb[:2]) + len(modal_verb) + 2:]).lower()
        else:
            w['form'] = str(form[:form.index(modal_verb)] + form[form.index(modal_verb) + len(modal_verb) + 1:]).lower()

    if dets:
        for det in dets:
            while det in w['form']:
                w['form'] = (w['form'][:w['form'].find(det)] + w['form'][w['form'].find(det) + len(det) + 1:]).strip()
    if "'" in w['form']:
        w['form'] = w['form'].replace("'", "")

    w['prep'] = prep
    w['dets'] = dets
    w['modality'] = modal_verb
    return w


# extract modal verb from a phrase
def extract_modal_verb(phrase):
    modal_verb = ''
    tokens = phrase.split()
    for i in range(len(tokens) - 1):
        if tokens[i] == 'не' and tokens[i + 1] in modal_verbs:
            modal_verb += tokens[i] + ' '
        elif tokens[i] in modal_verbs:
            if tokens[i][-2:] == 'ый':
                tokens[i] = tokens[i][:-2] + 'о'
            modal_verb += tokens[i] + ' '
        else:
            break
    if modal_verb != '':
        return modal_verb.strip()
    return None


# extract prepositions from a phrase
def extract_prep(phrase):
    if phrase.split()[0].lower() in preps:
        return phrase.split()[0].lower()
    return None


# extract determiners from a phrase
def extract_dets(phrase):
    result = []
    for det in dets:
        if re.findall('^' + det + ' ', phrase) != [] or re.findall(' ' + det + ' ', phrase) != []:
            result.append(det)
    return result


# check whether or not conllu subtree contains preposition
def prep_in(node, t='any'):
    for i in range(len(node.children)):
        if is_a_tag(node.children[i], "ADP") and t == 'any':
            return True
        elif is_a_tag(node.children[i], "ADP") and node.children[i].token['form'] in obj_preps and t == 'obj':
            return True
    return False


# CHECK IF THE VERB NODE HAS A CHILD WHICH IS DIRECT OBJECT
def has_direct_object(node):
    nouns_have_prep = []
    for j in range(len(node.children)):
        if (is_a_tag(node.children[j], 'NOUN') or is_a_tag(node.children[j], 'ADJ') or
                (is_a_tag(node.children[j], 'NUM') and 'advmod' not in node.children[j].token['deprel'])):
            nouns_have_prep.append(prep_in(node.children[j]))
        if 'csubj' in node.children[j].token['deprel']:
            return True
    if False in nouns_have_prep:
        return True
    else:
        return False


# check whether or not chilnden of node in conllu subtree contains nodes with specific deprel tag
def deprel_in(node, deprel):
    for i in range(len(node.children)):
        if deprel in node.children[i].token['deprel']:
            return True
    return False


# True if there is at least one pronoun in sentences
# False else
def pronouns_in(trees):
    for tree in trees:

        if type(tree) == list:
            current = tree[0]
        else:
            current = tree

        for j in range(len(current.children)):

            if is_a_tag(current.children[j], 'PRON'):
                return True

            # found open clausal complement
            if current.children[j].token['deprel'] == 'xcomp':
                return pronouns_in([current.children[j]])

            # found clausal complement
            if current.children[j].token['deprel'] == 'ccomp':
                return pronouns_in([current.children[j]])

    return False


# return list of TokenNodes with nouns
def find_nouns(trees, candidates=[]):
    for tree in trees:

        if type(tree) == list:
            current = tree[0]
        else:
            current = tree

        for j in range(len(current.children)):

            if 'NOUN' in current.children[j].token['upos']:
                candidates.append(current.children[j])

            # found open clausal complement
            if current.children[j].token['deprel'] == 'xcomp':
                return find_nouns([current.children[j]], candidates)

            # found clausal complement
            if current.children[j].token['deprel'] == 'ccomp':
                return find_nouns([current.children[j]], candidates)

    return candidates
