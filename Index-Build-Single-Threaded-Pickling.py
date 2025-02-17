#-------------------------------------------------------------------------------------------
#	Without multi-threading
#-------------------------------------------------------------------------------------------


#input = [file1, file2, ...]
#result = {filename: [world1, word2]}

import re
import time
import json
import os
import math
import pickle
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

stemmer = PorterStemmer()

class BuildIndex:

	def __init__(self, files):
		self.tf = {}
		self.df = {}
		self.idf = {}
		self.filenames = files
		self.file_to_terms = self.process_files()
		self.regdex = self.regIndex()
		self.totalIndex = self.execute()
		self.vectors = self.vectorize()
		self.mags = self.magnitudes(self.filenames)
		self.populateScores()


	def process_files(self):
		file_to_terms = {}
		for file in self.filenames:
			stopword = set(stopwords.words('english'))
			pattern = re.compile(r'[\W_]+')
			file_to_terms[file] = open(file, 'r').read().lower()
			file_to_terms[file] = pattern.sub(' ',file_to_terms[file])
			re.sub(r'[\W_]+','', file_to_terms[file])
			file_to_terms[file] = file_to_terms[file].split()
			file_to_terms[file] = [stemmer.stem(w) for w in file_to_terms[file] if w not in stopword]
		return file_to_terms

    #-----------------------------------------------------------------------------------------------
	#   input = [word1, word2, ...]
	#   output = {word1: [pos1, pos2], word2: [pos2, pos434], ...}
    #-----------------------------------------------------------------------------------------------
	def index_one_file(self, termlist):
		fileIndex = {}
		for index, word in enumerate(termlist):
			if word in fileIndex.keys():
				fileIndex[word].append(index)
			else:
				fileIndex[word] = [index]
		return fileIndex

    #-----------------------------------------------------------------------------------------------
	#   input = {filename: [word1, word2, ...], ...}
	#   result = {filename: {word: [pos1, pos2, ...]}, ...}
    #-----------------------------------------------------------------------------------------------
	def make_indices(self, termlists):
		total = {}
		for filename in termlists.keys():
			total[filename] = self.index_one_file(termlists[filename])
		return total

    #-----------------------------------------------------------------------------------------------
	#   input = {filename: {word: [pos1, pos2, ...], ... }}
	#   result = {word: {filename: [pos1, pos2]}, ...}, ...}
    #-----------------------------------------------------------------------------------------------
	def fullIndex(self):
		total_index = {}
		indie_indices = self.regdex
		for filename in indie_indices.keys():
			self.tf[filename] = {}
			for word in indie_indices[filename].keys():
				self.tf[filename][word] = len(indie_indices[filename][word])
				if word in self.df.keys():
					self.df[word] += 1
				else:
					self.df[word] = 1 
				if word in total_index.keys():
					if filename in total_index[word].keys():
						total_index[word][filename].append(indie_indices[filename][word][:])
					else:
						total_index[word][filename] = indie_indices[filename][word]
				else:
					total_index[word] = {filename: indie_indices[filename][word]}
		return total_index

	def vectorize(self):
		vectors = {}
		for filename in self.filenames:
			vectors[filename] = [len(self.regdex[filename][word]) for word in self.regdex[filename].keys()]
		return vectors

	def document_frequency(self, term):
		if term in self.totalIndex.keys():
			return len(self.totalIndex[term].keys()) 
		else:
			return 0

	def collection_size(self):
		return len(self.filenames)

	def magnitudes(self, documents):
		mags = {}
		for document in documents:
			mags[document] = pow(sum(map(lambda x: x**2, self.vectors[document])),.5)
		return mags

	def term_frequency(self, term, document):
		return self.tf[document][term]/self.mags[document] if term in self.tf[document].keys() else 0

	def populateScores(self): 
		for filename in self.filenames:
			for term in self.getUniques():
				self.tf[filename][term] = self.term_frequency(term, filename)
				if term in self.df.keys():
					self.idf[term] = self.idf_func(self.collection_size(), self.df[term]) 
				else:
					self.idf[term] = 0
		return self.df, self.tf, self.idf

	def idf_func(self, N, N_t):
		if N_t != 0:
			return math.log(N/N_t)
		else:
		 	return 0

	def generateScore(self, term, document):
		return self.tf[document][term] * self.idf[term]

	def execute(self):
		return self.fullIndex()

	def regIndex(self):
		return self.make_indices(self.file_to_terms)

	def getUniques(self):
		return self.totalIndex.keys()

if __name__ == "__main__":
	start = time.process_time()

	files = [os.path.dirname(os.path.realpath(__file__)) + os.sep + 'data-raw/test' + os.sep + x for x in os.listdir("./data-raw/test")] 
	ff = BuildIndex(files)
	
	""" Export the Inverted File structure to a Pickle file."""
	# http://stackoverflow.com/questions/12309269/how-do-i-write-json-data-to-a-file-in-python
	tf = './data-out/test/tf-test.pickle'
	idf = './data-out/test/idf-test.pickle'
	with open(tf, 'wb') as fh:
		pickle.dump((ff.tf), fh)
	with open(idf, 'wb') as fh:
		pickle.dump((ff.idf), fh)

	print("All exported.. in ", (time.process_time()-start))