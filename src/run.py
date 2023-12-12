from udmodel import *
import argparse
import os
from openai import OpenAI
import time

class llm_UD:

    def __init__(self,args):
        self.test = UDModel().parseConllu(args.PATHtest)
        self.train = UDModel().parseConllu(args.PATHtrain)
        self.gpt_client = OpenAI(api_key=args.openkey)
        self.matchs_DDA = {}
        self.matchs_UDA = {}
        self.syntatic_relations_testset = {}



    def process_chatgpt_message(self,message,model_chat='gpt-3.5-turbo'):
        messages = []

        if message:
          messages.append({'role':'user','content':message},
                          )
          chat = self.gpt_client.chat.completions.create(
              model =model_chat,messages=messages
          )

        reply = chat.choices[0].message.content

        return reply

    def getDepRelationsChat(self,message):
        relations_text = message.replace('"','').split('\n')[2:]
        dep_relations = []


        for line in relations_text:
          dep  = line.split('<')[1].split(',')[0].strip()
          head = line.split('<')[1].split(',')[1].split('>')[0].strip()
          dep_relations.append((dep,head))

        return dep_relations

    def compare(self,chatResponse,UDresponse):
      
      DDA = [0,len(UDresponse)]
      UDA = [0,len(UDresponse)]

      relations_pairs = []

      for r in UDresponse:

          relations_pairs.append('%s<#>%s' % (r['DEP'].lower(),r['HEAD'].lower()))

          if r['DEPREL'] not in self.syntatic_relations_testset:
            self.syntatic_relations_testset[r['DEPREL']] = 0

          if r['DEPREL'] not in self.matchs_UDA:
          	self.matchs_UDA[r['DEPREL']] = 0

          if r['DEPREL'] not in self.matchs_DDA:
          	self.matchs_DDA[r['DEPREL']] = 0


          self.syntatic_relations_testset[r['DEPREL']] += 1
      relations_pairs_buffer = relations_pairs.copy()


      for index_pair,chatRelation in enumerate(chatResponse):

          chatR_dh  = '%s<#>%s' % (chatRelation[1].lower(),chatRelation[0].lower())
          chatR_hd  = '%s<#>%s' % (chatRelation[0].lower(),chatRelation[1].lower())
          


          if chatR_dh in relations_pairs_buffer:
            index_relation = relations_pairs.index(chatR_dh)

            self.matchs_UDA[UDresponse[index_relation]['DEPREL']] += 1
            self.matchs_DDA[UDresponse[index_relation]['DEPREL']] += 1
            DDA[0] += 1
            UDA[0] += 1
            relations_pairs_buffer.remove(chatR_dh) #To avoid compare to the same relation

          elif chatR_hd in relations_pairs_buffer:
            index_relation = relations_pairs.index(chatR_hd)

            self.matchs_UDA[UDresponse[index_relation]['DEPREL']] += 1
            UDA[0] += 1

            relations_pairs_buffer.remove(chatR_hd) #To avoid compare to the same relation
      
      return UDA, DDA

    def computeResults(self,writerR):

          # del self.syntatic_relations_testset['root']
          # del self.matchs_UDA['root']
          # del self.matchs_DDA['root']              	  
          writerR.write('UDA %.3f\n' % (sum(self.matchs_UDA.values())/sum(self.syntatic_relations_testset.values())))
          writerR.write('DDA %.3f\n' % (sum(self.matchs_DDA.values())/sum(self.syntatic_relations_testset.values())))

          for sy_rel, value in self.syntatic_relations_testset.items():
           writerR.write('%s;%.3f;%.3f;%d\n' % (sy_rel,self.matchs_UDA[sy_rel]/self.syntatic_relations_testset[sy_rel],
                                            self.matchs_DDA[sy_rel]/self.syntatic_relations_testset[sy_rel],self.syntatic_relations_testset[sy_rel]))



    def testOneShot(self):
      guide = """Na frase "Todos os adversários de Tótó foram eliminados ." as relações de dependência <token dependente, token cabeça>
      são as seguintes
      <todos, adversários>
      <os, adversários>
      <adversários, eliminados>
      <de, totó>
      <totó, adversários>
      <foram, eliminados>"""

      PATH = '/'.join(os.getcwd().split('/')[0:-1])
      if 'results' not in os.listdir(PATH):
          os.mkdir('%s/results' % PATH)

      save_PATH = '%s/results/one_shot_results.txt' % (PATH)
      save_PATH_error = '%s/results/error.txt' % (PATH)

      writerR = open(save_PATH,'w')
      writerE = open(save_PATH_error,'w')
      out_pattern = 0
      for index,sample in enumerate(self.test):
        
        depRel = sample[0]
        sentence = sample[1]
        


        message = """%s\nAgora liste as relações de dependência na frase 
                       "%s" 
                       em pares usando <token dependente, token cabeça>""" % (guide,sentence)

        try:
          llm = self.getDepRelationsChat(self.process_chatgpt_message(message))
          r = self.compare(llm,depRel)
          sentence_chat = '<#>'.join(['%s<@>%s' % (r[0],r[1]) for r in llm])
          sentence_dep  = '<#>'.join(['%s<@>%s<@>%s' % (d['DEP'],d['HEAD'],d['DEPREL']) for d in depRel])
          writerR.write('chatGPT|:|%s|:|UDA:%.3f<#>DDA: %.3f\n' % (sentence_chat,r[0][0]/r[0][1],r[1][0]/r[1][1]))
          writerR.write('DepRel |:|%s\n' % sentence_dep)
          writerR.write('>--<\n')
        except:
          writerE.write('ERROR-chatGPT:[[%s]]\n' % message)
          writerE.write('ERROR-DepRel % s\n' % str([(d['DEP'],d['HEAD'],d['DEPREL']) for d in depRel]))
          writerR.write('>--<\n')
          out_pattern += 1
          continue

        if index % 10 == 0:
          print('%.3f %% concluded ' % ((index/100)*100))
          print('%.3f %% out of pattern' % ((out_pattern/100)*100))

        if index == 100:
          break
      self.computeResults(writerR)
        
def formatTime(time_):

  miliseconds = str(time_).split('.')[1]
  totalseconds = int(str(time_).split('.')[0])
  hours = totalseconds // 3600
  minutes = (totalseconds % 3600) // 60
  seconds = (totalseconds % 3600) % 60

  print('%02d:%02d:%02d,%s' % (hours,minutes,seconds,miliseconds))

if "__main__":
    parser = argparse.ArgumentParser(description='UDmodel')
    parser.add_argument('--PATHtest',type=str,default=0,help='CONLLU test file')
    parser.add_argument('--PATHtrain',type=str,default=0,help='CONLLU train file')
    parser.add_argument('--openkey',type=str,default='',help='openkey from openAI API')
    args = parser.parse_args()
    model = llm_UD(args)
    start = time.time()
    model.testOneShot()
    end = time.time()-start
    formatTime(end)

