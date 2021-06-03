import pandas as pd
import json
import os
import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import simple_preprocess
import multiprocessing
import configparser

# parse config file
config = configparser.ConfigParser()
config.read('config.ini')
if not 'DEFAULT' in config:
	exit('config.ini needs a DEFAULT section')
default_config = config['DEFAULT']
data_dir = default_config.get('Data', './Data')
if not os.path.isdir(data_dir):
	exit('Data directory in config.ini does not exist')
randomness = int(default_config.get('Randomness', 1))
es_url = default_config.get('Elasticsearch', 'localhost:9200')
target_user_id = default_config.get('User')

# get all messages to user and their replies
messages = []
for filename in os.listdir(data_dir):
	if filename.endswith('.json'):
		# open all json files in data_dir
		with open(os.path.join(data_dir, filename), encoding='utf-8') as f:
			channel_messages = json.loads(f.read())['messages'] # all messages in channel data
			filtered_messages = []
			for i, m in enumerate(channel_messages, start=1):
				# extend messages with target users messages and their preceeding message
				if m['author']['id'] == target_user_id:
					prev_m = channel_messages[i-1]
					messages.append([prev_m['content'], prev_m['author']['id'], False])
					messages.append([m['content'], m['author']['id'], True])

df = pd.DataFrame(messages)
df.columns = ['text', 'user_id', 'is_from_user']

# combines sequential messages by the same user into a single message
def make_sentances(series):
	return '. '.join(series)

train_data = pd.DataFrame(columns=['text', 'response'])

for person in pd.unique(df['user_id']):
	conversation = df[df['user_id'] == person]
	grouped = (conversation.groupby(conversation.is_from_user.diff()
			.ne(0).cumsum(), as_index=False)
			.agg({'text':make_sentances,'is_from_user':'first',
			'user_id':'first'}))
	
	tmp = pd.DataFrame({'text':list(conversation['text'][0:-1]),
			'response':list(conversation['text'][1:])})
	
	train_data = train_data.append(tmp[['text','response']],
			ignore_index=True)

train_data['text'] = train_data['text'].apply(lambda x: x.lower())
train_data['response'] = train_data['response'].apply(lambda x: x.lower())

# option 1: elastisearch
# actually relates messages with responses, but not very good for an interesting chatbot
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from random import randint

es = Elasticsearch([es_url])

texts_dict = train_data.to_dict(orient='records')
bulk(es, texts_dict, index='textbot', doc_type='clue', raise_on_error=True)

def chatbot():
	quit = False
	while not quit:
		text = str(input('Me: '))
		if text == 'quit()':
			quit = True
		else:
			response = es.search(index='textbot', doc_type='clue',
					body={'query': {
						'match': {
							'text': text
						}
					}})
			try:
				i = randint(0, randomness)
				print('Chatbot: %s' % response['hits']['hits'][i]['_source']['response'])
			except:
				print('Chatbot: idk')


# option 2: custom
# seems like it just gives a random message, kinda like it tho
'''
class MyTexts(object):
	def __iter__(self):
		for i in range(len(train_data)):
			yield TaggedDocument(words=simple_preprocess(train_data['text'][i]), tags=[i])

assert gensim.models.doc2vec.FAST_VERSION > -1

cores = multiprocessing.cpu_count()
texts = MyTexts()
doc2vec_model = Doc2Vec(workers=cores)
doc2vec_model.build_vocab(texts)
doc2vec_model.train(texts, total_examples=doc2vec_model.corpus_count, epochs=15)

# Save model
if not os.path.exists('models'):
	os.makedirs('models')
	doc2vec_model.save('models/doc2vec.model')
else:
	doc2vec_model.save('models/doc2vec.model')


def chatbot():
	quit = False
	while not quit:
		text = str(input('Me: '))
		if text == 'quit()':
			quit = True
		else:
			tokens = text.split()
			new_vector = doc2vec_model.infer_vector(tokens)
			index = doc2vec_model.dv.most_similar([new_vector], topn=10)
			print('Chatbot: ' + train_data.iloc[index[0][0], 1])
			print('\n')
'''

chatbot()
