'''
Constantin Werner. 24.12.2020
const.werner@gmail.com

'''
import time
import re
import requests
import json
import udpipe_analyzer.text_preprocessor
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from morpholog import Morpholog
from udpipe_analyzer.text_preprocessor import TextPreProcessor
from conllu import parse_tree


obj_preps = ['о','к','об','на','про','в','во','с', 'по','насчет', 'относительно','за','из','у','для']
preps = ['о','к','об','на','про','в','во','с', 'по','насчет', 'относительно','за','из','у','для','при','по','перед','после']
dets = ['какой то','какой-то','какой','тот','этот','это','такой','что за','что','сколько']

########### UTILITY FUNCTIONS #################

# utility function for checking pos-tag of udpipe node
def is_a_tag(node, tag):
  if (tag == node.token['upostag'] or tag == node.token['upos']):
    return True
  return False

# check voice parameter of udpipe node
def is_passive_voice(node):
  if 'feats' in node.token.keys():
    if 'Voice' in node.token['feats'].keys():
      if 'Pass' in node.token['feats']['Voice']:
        return True
      else:
        return False
  return False

# check case parameter of udpipe node
def is_a_case(node,case):
  if is_a_tag(node,'X'):
    return True
  if 'feats' in node.token.keys():
    if node.token['feats'] != None:
      if 'Case' in node.token['feats'].keys():
        if case in node.token['feats']['Case']:
          return True
        else:
          return False
    else:
      return False
  return True


# make dict for a word from udpipe node 
def make_word(node,form,prep=None, dets=[]):
  w = dict()
  
  w['pos'] = node.token['upostag']
  w['polarity'] = 'affirmative'

  if 'feats' in node.token.keys():
    if node.token['feats'] != None:
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

  if prep != None:
    w['form'] = ' '.join(form.split(' ')[1:]).lower()
  else:
    w['form'] = form.lower()
  if dets != []:
    for det in dets:
      w['form'] = (w['form'][:w['form'].find(det)] + w['form'][w['form'].find(det)+len(det):]).strip()

  w['prep'] = prep
  w['dets'] = dets
  return w

# extract prepositions from a word
def extract_prep(word):
  if word.split()[0] in preps:
      return word.split()[0]
  return None

# extract determiners from a word
def extract_dets(word):
  result = []
  for det in dets:
    if det + ' ' in word or ' ' + det + ' ' in word:
      result.append(det)
  return result


#####################################################


# class for representation of an expression
class Expression:
  '''
  subj: list of dicts
    subjects of the expression

  obj: list of dicts
    ojects of the expression

  pred: list of dicts
    predicates of the expression
  
  params: list of dicts
    parameters of the expression
    
  '''
  def __init__(self,subj=[],pred=[],obj=[],parameters=[]):
    self.subj = []
    self.pred = []
    self.obj = []
    self.params = []

  # insert specific item (subj/obj/pred/param)
  def insert(self,type_name,form,nodes,params=[]):
    temp = form.split(' | ')
    for i in range(len(temp)):
      if temp[i][0:2] == 'и ':
        temp[i] = temp[i][2:]
      while (len(nodes) < len(temp)):
        nodes.append(nodes[-1])
      prep = extract_prep(form)
      dets = extract_dets(form)
      word = make_word(nodes[i], temp[i], prep, dets)

      flag = 0
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
        for o,p in zip(self.obj,self.params):
          if word['form'] in p['form'] or word['form'] in o['form']:
            flag = 1
        if flag == 0:
          self.params.append(word)

      if type_name == 'pred':
        for p in self.pred:
          if word['form'] in p['form']:
            flag = 1
        if flag == 0:     
          self.pred.append(word)
    
    if params != []:
      self.insert('params',params[0][0],params[0][1])        


  def is_empty(self):
    return self.pred == '' and self.obj == ''

  def __str__(self):
    formated = 'subj : '
    
    for subj in self.subj:
      formated += subj['form'] + ', '
    formated += '\n'

    formated += 'pred : '
    for pred in self.pred:
      if pred['polarity'] == 'negative':  
        formated += 'не ' + pred['form'] + ', '
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


