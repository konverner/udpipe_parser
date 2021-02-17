"""
Constantin Werner. 24.12.2020
const.werner@gmail.com

"""
import time
import re
import requests
import copy
import json
from nltk.tokenize import word_tokenize
from text_preprocessor import TextPreProcessor
#from .text_preprocessor import TextPreProcessor
from conllu import parse_tree
from utilities import *
#from .utilities import *


#####################################################


# class for representation of an expression
class Expression:
    """
  subj: list of dicts
    subjects of the expression

  obj: list of dicts
    ojects of the expression

  pred: list of dicts
    predicates of the expression

  params: list of dicts
    parameters of the expression

  """

    def __init__(self):
        self.subj = []
        self.pred = []
        self.obj = []
        self.params = []

    # insert specific item (subj/obj/pred/param)
    def insert(self, type_name, form, nodes, params=[]):
        if form in ['.', ',']:
            return
        temp = form.split(' | ')
        for i in range(len(temp)):
            if temp[i][0:2] == 'и ':
                temp[i] = temp[i][2:]
            if temp[i][0:4] == 'или ':
                temp[i] = temp[i][4:]

            while len(nodes) < len(temp):
                nodes.append(nodes[-1])
            prep = extract_prep(form)
            dets = extract_dets(form)
            modal_verb = extract_modal_verb(temp[i])
            word = make_word(nodes[i], temp[i], prep, dets, modal_verb)
            flag = 0
            if "{" in word['form']:
                word_copy = copy.deepcopy(word)
                word_copy['form'] = re.findall(r'\{.*\}', word['form'])[0][1:-1]
                word['form'] = re.sub(r'\{.*\} ', '', word['form'])
                word['form'] = re.sub(r'\{.*\}', '', word['form'])
                word['form'] = word['form'].strip()
                if word_copy['form'] != 'не':
                    self.params.append(word_copy)

            if type_name == 'subj':
                if word not in self.subj:
                    for s in self.subj:
                        if word['form'] in s['form']:
                            flag = 1

                if flag == 0:
                    self.subj.append(word)

            if type_name == 'obj':
                for o in self.obj:
                    if word['form'] in o['form']:
                        flag = 1
                if flag == 0:
                    self.obj.append(word)

            if type_name == 'params':
                for o in self.obj:
                    if len(o['form']) > 3:
                        if word['form'] in o['form']:
                            flag = 1
                for p in self.params:
                    if word['form'] in p['form']:
                        flag = 1
                for p in self.pred:
                    if p['form'] in word['form']:
                        flag = 1
                for s in self.subj:
                    if len(s['form']) > 3:
                        if s['form'] in word['form'] or word['form'] in s['form']:
                            flag = 1
                if flag == 0:
                    self.params.append(word)

            if type_name == 'pred':
                if 'не быть' in word['form']:
                    if len(self.pred) == 1 and not 'не быть' in self.pred[0]['form']:
                        word = copy.deepcopy(self.pred[0])
                        word['form'] = 'не ' + self.pred[0]['form']
                        self.pred.append(word)
                    elif len(self.pred) == 0:
                        self.pred.append(word)
                else:
                    for p in self.pred:
                        if word['form'] in p['form']:
                            flag = 1
                    if flag == 0:
                        self.pred.append(word)

        if params != []:
            self.insert('params', params[0][0], params[0][1])

    def is_empty(self):
        return self.pred == '' and self.obj == ''

    def update(self):
        for param in self.params:
            if param['form'] == 'будет':
                for i in range(len(self.pred)):
                    self.pred[i]['tense'] = "Fut"
                self.params = [param for param in self.params if param['form'] != 'будет']
            if param['form'] == 'было':
                for i in range(len(self.pred)):
                    self.pred[i]['tense'] = "Past"
                self.params = [param for param in self.params if param['form'] != 'было']

    def __str__(self):
        formated = 'subj : '

        for subj in self.subj:
            formated += subj['form'] + ', '
        formated += '\n'

        formated += 'pred : '
        for pred in self.pred:
            if pred['modality'] != None:
                formated += str(pred['modality']) + ' ' + pred['form'] + ', '
            else:
                formated += pred['form'] + ', '
        formated += '\n'

        formated += 'obj : '
        for obj in self.obj:
            formated += obj['form'] + ', '
        formated += '\n'

        formated += 'params : '
        for param in self.params:
            formated += param['form'] + ', '
        return formated


