import networkx as nx
import numpy as np
 
from nltk.tokenize.punkt import PunktSentenceTokenizer
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer
 
def textrank(document):
    sentence_tokenizer = PunktSentenceTokenizer()
    sentences = sentence_tokenizer.tokenize(document)
 
    bow_matrix = CountVectorizer().fit_transform(sentences)
    normalized = TfidfTransformer().fit_transform(bow_matrix)
 
    similarity_graph = normalized * normalized.T
 
    nx_graph = nx.from_scipy_sparse_matrix(similarity_graph)
    scores = nx.pagerank(nx_graph)
    return sorted(((scores[i],s) for i,s in enumerate(sentences)),
                  reverse=True)

document = 'You will definitely want to do your own ranking, starting with a simple implementation of Pagerank which you may want to modify and experiment with e.g. with non-uniform exit link probabilities of links on pages. It is not that difficult to run Pagerank efficiently even on big datasets, you will need to implement some pretty basic block partitioning. After that, start experimenting with different heuristics for page and link elements such as titles, headings, anchor texts,  term frequencies etc.'
print textrank(document)