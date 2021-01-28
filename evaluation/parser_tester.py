import pandas as pd
from udpipe_parser import UDPipeParser
import time

###### TESTER CLASS ###########

class Tester:
    def __init__(self, TESTDATA_PATH):
        self.test_data = pd.DataFrame(pd.read_csv(TESTDATA_PATH, sep=",", header=0, index_col=False))

    def extract_forms(self, word_dicts):
        result = []
        for wd in word_dicts:
            form = wd['form']
            if 'modality' in wd.keys() and wd['modality'] != None:
                form = wd['modality'] + ' ' + form
            result.append(form)
        return result

    def run(self, parser):
        errors = 0
        i = 2
        start_time = time.time()
        for key, subj, pred, obj, params in zip(self.test_data['key'], self.test_data['subj'], self.test_data['pred'],
                                                self.test_data['obj'], self.test_data['params']):

            if type(subj) == str:
                subj = [s.strip(' ') for s in subj.split(',') if s != ' ']
            else:
                subj = []

            if type(obj) == str:
                obj = [o.strip(' ') for o in obj.split(',') if o != ' ']
            else:
                obj = []

            if type(params) == str:
                params = [param.strip(' ') for param in params.split(',') if param != ' ']
            else:
                params = []

            if type(pred) == str:
                pred = [p.strip(' ') for p in pred.split(',') if p != ' ']
            else:
                pred = []

            exps = parser.run(key)
            flag = False
            for q in exps:
                if (set(subj) & set(self.extract_forms(q.subj)) == set(subj) and set(pred) & set(
                        self.extract_forms(q.pred)) == set(pred) \
                        and set(obj) & set(self.extract_forms(q.obj)) == set(obj) and set(params) & set(
                            self.extract_forms(q.params)) == set(params)):
                    print(str(i) + "#", "PASSED")
                    flag = True
                    break
            if (flag == False):
                print(str(i) + "#", 'FAILED')
                errors += 1
            i += 1
        end_time = time.time()
        print('accuracy =', 1 - errors / i)
        print('time ellapsed =', end_time - start_time)
        print('average time:', (end_time - start_time) / i)
        print('number of tests:', i)


#############################################


propn_nouns = ['c\+\+', 'пми', 'мкн', 'мца', 'нсунет', 'nsunet', 'нгу', 'ммф', "эф", 'ги', 'ггф', 'фф', 'фит', 'ифип',
               'стц', 'пгас', 'фен', 'цввр']
P = UDPipeParser(propn_nouns=propn_nouns)

tester = Tester(r'C:\Users\const\Google Диск\bot\test_data.csv')
tester.run(P)