#################################################################


class UDPipeParser:
    """
      propn : list of strings
        list of words/phrases that should be treated as proper nouns

      abbrev_dict : dict
        pairs <abbreviation : full form>

  """

    def __init__(self, propn_nouns=[], abbrev_dict={}, lang='ru'):
        self.morph = Morpholog()
        self.preprocessor = TextPreProcessor(propn_nouns=propn_nouns, abbrev_dict=abbrev_dict)
        self.propn_nouns = propn_nouns
        self.logging = False
        self.lang = lang  # for now only russian is available.

    def cann_form(self, sent):
        pred_here = False
        subj_here = False
        tokens = word_tokenize(sent)
        for token in tokens:
            parsed = self.morph.parse(token)
            for p in parsed:
                if p.word.lower() not in self.propn_nouns:
                    if ((('INFN' in p.tag or 'VERB' in p.tag) and ('incl' not in p.tag)) or (
                            'разр' in p.word or 'долж' in p.word or 'нужн' in p.word)):
                        pred_here = p
                if (('NOUN' in p.tag or 'NPRO' in p.tag or 'ADJF' in p.tag or 'ADJS' in p.tag) and (
                        'nomn' in p.tag) or p.word in self.propn_nouns):
                    subj_here = p
        if pred_here == False:
            j = -1
            for i in range(len(tokens)):
                if tokens[i] == 'это':
                    j = i + 1
                    break
            if j == -1:
                if tokens[-1] not in ['.', '!', '?']:
                    tokens.append('есть')
                else:
                    tokens.insert(-1, 'есть')
            else:
                tokens.insert(j, 'есть')
        tokens = ['есть' if token == 'будут' else token for token in tokens]

        if not subj_here:
            if pred_here != False:
                p = pred_here
                if '1per' in p.tag and 'sing' in p.tag:
                    tokens.insert(tokens.index(p.word) - 1, 'я')
                elif '2per' in p.tag and 'sing' in p.tag:
                    tokens.insert(tokens.index(p.word) - 1, 'ты')
                elif '3per' in p.tag and 'sing' in p.tag:
                    tokens.insert(tokens.index(p.word) - 1, 'он')
                elif '1per' in p.tag and 'plur' in p.tag:
                    tokens.insert(token.index(p.word) - 1, 'мы')
                elif '2per' in p.tag and 'plur' in p.tag:
                    tokens.insert(tokens.index(p.word) - 1, 'вы')
                elif '3per' in p.tag and 'plur' in p.tag:
                    tokens.insert(tokens.index(p.word) - 1, 'они')
        return ' '.join(tokens)

    def solve_anaphora(self, trees, candidates=[]):
        """
    params

    ---
    trees : list of conllu tree objects
    candidates : list of udpipe node objects
      nouns that can probably be associated with pronouns
    """
        if candidates == []:
            candidates = find_nouns(trees)

        for tree in trees:

            if type(tree) == list:
                current = tree[0]
            else:
                current = tree

            for j in range(len(current.children)):
                if is_a_tag(current.children[j], 'PRON') and current.children[j].token['feats'] != None:
                    if ('Person' in current.children[j].token['feats'].keys() and 'Gender' in current.children[j].token[
                        'feats'].keys()):
                        if current.children[j].token['feats']['Person'] == '3':
                            for cand in candidates:
                                # check that pronoun and noun are consistent
                                if cand.token['feats']['Gender'] == current.children[j].token['feats']['Gender']:
                                    current.children[j] = cand

                # found open clausal complement
                if is_a_tag(current.children[j], 'VERB'):
                    self.solve_anaphora([current.children[j]], candidates)

        return trees

    def _parse_verb_phrase(self, current, root):
        nodes = [current]
        result = current.token['lemma']
        params = []
        if len(current.children) != 0:
            for k in range(len(current.children)):
                if one_of_these(current.children[k], ['xcomp', 'csubj']):
                    nodes.append(current.children[k])
                    result += ' ' + self._parse_verb_phrase(current.children[k], current)[0]

                elif 'conj' in current.children[k].token['deprel']:
                    nodes.append(current.children[k])
                    result += " | " + self._parse_verb_phrase(current.children[k], current)[0]

                elif each_of_these(current.children[k], ['Loc', 'obl']):
                    params.append(self._parse_noun_phrase(current.children[k], current, tag='lemma'))


                elif each_of_these(current.children[k], ['NOUN', 'advcl']):
                    result += ' ' + self._parse_noun_phrase(current.children[k], root, tag='form')[0]

                if current.children[k].token['lemma'] == 'не':
                    result = current.children[k].token['form'] + ' ' + result
        return result, nodes, params

    def _parse_noun_phrase(self, current, root, tag='lemma'):
        nodes = [current]
        if is_a_tag(current, 'PROPN'):
            result = current.token['lemma']
        else:
            result = current.token[tag]

        for k in range(len(current.children)):
            if is_a_tag(current.children[k], 'ADJ'):
                result += ' ' + current.children[k].token[tag]
                for i in range(len(current.children[k].children)):

                    # E.G. 'физико-математический', where 'физико' is compound
                    if one_of_these(current.children[k].children[i], ['compound']):
                        result = ' '.join(result.split(' ' )[:-1]) + ' ' +current.children[k].children[i].token['form'] + '-' + result.split(' ' )[-1]

                    if one_of_these(current.children[k].children[i], ['PART', 'ADV']):
                        result += ' {' + self._parse_noun_phrase(current.children[k].children[i], None)[0] + '}'

            if current.children[k].token['form'] == 'не':
                result = current.children[k].token['form'] + ' ' + result

            # NUMBER E.G. 'семьсот' OR DETERMINANT E.G. 'мой подарок'
            elif one_of_these(current.children[k], ['NUM', 'DET', 'X']):
                result = current.children[k].token['lemma'] + ' ' + result
                if is_a_tag(current.children[k], 'DET') and len(current.children[k].children) != 0:
                    result += ' {' + self._parse_noun_phrase(current.children[k].children[0], None)[0] + '}'
                else:
                    for j in range(len(current.children[k].children)):
                        result = self._parse_noun_phrase(current.children[k].children[j], current, tag='form')[
                                     0] + ' ' + result

            if one_of_these((current.children[k]), ['NOUN', 'PRON', 'VERB', 'ADV', 'PROPN', 'PART']):
                if 'parataxis' in current.children[k].token['deprel']:
                    result += ' (' + current.children[k].token['form'] + ') '

                elif 'conj' in current.children[k].token['deprel']:
                    nodes.append(current.children[k])
                    result += " | " + self._parse_noun_phrase(current.children[k], current, tag='lemma')[0]

                elif one_of_these(current.children[k], ['PRON', 'PROPN']):
                    result += ' ' + self._parse_noun_phrase(current.children[k], current, tag='form')[0]

                # PARTICLE E.G. 'именно книга'
                elif one_of_these(current.children[k], ['PART', 'ADV']):
                    result += ' {' + self._parse_noun_phrase(current.children[k], current, tag='form')[0] + '}'

                # PARTICIPLE E.G. "повышенный"
                elif each_of_these(current.children[k], ['VERB', 'amod']):
                    result += ' ' + current.children[k].token['form']


                elif one_of_these(current.children[k], ['fixed', 'nmod', 'appos', 'advmod']):
                    # IT IS EXCEPTION, MODEL IS DOING BAD WITH THIS WORD
                    if current.children[k].token['form'] == 'оффлайн':
                        result += ' {' + current.children[k].token['form'] + '}'
                    else:
                        result += ' ' + self._parse_noun_phrase(current.children[k], current, tag='form')[0]

                # NOUN IN GENETIVE CASE E.G. "факультет математики"
                elif ((is_a_case(current.children[k], 'Gen') and prep_in(
                        current.children[k]) == False) or is_a_case(current.children[k], 'Ins')):
                    result += ' ' + self._parse_noun_phrase(current.children[k], current, tag='form')[0]

                # noun in accusative case with some preposition found: справка о доходах
                elif one_of_these(current.children[k], ['Acc', 'Loc']):
                    # looking for prepositions and adjectives
                    for i in range(len(current.children[k].children)):

                        if (is_a_tag(current.children[k].children[i], 'ADP') and current.children[k].children[i].token[
                            'lemma'] != 'в'):
                            result += ' ' + current.children[k].children[i].token['form'] + ' ' + \
                                      current.children[k].token['form']
                        if is_a_tag(current.children[k].children[i], 'NUM'):
                            result += ' ' + current.children[k].children[i].token['form'] + ' ' + \
                                      current.children[k].token['form']
                        if is_a_tag(current.children[k].children[i], 'ADJ'):
                            result += ' ' + current.children[k].children[i].token['lemma']
                        if is_a_tag(current.children[k].children[i], 'CCONJ'):
                            result += ' ' + current.children[k].children[i].token['form'] + ' ' + \
                                      current.children[k].token['form']

        for k in range(len(current.children)):
            if one_of_these(current.children[k], ['ADP', 'CCONJ']):
                result = self._parse_noun_phrase(current.children[k], current, tag='form')[0] + ' ' + result
        return result, nodes

    # IT GOES THROUGH A TREE AND PARSE IT
    # IT STARTS WITH A NODE WHICH IS PREDICATE IF NOT IT STARTS TO SEARCH FOR
    # A PREDICATE NODE TO START WITH
    def traverse_tree(self, tree, expression=Expression(), result=[]):

        result_exp = expression
        current = tree
        visited = [current.token['id']]
        # CHECK IF CURRENT IS PREDICATE NODE
        if not is_a_tag(current, 'VERB') and not is_a_tag(current, 'AUX') and not is_modal_verb(current):
            found = False
            for j in range(len(current.children)):
                if is_a_tag(current.children[j], 'VERB') or is_a_tag(current.children[j], 'AUX'):
                    buffer = current.token
                    current.token = current.children[j].token
                    current.children[j].token = buffer
                    #visited.append(current.children[j].token['id'])
                    found = True
                    break
            # PREDICATE NODE DOES NOT FOUND, SO MAKE A DUMMY NODE WITH PREDICATE
            if not found:
                new_root = copy.deepcopy(current)
                current.children = []
                current.token['deprel'] = 'nsubj'
                current.token['id'] = 21
                new_root.token['form'] = 'быть'
                new_root.token['lemma'] = 'быть'
                new_root.token['upostag'] = 'VERB'
                new_root.children.append(current)
                current = new_root

        # traverse children
        for j in range(len(current.children)):
            curr_child = current.children[j]

            if self.logging:
                print('child of ', current.token['form'], ":", curr_child.token['form'], curr_child.token)

            if 'parataxis' in curr_child.token['deprel']:
                sub_exp = Expression()
                result.insert(0, self.traverse_tree(curr_child, expression=sub_exp, result=[])[0])

            # SUBJECT OR OBJECT
            if 'advmod' not in curr_child.token['deprel'] and one_of_these(curr_child, ['NUM', 'NOUN', 'X', 'ADJ', 'PRON', 'PROPN']):
                # FIRSTLY, WE ARE LOORING FOR SUBJECT
                if 'nsubj' in curr_child.token['deprel'] and not curr_child.token['id'] in visited:
                    result_exp.insert('subj', *self._parse_noun_phrase(curr_child, current))
                    result_exp.insert('pred', *self._parse_verb_phrase(current, current))
                    visited.append(curr_child.token['id'])
                    for child in curr_child.children:
                        visited.append(child.token['id'])

                # IF NSUBJ NODE IS NOT IN THE TREE THEN IOBJ NODE IS A SUBJECT
                elif 'iobj' in curr_child.token['deprel'] and not curr_child.token['id'] in visited:

                    # IF THERE IS A SUBJECT THEN IOBJ IS OBJECT E. G. "Он мне помог"
                    if deprel_in(current, 'subj'):
                        result_exp.insert('obj', *self._parse_noun_phrase(curr_child, current))

                    # IF NOT THEN IT IS A SUBJECT E.G. 'как мне доехать?'
                    else:
                        result_exp.insert('subj', *self._parse_noun_phrase(curr_child, current))
                    visited.append(curr_child.token['id'])
                    for child in curr_child.children:
                        visited.append(child.token['id'])

                # PASSIVE VOICE
                elif (prep_in(curr_child) and (current.token['lemma'] == 'быть' or is_passive_voice(current))
                      and not curr_child.token['id'] in visited):
                    result_exp.insert('params', *self._parse_noun_phrase(curr_child, current))
                    visited.append(curr_child.token['id'])
                    for child in curr_child.children:
                        visited.append(child.token['id'])

                # TIME PARAMETER
                elif prep_in(curr_child) and approx_match(curr_child.token['form'], time_periods):
                    result_exp.insert('params', *self._parse_noun_phrase(curr_child, current))
                    visited.append(curr_child.token['id'])

                # CURRENT CHILD IS INDIRECT OBJECT, ROOT-VERB DOES NOT HAVE DIRECT OBJECT AND OBJECT WAS'T FOUND
                elif ((not is_a_case(curr_child, 'Loc') or is_a_case(curr_child, 'X')) and prep_in(curr_child,
                                                                                                   t='obj')
                      and has_direct_object(current) == False and result_exp.obj == [] and not curr_child.token[
                                                                                                   'id'] in visited):
                    result_exp.insert('obj', *self._parse_noun_phrase(curr_child, current))
                    result_exp.insert('pred', *self._parse_verb_phrase(current, current))
                    visited.append(curr_child.token['id'])
                    for child in curr_child.children:
                        visited.append(child.token['id'])

                # CURRENT CHILD WITH ACC/GEN CASE IS DIRECT OBJECT
                elif (is_trans(current) and (not prep_in(curr_child) and
                                             one_of_these(curr_child, ['Ins', 'Acc', 'Gen',
                                                                       'Dat']) and result_exp.obj == [] and not deprel_in(
                            current, 'csubj') and not curr_child.token['id'] in visited)):

                    result_exp.insert('obj', *self._parse_noun_phrase(curr_child, current))
                    result_exp.insert('pred', *self._parse_verb_phrase(current, current))
                    visited.append(curr_child.token['id'])
                    for child in curr_child.children:
                        visited.append(child.token['id'])

                elif (not is_a_tag(curr_child, 'PUNCT') and curr_child.token['form'] != 'не' and curr_child.token[
                    'form'] != 'нет'):
                    result_exp.insert('params', *self._parse_noun_phrase(curr_child, current))
                    visited.append(curr_child.token['id'])
                    for child in curr_child.children:
                        visited.append(child.token['id'])

            # AUXILIARY VERB THAT MODIFIES TENSE OF MAIN VERB TO FUTURE TENSE
            elif 'aux' in curr_child.token['deprel']:
                if 'будет' == curr_child.token['form']:
                    result_exp.pred[-1]['tense'] = 'Fut'

            # NUMBER AS A PARAMETER
            elif is_a_tag(curr_child, 'NUM') and 'nummod' in curr_child.token['deprel'] and not curr_child.token[
                                                                                                    'id'] in visited:
                result_exp.insert('params', curr_child.token['form'], [curr_child])
                visited.append(curr_child.token['id'])

            # NUMBER AS AN OBJECT
            elif is_a_tag(curr_child, 'NUM') and 'advmod' not in curr_child.token['deprel'] and not curr_child.token[
                                                                                                        'id'] in visited:

                if (((prep_in(curr_child) == False and has_direct_object(current) == True) or
                     (prep_in(curr_child) == True and has_direct_object(
                         current) == False)) and result_exp.obj == []):
                    result_exp.insert('obj', *self._parse_noun_phrase(curr_child, current))
                    result_exp.insert('pred', *self._parse_verb_phrase(current, current))
                else:
                    result_exp.insert('params', *self._parse_noun_phrase(curr_child, current, tag='form'))
                visited.append(curr_child.token['id'])
                for child in curr_child.children:
                    visited.append(child.token['id'])

                for i in range(len(curr_child.children)):
                    if one_of_these(curr_child, ['nmod', 'advmod']) and not curr_child.token['id'] in visited:
                        result_exp.insert('params', *curr_child.children[i].token['lemma'])
                        visited.append(curr_child.token['id'])

            # FOUND CLAUSAL COMPLEMENT
            elif is_a_tag(curr_child, 'VERB') and one_of_these(curr_child, ['csubj:pass', 'csubj', 'xcomp']) and not \
                    curr_child.token['id'] in visited:
                result_exp.insert('pred', *self._parse_verb_phrase(current, current))
                visited.append(curr_child.token['id'])
                if curr_child.token['lemma'] not in result_exp.pred[0]['form']:
                    result_exp.pred[0]['form'] += ' ' + curr_child.token['lemma']
                self.traverse_tree(curr_child, expression=result_exp)

            # CONJUGATION VERB
            elif each_of_these(curr_child, ['VERB', 'conj']):
                self.traverse_tree(curr_child, expression=result_exp)

            # THE REST OF DESCENDANTS ARE POSSIBLE PARAMETERS
            elif (not is_a_tag(curr_child, 'PART') and
                  (one_of_these(curr_child, ['adcvl', 'advmod', 'mark', 'obl']))
                  and not curr_child.token['id'] in visited):
                result_exp.insert('params', *self._parse_verb_phrase(curr_child, current))
                visited.append(curr_child.token['id'])
                for i in range(len(curr_child.children)):
                    if one_of_these(curr_child, ['advmod', 'nmod']):
                        result_exp.insert('params', curr_child.children[i].token['lemma'], [curr_child.children[i]])
                        visited.append(curr_child.children[i].token['id'])

            elif each_of_these(curr_child, ['cop', 'AUX']) and not curr_child.token['id'] in visited:
                result_exp.insert('params', curr_child.token['form'], [curr_child])
                visited.append(curr_child.token['id'])

            elif ('cop' in curr_child.token['deprel'] and curr_child.token['lemma'] != 'быть' and not curr_child.token[
                                                                                                          'id'] in visited):
                result_exp.insert('params', curr_child.token['form'] + ' ' + current.token['form'], [curr_child])
                visited.append(curr_child.token['id'])

            elif 'advcl' in curr_child.token['deprel'] and not curr_child.token['id'] in visited:
                result_exp.insert('params', *self._parse_noun_phrase(curr_child, current, tag='form'))
                visited.append(curr_child.token['id'])
                for child in curr_child.children:
                    visited.append(child.token['id'])

        if result_exp.pred == []:
            if is_a_tag(current, 'NOUN') or is_a_tag(current, 'ADJ'):
                result_exp.insert('pred', form='быть', nodes=[None])
                result_exp.insert('subj', form=current.token['form'], nodes=[current])
            else:
                result_exp.insert('pred', *self._parse_verb_phrase(current, current))
        result_exp.update()
        result.insert(0, result_exp)
        return result

    def parse(self, text, solve_anaphora=False):
        """
        params
        ---

        text : str
          text to parse

        solve_anaphora : bool
          if true then anaphora is to be solved

        return
        ---
        exp : analyzer.Expression object
        """
        request = json.loads(requests.get(
            'http://lindat.mff.cuni.cz/services/udpipe/api/process?model=russian-syntagrus-ud-2.6-200830&tokenizer&tagger&parser&data=' + text).text)
        trees = parse_tree(request['result'])
        if solve_anaphora:
            if len(trees) > 1 and pronouns_in(trees):
                trees = self.solve_anaphora(trees)
        result = []
        for tree in trees:
            new_exp = Expression()
            exps = self.traverse_tree(tree, expression=new_exp, result=[])
            for exp in exps:
                result.append(exp)

        return result

    def run(self, text, solve_anaphora=False, logging=False):

        start_time = time.time()
        self.logging = logging

        text = self.cann_form(text)
        text = self.preprocessor.run(text)
        if logging:
            print("sent:", text)
        result = self.parse(text.strip(' '), solve_anaphora=solve_anaphora)

        end_time = time.time()

        if self.logging:
            print('[UDPipeParser] elapsed time:', end_time - start_time)

        return result


