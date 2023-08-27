import datetime
from stanza.models.common.doc import Document
from stanza.utils.conll import CoNLL
import pandas as pd
import stanza
import csv
import re
import os
import syll
from tqdm import tqdm

path = r'coca-split\mag\split_mag_1991.tsv'
# filename = r''
# source = path + filename
# genre = re.search('acad|blog|fic|mag|tvm|spok|news|web', filename)
# year = re.search('[0-9]{4}', filename)

mode = 'w'
# tok = stanza.Pipeline(lang='en', processors='tokenize', download_method=None)
nlp = stanza.Pipeline(lang='en', processors='tokenize, lemma, mwt, pos, depparse, ner', download_method=None)


def splitter(src):
    """
    splits the text into parts, puts them in a dictionary with their IDs as keys
    :param src: name of the source file
    :return: dictionary with the split texts
    """
    texts = {}
    df = pd.read_csv(src, sep='\t', quoting=csv.QUOTE_NONE, lineterminator='\n')
    txt = ''
    marker = ''
    genre = df.loc[1][2]
    year = df.loc[1][3]
    source = df.loc[1][4]
    for x in tqdm(range(1, len(df))):
        if marker != df.loc[x][5] and marker != '':
            m = re.match('@@[0-9]+', marker)
            texts[m.group()] = txt
            txt = ''
            marker = df.loc[x][5]
        elif marker != df.loc[x][5]:
            marker = df.loc[x][5]
        sentence = clean(str(df.loc[x][1]))
        txt += sentence + '\n\n'

    return texts, genre, year, source


# def remove_sentences(txt):
#     """
#     removes the sentences with series of @
#     :param txt: text to clean
#     :return: clean text
#     """
#     doc = tok(txt)
#     to_remove = []
#     for sent in doc.sentences:
#         if '@ @' in sent.text:
#             to_remove.append(sent.index)
#     to_remove.reverse()
#     for sent_id in to_remove:
#         doc.sentences.remove(doc.sentences[sent_id])
#
#     cln = ''
#     for sent in doc.sentences:
#         cln += sent.text+' '
#     return cln


def clean(txt):
    """
    removes <p>, <h>, @! from a given text, as well as redundant spaces by the punctuation
    :param txt: text to clean
    :return: clean text
    """
    to_remove = []                                             # lista pozycji na których są spacje do usunięcia
    qm = 2                                                     # quotation mark, sprawdza czy cudzysłów był otwarty, 0 - zamknięty, 1 - otwarty, 2 - nie ustawiono

    for i in range(len(txt)):                               # usuwa odpowiednie spacje przy interpunkcji itp.
        if txt[i] == ' ':
            if i+1 == len(txt) or \
                    (len(txt) > i+3 and txt[i+1:i+3] == '...') or \
                    (txt[i + 1] in [',', '.', '!', '?', ')', '}', ']', ':', ';'] and ((i + 2 < len(txt) and txt[i + 2] == ' ') or i + 2 == len(txt))) or \
                    (txt[i - 1] in ['(', '{', '['] and txt[i - 2] == ' ') or \
                    (txt[i + 1:i + 4] == "n't"):
                to_remove.append(i)
        elif len(txt) == 1:
            break
        elif txt[i] in [',', '.', '!', '?', ')', '}', ']', '(', '{', '[', ':', ';'] and i == 0 and (len(txt) == 1 or txt[1] == ' '):
            to_remove.append(i+1)
        elif txt[i] == "'" and txt[i - 1] == ' ' and (i+1 == len(txt) or txt[i + 1] != ' '):
            to_remove.append(i-1)
        elif txt[i] == '"':
            if i == 0 and txt[1] == ' ':
                to_remove.append(1)
                qm = 1
            elif i == len(txt)-1 and txt[i-1] == ' ':
                to_remove.append(i-1)
            elif txt[i - 1] == ' ' and (i + 1 == len(txt) or txt[i + 1] == ' '):
                if qm == 1:
                    to_remove.append(i - 1)
                    qm = 0
                else:
                    to_remove.append(i + 1)
                    qm = 1

    periods = []                                            # na które pozycje trzeba wstawić kropki (tam gdzie było np. <p>)
    marks = re.finditer('<[ph]>|@!', txt)                   # znajduje <p>, <h> i @!
    for elt in marks:                                       # usuwa <p>, <h> i @!
        i = elt.start()
        if txt[elt.start() - 2] not in ['.', '!', '?', '"', "'"] and i != 0:
            periods.append(i)       # nie ma potrzeby wstawiać kropek jeśli jest już coś kończącego zdanie lub jeśli to pierwsze zdanie w tekście
        while i <= elt.end():
            to_remove.append(i)
            i += 1

    to_remove.sort()
    to_remove.reverse()
    for j in to_remove:                                     # usuwa każdą niepotrzebną spację z tekstu, niektóre zastępuje kropkami
        if j in periods and j != 0:
            txt = txt[:j - 1] + '. ' + txt[j + 1:]
        else:
            txt = txt[:j] + txt[j + 1:]
    return txt


