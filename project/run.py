import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from flask import Flask
from flask import request
from nltk import sent_tokenize, word_tokenize
from search import Index
from spell import correction
import re
import argparse
from clint.textui import *

app = Flask(__name__)



def results2string(doc_ids, query, corrected):
    """ Return the top 100 search results as a string of <p> blocks, looking up each
    doc_id in the index. """
    res = ''
    if corrected:
        res += "<p>search results for <i>" + query + "</i>"
    query = word_tokenize(query)
    res += "<ul style='list-style: none;'>"
    for doc_id, score in doc_ids[:100]:
        res += "<li><h4>%s</h4></li>" % (my_index.files[doc_id])
        f = open(dirname + my_index.files[doc_id], 'r')
        text = f.read()
        f.close()
        sent = sent_tokenize(text)
        res += "<ul style='list-style: none;'>"
        for s in sent:
            for q in query:
                if q in s:
                    res += '<li><p>' + s  + '</p></li>'
        res += "</ul>"
    res += "</ul>"
    return res


def form():
    """ Create a search form, optionally with the query box filled in."""
    query = request.form['query'] if request.form else ''
    return '''
    <form action="/index" method="post">
      <input type="text" name="query" size="50" value="%s"/>
      <input type="submit" value="search"/>
    </form>
   ''' % (query)

def tokenize(document):
    return [t.lower() for t in re.findall(r"\w+(?:[-']\w+)*", document)]
    

@app.route('/')
@app.route('/index', methods=["POST"])
def index():
    """ Process search request and results. """
    result = "<html style='margin:20px 50px'>\n<body><p>&nbsp&nbsp&nbspWelcome to<br/>Document Retreival Engine</p>" + form()
    if request.method == 'POST':
        query_terms = tokenize(request.form['query'])
        updated_query = []
        corrected = False
        for term in query_terms:
            new_term = correction(term, my_index.WORDS)
            if new_term != term:
                corrected = True
            updated_query.append(new_term)
        result += results2string(my_index.search(' '.join(updated_query)), ' '.join(updated_query), corrected)
    result += "<body></html>"
    return result

def cmd_app():
    query = prompt.query("Type query: ", validators=[])
    query_terms = tokenize(query)
    updated_query = []
    corrected = False
    for term in query_terms:
        new_term = correction(term, my_index.WORDS)
        if new_term != term:
            corrected = True
        updated_query.append(new_term)

    new_query = ' '.join(updated_query)
    if corrected:
        print 'Search results for ' + colored.green(new_query)

    doc_ids = my_index.search(new_query)
    for doc_id, score in doc_ids[:100]:
        print '*'*50
        print colored.blue(my_index.files[doc_id])
        f = open(dirname + my_index.files[doc_id], 'r')
        text = f.read()
        f.close()
        sent = sent_tokenize(text)
        with indent(4, quote=''):
            for s in sent:
                for q in updated_query:
                    if q in s:
                        puts(s)
        print 

if __name__ == '__main__':
    print '*'*50
    print ' '*15 + 'Welcome To'
    print ' '*10 + 'Document Retreival Engine'
    print '*'*50

    options = [{'selector':'1','prompt':'Browser Engine','return':'web'},
                {'selector':'2','prompt':'Terminal Engine','return':'cmd'},
                {'selector':'3','prompt':'Exit','return':'exit'}]
    selection = prompt.options("Browser or Terminal Engine", options)
        
    if selection == 'exit':
    	print 'Bye'
    	exit()

    global my_index, dirname
    dirname = path = prompt.query('Documents Path', default=os.getcwd(), validators=[validators.PathValidator()])
    my_index = Index(dirname)

    if selection == 'web':
        app.run(debug=False)
    elif selection == 'cmd':
        while 1:
            options = [{'selector':'1','prompt':'Query','return':'cont'},
                        {'selector':'2','prompt':'Exit','return':'exit'}]

            selection = prompt.options("Select Option", options)
            if selection == 'cont':
                cmd_app()
            else:
                break
    
    print 'Bye'