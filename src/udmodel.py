class UDModel:


  def parseLine(self,const):
      """We used the same terms described in https://universaldependencies.org/format.html at 26 September 2023"""

      field = const.split('\t')
      distance = abs(int(field[0])-int(field[6]))


      return {'distance_dep_relation':distance,
              'ID':field[0],
              'FORM':field[1],
              'lema_pos':'%s_%s' % (field[2],field[3]),
              'LEMMA':field[2],
              'UPOS':field[3],
              'XPOS':field[4],
              'FEATS':field[5],
              'HEAD':field[6],
              'DEPREL':field[7]}

  def end_sentence__(self,line):
      return True if len(line) == 0 else False

  def is_validconst__(self,line):
      idtoken = line.split()[0]

      return True if idtoken[0].isdigit() and ('.' not in idtoken and '-' not in idtoken) else False


  def getSentenceDepRelations(self,sentence):
      deprel = []
      ids = dict([(const['ID'],const['FORM']) for const in sentence])
      idspos = dict([(const['ID'],const['UPOS']) for const in sentence])


      for line in sentence:
        if ':' in line['DEPREL']:
          line['DEPREL'] = line['DEPREL'].split(':')[0]

        if line['HEAD'] == '0':
          deprel.append({'HEAD':'root',
                        'DEP':line['FORM'],
                        'DEPREL':line['DEPREL'],
                        'UPOSD':line['UPOS'],
                        'UPOSH':line['UPOS'],
                        'distance_dep_relation':line['distance_dep_relation']})
        else:
          deprel.append({'HEAD':ids[line['HEAD']],
                        'DEP':line['FORM'],
                        'UPOSD':line['UPOS'],
                        'UPOSH':idspos[line['HEAD']],
                        'DEPREL':line['DEPREL'],
                        'distance_dep_relation':line['distance_dep_relation']})


      return deprel


  def get_sentence_form(self,sentence):

      return ' '.join([const['FORM'] for const in sentence])


  def parseConllu(self,data_CONLLU):
      conllu_parsed = []
      es = 0

      sentence = []

      for line in open(data_CONLLU).read().split('\n'):

          if self.end_sentence__(line):
            conllu_parsed.append((self.getSentenceDepRelations(sentence),self.get_sentence_form(sentence)))
            sentence = []
            es += 1

          elif self.is_validconst__(line):
            sentence.append(self.parseLine(line))

      

      print('%s\n%d Sentences\n%d dependency relations' % (data_CONLLU,len(conllu_parsed[1:-1]),sum([len(i[0]) for i in conllu_parsed[1:-1]])))
      return conllu_parsed[1:-1]