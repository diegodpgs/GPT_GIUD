from udmodel import *
import argparse
import os
from openai import OpenAI


class llm_UD:

	def __init__(self,args):
		self.test = UDModel().parseConllu(args.PATHtest)
		self.train = UDModel().parseConllu(args.PATHtrain)
		self.gpt_client = OpenAI(api_key=args.openkey)




if "__main__":
	parser = argparse.ArgumentParser(description='UDmodel')
	parser.add_argument('--PATHtest',type=str,default=0,help='CONLLU test file')
	parser.add_argument('--PATHtrain',type=str,default=0,help='CONLLU train file')
	parser.add_argument('--openkey',type=str,default='',help='openkey from openAI API')
	args = parser.parse_args()
	model = llm_UD(args)