def create_tsv(src):
    df = pd.read_csv(src, sep='\t', quoting=csv.QUOTE_NONE, lineterminator='\n')
    # quoting=csv.QUOTE_NONE ensures there are no rows are packed into other rows
    data = [['SENT', 'TYPE', 'YEAR', 'FILE', 'PARA ID']]
    print('cleaning sentences, creating a clean .tsv file...')
    for i in tqdm(range(1, len(df)-1)):
        if clean(str(df.loc[i][1])) != '':
            data.append([clean(str(df.loc[i][1])), df.loc[i][2], df.loc[i][3], df.loc[i][4], df.loc[i][5]])

    new_file_name = 'stanza_clean_sentences_' + df.loc[1][2] + '_' + str(df.loc[1][3]) + '.tsv'

    with open(new_file_name, mode='w') as done:
        df = pd.DataFrame(data)
        df.to_csv(done, sep='\t', quoting=csv.QUOTE_NONE, escapechar='\n', header=False, lineterminator='\n')

    return new_file_name


def dep_children(sentence):
    """
    for every word in a given sentence finds a list of IDs of that words dependents
    :param sentence: a Stanza object
    :return: nothing
    """
    for word in sentence.words:
        word.children = []
        for w in sentence.words:
            if w.head == word.id:
                word.children.append(w.id)


def coord_info(crd, sent, conj, other_ids):
    """
    collects information on elements of a coordination: text of the conjunct, number of words, tokens and syllables
    :param crd: coordination (a dictionary containing the left and right elements of coordination, its head and the conjunct, if there is one)
    :param sent: sentence (Stanza object) where the coordination was found
    :param conj: which element of a coordination is to be considered (takes values "L" or "R")
    :param other_ids: a list of word IDs, that belong to the other element of the coordination
    :return: a list of word IDs, that belong to the element of the coordination that was specified by the conj parameter
    """
    txt_ids = []

    for id in crd[conj].children:
        if conj == 'L' and id < max(other_ids) and id not in crd['other_conjuncts'] and id != crd['R'].id:
            if id < crd['L'].id:
                for c in crd['other_conjuncts']:
                    for c_child in sent.words[c - 1].children:
                        if (sent.words[c_child - 1].deprel == sent.words[id - 1].deprel
                                or (sent.words[c_child - 1].deprel in ['nsubj', 'nsubj:pass'] and sent.words[id - 1].deprel in ['nsubj', 'nsubj:pass'])) \
                                and sent.words[id - 1].deprel != 'cc':
                            txt_ids.append(id)
                            break
                    if id in txt_ids:
                        break
                else:
                    for ch in crd['R'].children:
                        if sent.words[ch - 1].deprel == sent.words[id - 1].deprel and sent.words[id - 1].deprel != 'cc':
                            txt_ids.append(id)
                            break
            else:
                txt_ids.append(id)
        elif conj == 'R' and ("conj" not in crd.keys() or id != crd["conj"].id):
            txt_ids.append(id)

    for id in txt_ids:
        for i in sent.words[id - 1].children:
            txt_ids.append(i)
    txt_ids.append(crd[conj].id)

    while sent.words[min(txt_ids)-1].text in [',', ';', '-', ':']:
        txt_ids.remove(min(txt_ids))

    words = 0
    tokens = 0
    for id in range(min(txt_ids), max(txt_ids) + 1):
        tokens += 1
        if sent.words[id - 1].deprel != 'punct':
            words += 1

    txt = sent.text[sent.words[min(txt_ids) - 1].start_char - sent.words[0].start_char:sent.words[max(txt_ids) - 1].end_char - sent.words[0].start_char]

    syllables = 0
    for w in txt.split():
        syllables += syll.count_word(w)

    crd[conj+'conj'] = txt
    crd[conj+'words'] = words
    crd[conj+'tokens'] = tokens
    crd[conj+'syl'] = syllables

    return txt_ids