class Analyzer:
  '''
  propn : list of strings
    list of words/phrases that should be treated as proper nouns

  '''
  def __init__(self, propn_nouns={}):
    self.morph =  Morpholog()
    self.preprocessor = TextPreProcessor(replace_words=propn_nouns)
    self.propn = propn_nouns
    self.logging = False


  def cann_form(self, sent):
    pred_here = False
    subj_here = False
    tokens = word_tokenize(sent)
    for token in tokens:
      parsed = self.morph.parse(token)
      for p in parsed:
        if ( (('INFN' in p.tag or 'VERB' in p.tag) and ('incl' not in p.tag) ) or ('долж' in p.word or 'нужн' in p.word)):
          pred_here = p
        if (('NOUN' in p.tag or 'NPRO' in p.tag or 'ADJF' in p.tag or 'ADJS' in p.tag) and ('nomn' in p.tag) or p.word in self.propn):
          subj_here = p
    
    if pred_here == False:
      j = -1
      for i in range(len(tokens)):
        if tokens[i] == 'это':
          j = i+1
          break
      if j == -1:
        if tokens[-1] not in ['.','!','?']:
          tokens.append('есть')
        else:
          tokens.insert(-1,'есть')
      else:
        tokens.insert(j,'есть')
      

    if subj_here == False:
      if pred_here != False:
        p = pred_here
        if '1per' in p.tag and 'sing' in p.tag:
          tokens.insert(tokens.index(p.word)-1,'я')
        elif '2per' in p.tag and 'sing' in p.tag:
          tokens.insert(tokens.index(p.word)-1,'ты')
        elif '3per' in p.tag and 'sing' in p.tag:
          tokens.insert(tokens.index(p.word)-1,'он')
        elif '1per' in p.tag and 'plur' in p.tag:
          tokens.insert(token.index(p.word)-1,'мы')
        elif '2per' in p.tag and 'plur' in p.tag:
          tokens.insert(tokens.index(p.word)-1,'вы')
        elif '3per' in p.tag and 'plur' in p.tag:
          tokens.insert(tokens.index(p.word)-1,'они')
    return ' '.join(tokens)

  # return list of TokenNodes with nouns
  def find_nouns(self,trees, candidates=[]):

    for tree in trees:

      if (type(tree) == list):
        current = tree[0]
      else:
        current = tree

      for j in range(len(current.children)):

        if ('NOUN' in current.children[j].token['upos']):
            candidates.append(current.children[j])

          
        # found open clausal complement
        if (current.children[j].token['deprel'] == 'xcomp'):
          return self.find_nouns([current.children[j]], candidates)

        # found clausal complement
        if (current.children[j].token['deprel'] == 'ccomp'):
          return self.find_nouns([current.children[j]], candidates)

    return candidates


  # True if there is at least one pronoun in sentences
  # False else
  def pronouns_in(self,trees):

    for tree in trees:

      if (type(tree) == list):
        current = tree[0]
      else:
        current = tree

      for j in range(len(current.children)):

        if (is_a_tag(current.children[j],'PRON')):
          return True

            
        # found open clausal complement
        if (current.children[j].token['deprel'] == 'xcomp'):
          return self.pronouns_in([current.children[j]])

        # found clausal complement
        if (current.children[j].token['deprel'] == 'ccomp'):
          return self.pronouns_in([current.children[j]])
    
    return False



  def solve_anaphora(self, trees, candidates=[]):
    '''
    params

    ---
    trees : list of conllu tree objects
    candidates : list of udpipe node objects
      nouns that can probably be associated with pronouns
    '''
    if (candidates == []):
      candidates = self.find_nouns(trees)

    for tree in trees:
      
      if (type(tree) == list):
        current = tree[0]
      else:
        current = tree

      for j in range(len(current.children)):
          if (is_a_tag(current.children[j],'PRON') and  current.children[j].token['feats'] != None):
              if ('Person' in current.children[j].token['feats'].keys() and 'Gender' in current.children[j].token['feats'].keys()):
                if (current.children[j].token['feats']['Person'] == '3'):
                    for cand in candidates:
                      # check that pronoun and noun are consistent 
                      if (cand.token['feats']['Gender'] == current.children[j].token['feats']['Gender']):
                        current.children[j] = cand

            
          # found open clausal complement
          if (is_a_tag(current.children[j],'VERB')):
            self.solve_anaphora([current.children[j]], candidates)

    return trees


  def prep_in(self, node, t = 'any'):
    for i in range(len(node.children)):
      if (is_a_tag(node.children[i],"ADP") and t == 'any'):
        return True
      elif (is_a_tag(node.children[i],"ADP") and node.children[i].token['form'] in obj_preps and t == 'obj'):
        return True
    return False

  def deprel_in(self,node,deprel):
    for i in range(len(node.children)):
      if (deprel == node.children[i].token['deprel']):
        return True
    return False

  

  def has_direct_object(self, node):

    nouns_have_prep = []

    for j in range(len(node.children)):
      if (is_a_tag(node.children[j],'NOUN') or is_a_tag(node.children[j],'ADJ') or\
       (is_a_tag(node.children[j],'NUM') and 'advmod' not in node.children[j].token['deprel'])):
        nouns_have_prep.append(self.prep_in(node.children[j]))
    if (False in nouns_have_prep):
      return True
    else:
      return False

  def _parse_verb_phrase(self,current,root):

    nodes = [current]
    result = current.token['lemma']
    params = []
    if len(current.children) != 0:
        for k in range(len(current.children)):
            if 'xcomp' in current.children[k].token['deprel']:
                nodes.append(current.children[k])
                result += ' ' + self._parse_verb_phrase(current.children[k],current)[0]

            elif 'conj' in current.children[k].token['deprel']:
                nodes.append(current.children[k])
                result += " | " + self._parse_verb_phrase(current.children[k],current)[0]

            elif ('obl' in current.children[k].token['deprel'] and is_a_case(current.children[k],'Loc')):
              params.append(self._parse_noun_phrase(current.children[k],current,tag='lemma'))


            elif (is_a_tag(current,'NOUN') and 'advcl' in current.token['deprel']):     
              result += ' ' + self._parse_noun_phrase(current.children[k],root,tag='form')[0]

            if ('не ' in current.children[k].token['lemma']):
              result = current.children[k].token['form'] + ' ' + result
    return result, nodes,params


  def _parse_noun_phrase(self,current, root,tag='lemma'):
      nodes = [current]
      if is_a_tag(current,'PROPN'):
        result = current.token['form']
      else:
        result = current.token[tag]

      for k in range(len(current.children)):
        if (is_a_tag(current.children[k],'ADJ')):
          result += ' ' + current.children[k].token[tag]

        if (current.children[k].token['form'] == 'не'):
          result = current.children[k].token['form'] + ' ' + result

        # NUMBER E.G. 'семьсот' OR DETERMINANT E.G. 'мой подарок'
        elif (is_a_tag(current.children[k],'NUM') or is_a_tag(current.children[k],'DET') or is_a_tag(current.children[k],'X')):
          result = current.children[k].token['lemma'] + ' ' + result

        
        if is_a_tag(current.children[k],'NOUN') or is_a_tag(current.children[k],'PRON') or is_a_tag(current.children[k],'PROPN') or is_a_tag(current.children[k],'VERB'):
          if 'conj' in current.children[k].token['deprel']:
            nodes.append(current.children[k])
            result += " | " + self._parse_noun_phrase(current.children[k],current,tag='lemma')[0]

          elif (is_a_tag(current.children[k],'PRON') or is_a_tag(current.children[k],'PROPN')):
            result += ' ' + current.children[k].token['lemma']

          # PARTICIPLE E.G. "повышенный" 
          elif (is_a_tag(current.children[k],'VERB') and 'amod' in current.children[k].token['deprel']):
            result += ' ' + current.children[k].token['form']

          elif  (('nmod' in current.children[k].token['deprel'] or 'appos' in current.children[k].token['deprel'])):
            result += ' ' + self._parse_noun_phrase(current.children[k],current,tag='form')[0]

          # NOUN IN GENETIVE CASE E.G. "факультет математики"      
          elif ( (is_a_case(current.children[k],'Gen') and self.prep_in(current.children[k]) == False) or is_a_case(current.children[k],'Ins') ):
            result += ' ' + self._parse_noun_phrase(current.children[k],current,tag='form')[0]

          # noun in accusative case with some preposition found: справка о доходах       
          elif ( is_a_case(root.children[k],'Acc') or is_a_case(root.children[k],'Loc')):
            # looking for prepositions and adjectives
            for i in range(len(current.children[k].children)):

              if (is_a_tag(current.children[k].children[i],'ADP') and current.children[k].children[i].token['lemma'] != 'в'):
                result += ' ' + current.children[k].children[i].token['form'] + ' ' + current.children[k].token['form']
              if (is_a_tag(current.children[k].children[i],'NUM')):
                result += ' ' + current.children[k].children[i].token['form'] + ' ' + current.children[k].token['form']
              if (is_a_tag(current.children[k].children[i],'ADJ')):
                result += ' ' + current.children[k].children[i].token['lemma']
              if (is_a_tag(current.children[k].children[i],'CCONJ')):
                result += ' ' + current.children[k].children[i].token['form'] + ' ' + current.children[k].token['form']

      for k in range(len(current.children)):
        if (is_a_tag(current.children[k],'ADP') or is_a_tag(current.children[k],'CCONJ')):
          result = current.children[k].token['lemma'] + ' ' + result
      return result, nodes


  def traverse_tree(self, tree, expression=Expression()):
    result_exp = expression
    current = tree

    ### traverse children
    for j in range(len(current.children)):
      curr_child =  current.children[j]
      
      if self.logging:
        print('child of ', current.token['form'], ":" ,curr_child.token['form'],curr_child.token)

      # SUBJECT OR OBJECT
      if ((is_a_tag(curr_child,'PUNCT') == False and 'advmod' not in curr_child.token['deprel']) and (is_a_tag(curr_child,'X') or is_a_tag(curr_child,'NOUN') \
        or is_a_tag(curr_child,'ADJ') or is_a_tag(curr_child,'PRON') or is_a_tag(curr_child,'PROPN') or is_a_tag(curr_child,'NUM'))):

        # FIRSTLY, WE ARE LOORING FOR SUBJECT
        if ( 'nsubj' in curr_child.token['deprel']):
          
          result_exp.insert('subj',*self._parse_noun_phrase(curr_child,current))

          result_exp.insert('pred',*self._parse_verb_phrase(current,current))

          for i in range(len(curr_child.children)): 
            if self.prep_in(curr_child.children[i]):
              result_exp.insert('params',*self._parse_noun_phrase(curr_child.children[i],curr_child))

        # IF NSUBJ NODE IS NOT IN THE TREE THEN IOBJ NODE IS A SUBJECT
        elif ('iobj' in curr_child.token['deprel']):
          if (self.deprel_in(current,'nsubj') == False):
            result_exp.insert('subj',*self._parse_noun_phrase(curr_child,current))
          else:
            result_exp.insert('obj',*self._parse_noun_phrase(curr_child,current))

        elif ( self.prep_in(curr_child) and (current.token['lemma'] == 'быть' or is_passive_voice(current)) ):
          result_exp.insert('params',*self._parse_noun_phrase(curr_child,current))


        # CURRENT CHILD IS INDIRECT OBJECT, ROOT-VERB DOES NOT HAVE DIRECT OBJECT AND OBJECT WAS'T FOUND
        elif ( (not is_a_case(curr_child, 'Loc') or is_a_case(curr_child, 'X') ) and self.prep_in(curr_child, t='obj') and self.has_direct_object(current) == False and result_exp.obj == []):
          result_exp.insert('obj',*self._parse_noun_phrase(curr_child,current))
          result_exp.insert('pred',*self._parse_verb_phrase(current,current))

        # CURRENT CHILD WITH ACC/GEN CASE IS DIRECT OBJECT
        elif (self.prep_in(curr_child) == False and (is_a_case(curr_child,'Ins') or is_a_case(curr_child,'Acc') or is_a_case(curr_child,'Gen')) and result_exp.obj == []):
          result_exp.insert('obj',*self._parse_noun_phrase(curr_child,current))
          result_exp.insert('pred',*self._parse_verb_phrase(current,current))

        else:
          result_exp.insert('params',*self._parse_noun_phrase(curr_child,current))

      # NUMBER AS A PARAMETER    
      elif is_a_tag(curr_child,'NUM') and 'nummod' in curr_child.token['deprel']:
        result_exp.insert('params',curr_child.token['form'])
      
      # NUMBER AS AN OBJECT
      elif is_a_tag(curr_child,'NUM') and 'advmod' not in curr_child.token['deprel']:

        if (((self.prep_in(curr_child) == False and self.has_direct_object(current) == True) or\
         (self.prep_in(curr_child) == True and self.has_direct_object(current) == False)) and result_exp.obj == []):
          result_exp.insert('obj',*self._parse_noun_phrase(curr_child,current))
          result_exp.insert('pred',*self._parse_verb_phrase(current,current))
        else:
          result_exp.insert('params',*self._parse_noun_phrase(curr_child,current,tag='form'))

        for i in range(len(curr_child.children)):
          if ('advmod' in curr_child.children[i].token['deprel'] or 'nmod' in curr_child.children[i].token['deprel']):
            result_exp.insert('params',*curr_child.children[i].token['lemma'])

      # NEGOTATION OF PREDICATE
      elif (curr_child.token['form'] == 'не'):
        result_exp.pred[-1]['polatiry'] = 'negative'

      # FOUND CLAUSAL COMPLEMENT
      elif ( is_a_tag(curr_child,'VERB') and ('xcomp' in curr_child.token['deprel'] or 'csubj' in curr_child.token['deprel'])):
        result_exp.insert('pred',*self._parse_verb_phrase(current,current))
        if curr_child.token['form'] not in result_exp.pred[0]['form']:
          result_exp.pred[0]['form'] += ' ' + curr_child.token['form']
        return self.traverse_tree(curr_child, expression=result_exp)

      # THE REST OF DESCENDANTS ARE POSSIBLE PARAMETERS
      elif ( (is_a_tag(curr_child,'ADV') or is_a_tag(curr_child,'ADJ') or is_a_tag(curr_child,'NUM') or is_a_tag(curr_child,'PROPN')) and ('advcl' in curr_child.token['deprel'] or 'advmod' in curr_child.token['deprel'])):
        result_exp.insert('params',*self._parse_verb_phrase(curr_child,current))
        for i in range(len(curr_child.children)):
          if ('advmod' in curr_child.children[i].token['deprel'] or 'nmod' in curr_child.children[i].token['deprel']):
            result_exp.insert('params',curr_child.children[i].token['lemma'],[curr_child.children[i]])

      elif ( 'cop' in curr_child.token['deprel'] and is_a_tag(curr_child,'AUX')):
        result_exp.insert('params',curr_child.token['form'],[curr_child])

      elif ( 'cop' in curr_child.token['deprel'] ):
        result_exp.insert('params',curr_child.token['form'] + ' ' + current.token['form'], [curr_child])

      elif ( 'advcl' in curr_child.token['deprel'] ):
        result_exp.insert('params',*self._parse_noun_phrase(curr_child,current,tag='form'))

    if result_exp.pred == []:
      result_exp.insert('pred',*self._parse_verb_phrase(current,current))
    return result_exp


                
  def parse(self, text,solve_anaphora=False):
    '''
    params
    ---

    text : str
      text to parse

    solve_anaphora : bool
      if true then anaphora is to be solved

    return
    ---
    exp : analyzer.Expression object
    '''
    request = json.loads(requests.get('http://lindat.mff.cuni.cz/services/udpipe/api/process?model=russian-syntagrus-ud-2.6-200830&tokenizer&tagger&parser&data='+text).text)
    trees = parse_tree(request['result'])
    if (solve_anaphora):
      if (len(trees) > 1 and self.pronouns_in(trees)):
        trees = self.solve_anaphora(trees)
    result = []
    for tree in trees:
      exp = Expression()
      exp.params = []
      result.append(self.traverse_tree(tree,expression=exp))

    return result


  def run(self, text,solve_anaphora=False,logging=False):

    start_time = time.time()
    self.logging = logging

    result = []
    sent = self.cann_form(text)
    sent = self.preprocessor.run(sent)
    if (logging):
      print("sent:",sent)
    result = self.parse(sent.strip(' '),solve_anaphora=solve_anaphora)
    
    
    end_time = time.time()
    
    if (self.logging):
      print('[ANALYZER] elapsed time:', end_time - start_time)
    
    return result
