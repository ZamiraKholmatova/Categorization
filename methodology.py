import os
from pathlib import Path

import nltk
import numpy as np

import codecs

nltk.download('stopwords')
nltk.download('punkt')
from collections import Counter
from nltk.corpus import stopwords
import string
from nltk.tokenize import RegexpTokenizer


def files_dict(path):
    files = dict()
    for foldername in os.listdir(path):
        for filename in os.listdir(os.path.join(path + os.sep, foldername)):
            # with open(os.path.join(path + os.sep, foldername, filename)) as f:
            f = codecs.open(os.path.join(path + os.sep, foldername, filename), "r", "utf_8_sig")
            category = foldername
            if category in files:
                files[category].extend([x.partition('.')[2].lower().strip().strip('\r') for x in f.read().split('\n')])
            else:
                files[category] = [x.partition('.')[2].lower().strip().strip('\r') for x in f.read().split('\n')]
    return files


def get_doc_category(doc_id, ranges):
    for r in ranges:
        if doc_id < r[1]:
            return r[0]
    return "out of range"


def get_app_name(name: str) -> str:
    return Path(name).stem.split(".")[0].lower().replace("%20", " ")


def edit_dist(s1, s2) -> int:
    xrange = range
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in xrange(-1, lenstr1 + 1):
        d[(i, -1)] = i + 1
    for j in xrange(-1, lenstr2 + 1):
        d[(-1, j)] = j + 1

    for i in xrange(lenstr1):
        for j in xrange(lenstr2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,  # deletion
                d[(i, j - 1)] + 1,  # insertion
                d[(i - 1, j - 1)] + cost,  # substitution
            )
            if i and j and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)  # transposition
    return d[lenstr1 - 1, lenstr2 - 1]


def lm_rank_documents(query, tdm, terms_list, smoothing='additive', param=0.001):
    # TODO: score each document in tdm using this document's language model
    # implement two types of smoothing. Looks up term frequencies in tdm
    # return document scores in a convenient form
    # param is alpha for additive / lambda for jelinek-mercer
    """
    :param query: dict, term:count
    :param tdm: term-document matrix
    :param terms_list: vocabulary list
    :param smoothing: which smoothing to apply, either 'additive' or 'jelinek-mercer'
    :param param: alpha for additive / lambda for jelinek-mercer
    :return: list of scores, list of doc_ids sorted by their scores
    """
    n_docs = tdm.shape[0]
    doc_lengths = tdm.sum(axis=1)
    len_collection = np.sum(doc_lengths)
    scores = np.zeros(n_docs)
    for term in query.keys():
        candidate_term = term
        # check if term exists
        if term in terms_list:
            # get term's id
            term_id = terms_list.index(term)
        else:
            # continue #CASE WHERE WE DON'T HAVE THE TERM IN A MATRIX
            dists = dict()
            for word in terms_list:
                dists[word] = edit_dist(term, word)
            candidate_term = sorted(dists.items(), key=lambda x: x[1])[0][0]
            term_id = terms_list.index(candidate_term)
        query_tf = query[candidate_term]
        # calculate collection frequency of a term
        collection_tf = np.sum(tdm[:, term_id])
        for doc_id in range(n_docs):
            doc_tf = tdm[doc_id, term_id]
            # apply smoothing of any
            if smoothing == 'additive':
                doc_score_factor = (doc_tf + param) / (doc_lengths[doc_id] + param * len(terms_list))
            elif smoothing == 'jelinek':
                doc_score_factor = param * doc_tf / doc_lengths[doc_id] + (1 - param) * collection_tf / len_collection
            else:
                doc_score_factor = doc_tf / doc_lengths[doc_id]
            doc_score_factor = doc_score_factor ** query_tf

            if doc_id not in scores:
                scores[doc_id] = 1
            # accumulate scores
            scores[doc_id] *= doc_score_factor
    # sort doc_ids by scores
    sorted_doc_ids = np.argsort(-scores)
    return scores, sorted_doc_ids


def prepare_query(raw_query):
    # lower-case, remove punctuation and stopwords
    stop_words = list(string.punctuation) + stopwords.words('english')
    tokenizer = RegexpTokenizer(r'\w+')
    # return Counter([i for i in word_   tokenize(raw_query.lower()) if i not in stop_words])
    return Counter([i for i in tokenizer.tokenize(raw_query.lower()) if i not in stop_words and i.isalpha()])


def process_query(raw_query, counts_data, terms, data_ranges, all_data):
    # TODO process user query and print search results including document category, id, score, and some part of it
    query = prepare_query(raw_query)
    # print("user query:", '\033[95m' + raw_query + '\033[0m')
    # print("prepared query:", query)
    doc_scores, doc_ids_sorted = lm_rank_documents(query, counts_data, terms)
    # print("\nsearch results:")
    temp = []
    # for i in range(5):
    #    doc_id = doc_ids_sorted[i]
    #    temp.append((get_doc_category(doc_id, data_ranges),all_data[doc_id][:100]))
    doc_id = doc_ids_sorted[0]
    temp.append((get_doc_category(doc_id, data_ranges), all_data[doc_id][:100]))
    return (temp)


def get_category(cat_id, cursor):
    select_category_query = "select * from innometricsconfig.cl_categories where catid=%s"
    cursor.execute(select_category_query, (cat_id,))
    category = cursor.fetchone()[1]
    return category


def if_exists(executable, cursor):
    #print('checking if exists in cl_apps')
    select_category_id_query = "select * from innometricsconfig.cl_apps_categories where executablefile=%s"
    cursor.execute(select_category_id_query, (executable,))
    r = cursor.fetchone()
    category_id, app_name = r[1], r[2]
    category = get_category(category_id, cursor)
    return category, app_name
