from collections import defaultdict, Counter
import codecs
import gzip
import math
from math import log10
import re
from os import listdir
from textrank import extract_key_phrases
from keyphrases import score_keyphrases_by_tfidf

class Index(object):

    def __init__(self, dirname=None):
        """
        Create a new index by parsing the given file containing documents,
        one per line. You should not modify this. """

        if dirname:  # filename may be None for testing purposes.

            self.files = listdir(dirname)
            self.documents = {}

            for file in self.files:
                f = open(dirname + file, 'r')
                #print 'Reading File ' + file + '.'
                self.documents[file] = f.read()
                f.close()

            toked_docs = [score_keyphrases_by_tfidf(f, self.documents[f]) for f in self.files]
            words = []
            for tokens in toked_docs:
                words += tokens
            self.WORDS = Counter(words)
            self.doc_freqs = self.count_doc_frequencies(toked_docs)
            self.index = self.create_tfidf_index(toked_docs, self.doc_freqs)
            self.doc_lengths = self.compute_doc_lengths(self.index)

    def compute_doc_lengths(self, index):
        """
        Return a dict mapping doc_id to length, computed as sqrt(sum(w_i**2)),
        where w_i is the tf-idf weight for each term in the document.

        E.g., in the sample index below, document 0 has two terms 'a' (with
        tf-idf weight 3) and 'b' (with tf-idf weight 4). It's length is
        therefore 5 = sqrt(9 + 16).

        >>> lengths = Index().compute_doc_lengths({'a': [[0, 3]], 'b': [[0, 4]]})
        >>> lengths[0]
        5.0
        """
        sum_w = defaultdict(lambda: 0)
        for k, docs in index.items():
            for doc in docs:
                sum_w[doc[0]] += doc[1]**2
        
        lengths = [0 for i in range(len(self.documents))]
        
        for k in xrange(len(lengths)):
            lengths[k] = math.sqrt(sum_w[k])
        return lengths


    def create_tfidf_index(self, docs, doc_freqs):
        """
        Create an index in which each postings list contains a list of
        [doc_id, tf-idf weight] pairs. For example:

        {'a': [[0, .5], [10, 0.2]],
         'b': [[5, .1]]}

        This entry means that the term 'a' appears in document 0 (with tf-idf
        weight .5) and in document 10 (with tf-idf weight 0.2). The term 'b'
        appears in document 5 (with tf-idf weight .1).

        Parameters:
        docs........list of lists, where each sublist contains the tokens for one document.
        doc_freqs...dict from term to document frequency (see count_doc_frequencies).

        Use math.log10 (log base 10).

        >>> index = Index().create_tfidf_index([['a', 'b', 'a'], ['a']], {'a': 2., 'b': 1., 'c': 1.})
        >>> sorted(index.keys())
        ['a', 'b']
        >>> index['a']
        [[0, 0.0], [1, 0.0]]
        >>> index['b']  # doctest:+ELLIPSIS
        [[0, 0.301...]]
        """
        index = defaultdict(list)
        for document in docs:
            for word in list(set(document)):
                temp = (1 + log10(float(document.count(word)))) * (log10(float(len(docs))/float(doc_freqs[word])))
                index[word] += [[docs.index(document),temp]]

        return index

    def count_doc_frequencies(self, docs):
        """ Return a dict mapping terms to document frequency.
        >>> res = Index().count_doc_frequencies([['a', 'b', 'a'], ['a', 'b', 'c'], ['a']])
        >>> res['a']
        3
        >>> res['b']
        2
        >>> res['c']
        1
        """
        res = defaultdict(lambda: 0)
        for doc in docs:
            for token in list(set(doc)):
                    res[token] += 1
        return res

    def query_to_vector(self, query_terms):
        """ Convert a list of query terms into a dict mapping term to inverse document frequency (IDF).
        Compute IDF of term T as log10(N / (document frequency of T)), where N is the total number of documents.
        You may need to use the instance variables of the Index object to compute this. Do not modify the method signature.

        If a query term is not in the index, simply omit it from the result.

        Parameters:
          query_terms....list of terms

        Returns:
          A dict from query term to IDF.
        """
        #   {'a': [[0, .5], [10, 0.2]],
        #    'b': [[5, .1]]}

        N = float(len(self.documents))
        index = self.index

        query_vector = defaultdict(lambda: 0)
        for term in query_terms:
            if term in index:
                query_vector[term] = math.log10(1. * N/float(self.doc_freqs[term]))

        return query_vector

    def search_by_cosine(self, query_vector, index, doc_lengths):
        """
        Return a sorted list of doc_id, score pairs, where the score is the
        cosine similarity between the query_vector and the document. The
        document length should be used in the denominator, but not the query
        length (as discussed in class). You can use the built-in sorted method
        (rather than a priority queue) to sort the results.

        The parameters are:

        query_vector.....dict from term to weight from the query
        index............dict from term to list of doc_id, weight pairs
        doc_lengths......dict from doc_id to length (output of compute_doc_lengths)

        In the example below, the query is the term 'a' with weight
        1. Document 1 has cosine similarity of 2, while document 0 has
        similarity of 1.

        >>> Index().search_by_cosine({'a': 1}, {'a': [[0, 1], [1, 2]]}, {0: 1, 1: 1})
        [(1, 2.0), (0, 1.0)]
        """
        scores = defaultdict(lambda: 0)
        # For each search term

        for query_term, query_weight in query_vector.items():
            # For each matching doc
            for doc_id, doc_weight in index[query_term]:
                scores[doc_id] += query_weight * doc_weight  # part of dot product

        # normalize by doc length (why not also by query length?)
        for doc_id in scores:
            scores[doc_id] /= float(doc_lengths[doc_id])

        return sorted(scores.items(), key=lambda key: key[1], reverse=True)

    def search(self, query):
        """ Return the document ids for documents matching the query. Assume that
        query is a single string, possible containing multiple words. Assume
        queries with multiple words are AND queries. The steps are to:

        1. Tokenize the query (calling self.tokenize)
        2. Convert the query into an idf vector (calling self.query_to_vector)
        3. Compute cosine similarity between query vector and each document (calling search_by_cosine).

        Parameters:

        query...........raw query string, possibly containing multiple terms (though boolean operators do not need to be supported)
        use_champions...If True, Step 4 above will use only the champion index to perform the search.
        """
        query_terms = self.tokenize(query)
        query_vector = self.query_to_vector(query_terms)
        return self.search_by_cosine(query_vector, self.index, self.doc_lengths)

    def read_lines(self, filename):
        """
        Read a gzipped file to a list of strings.
        """
        return [l.strip() for l in gzip.open(filename, 'rt').readlines()]

    def tokenize(self, document):
        """
        Convert a string representing one document into a list of
        words. Retain hyphens and apostrophes inside words. Remove all other
        punctuation and convert to lowercase.

        >>> Index().tokenize("Hi there. What's going on? first-class")
        ['hi', 'there', "what's", 'going', 'on', 'first-class']
        """
        return [t.lower() for t in re.findall(r"\w+(?:[-']\w+)*", document)]

def main():


    for query in ['pop love song', 'chinese american', 'city']:
        print('\n\nQUERY=%s' % query)
        print('\n'.join(['%d\t%e' % (doc_id, score) for doc_id, score in indexer.search(query)[:10]]))
        print('\n\nQUERY=%s Using Champion List' % query)
        print('\n'.join(['%d\t%e' % (doc_id, score) for doc_id, score in indexer.search(query, True)[:10]]))

if __name__ == '__main__':
    main()