def extract_coords(src, marker, conll_list, sentence_count):
    """
    finds coordinations in a given text, creates a conllu file containing every sentence with a found coordination
    :param src: text to parse
    :param marker: marker of the parsed text
    :param conll_list: list for sentences, to later create a conllu file corresponding to the table of coordinations
    :param sentence_count: how many sentences have been processed already in the whole source file
    :return: list of dictionaries representing coordinations
    """
    doc = nlp(src)
    coordinations = []
    for sent in doc.sentences:
        dep_children(sent)

        conjs = {}
        for dep in sent.dependencies:
            if dep[1] == 'conj' and dep[0].upos != 'PUNCT' and dep[2].upos != 'PUNCT':
                if dep[0].id in conjs.keys():
                    conjs[dep[0].id].append(dep[2].id)
                else:
                    conjs[dep[0].id] = [dep[2].id]

        if conjs:
            conll_list.append(sent.to_dict())

        crds = []
        for l in conjs.keys():
            crd = [l]
            temp_coord = []
            cc = None
            another_coord = False
            for conj in conjs[l]:
                if cc:
                    temp_coord.append(conj)
                else:
                    crd.append(conj)
                for ch in sent.words[conj-1].children:
                    if not cc and sent.words[ch-1].deprel == 'cc':
                        cc = sent.words[ch-1].text
                    elif cc and sent.words[ch-1].deprel == 'cc' and sent.words[ch-1].text != cc:
                        crds.append(crd)
                        crd = [l] + temp_coord
                        another_coord = True
                        cc = sent.words[ch-1].text
                    elif cc and sent.words[ch-1].deprel == 'cc' and sent.words[ch-1].text == cc:
                        crd += temp_coord
                        temp_coord = []
            if not another_coord:
                crd += temp_coord
            crds.append(crd)
        for crd in crds:
            if len(crd) > 1:                    # UWAGA tu się potrafi wykrzaczyć (plik text_acad_2000, drugi znacznik)
                coord = {'L': sent.words[min(crd) - 1], 'R': sent.words[max(crd) - 1]}
                crd.pop(0)
                crd.pop(-1)
                coord['other_conjuncts'] = crd
                if coord['L'].head != 0:
                    coord['gov'] = sent.words[coord['L'].head - 1]
                for child in coord['R'].children:
                    if sent.words[child-1].deprel == 'cc':
                        coord['conj'] = sent.words[child-1]
                r_ids = coord_info(coord, sent, 'R', [])
                coord_info(coord, sent, 'L', r_ids)
                coord['sentence'] = sent.text
                coord['sent_id'] = str(marker) + '-' + str(sent.index + sentence_count)
                coordinations.append(coord)
    sentence_count += doc.sentences[len(doc.sentences)-1].index
    return coordinations, sentence_count


def create_csv(crd_list):
    path = r'C:\Users\magda\PycharmProjects\nlp310\done-csv\stanza_coordinations_' + str(genre) + '_' + str(year) + '.csv'
    with open(path, mode=mode, newline="") as file:
        writer = csv.writer(file)

        if os.path.getsize(path) == 0:
            with open("UD_Polish-LFG.csv", newline='') as ud:
                for row in csv.reader(ud):
                    col_names = row
                    break
            writer.writerow(col_names)

        for coord in crd_list:
            writer.writerow(['0' if 'gov' not in coord.keys() else 'L' if coord['L'].id > coord['gov'].id else 'R',     # governor.position
                             coord['gov'].text if 'gov' in coord.keys() else '',                                        # governor.word
                             coord['gov'].xpos if 'gov' in coord.keys() else '',                                        # governor.tag
                             coord['gov'].upos if 'gov' in coord.keys() else '',                                        # governor.pos
                             coord['gov'].feats if 'gov' in coord.keys() else '',                                       # governor.ms
                             coord['conj'].text if 'conj' in coord.keys() else '',                                      # conjunction.word
                             coord['conj'].xpos if 'conj' in coord.keys() else '',                                      # conjunction.tag
                             coord['conj'].upos if 'conj' in coord.keys() else '',                                      # conjunction.pos
                             coord['conj'].feats if 'conj' in coord.keys() else '',                                     # conjunction.ms
                             2 + len(coord['other_conjuncts']),                                                         # no.conjuncts
                             coord['Lconj'],                                                                            # L.conjunct
                             coord['L'].deprel,                                                                         # L.dep.label
                             coord['L'].text,                                                                           # L.head.word
                             coord['L'].xpos,                                                                           # L.head.tag
                             coord['L'].upos,                                                                           # L.head.pos
                             coord['L'].feats,                                                                          # L.head.ms
                             coord['Lwords'],                                                                           # L.words
                             coord['Ltokens'],                                                                          # L.tokens
                             coord['Lsyl'],                                                                             # L.syllables
                             len(coord['Lconj']),                                                                       # L.chars
                             coord['Rconj'],                                                                            # R.conjunct
                             coord['R'].deprel,                                                                         # R.dep.label
                             coord['R'].text,                                                                           # R.head.word
                             coord['R'].xpos,                                                                           # R.head.tag
                             coord['R'].upos,                                                                           # R.head.pos
                             coord['R'].feats,                                                                          # R.head.ms
                             coord['Rwords'],                                                                           # R.words
                             coord['Rtokens'],                                                                          # R.tokens
                             coord['Rsyl'],                                                                             # R.syllables
                             len(coord['Rconj']),                                                                       # R.chars
                             coord['sentence'],                                                                         # sentence
                             coord['sent_id'],                                                                          # sent.id
                             genre,                                                                                     # genre
                             source,                                                                                    # converted.from.file
                             ])


s = datetime.datetime.now()

txts, genre, year, source = splitter(path)
crds_full_list = []
conll_list = []
sent_count = 0

for mrk in tqdm(txts.keys()):
    coordinations, sent_count = extract_coords(txts[mrk], mrk, conll_list, sent_count)
    crds_full_list += coordinations

conll_name = r'C:\Users\magda\PycharmProjects\nlp310\done-conll\coords_' + str(genre) + '_' + str(year) + '.conllu'
conll_doc = Document(conll_list)
CoNLL.write_doc2conll(conll_doc, conll_name)
create_csv(crds_full_list)

e = datetime.datetime.now()
print(e-s)
