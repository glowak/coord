import re
from collections import OrderedDict
from coord.tools.syllables import syllables


def select_conj(dict_parsed: dict) -> tuple[dict, list[int]]:
    '''
    Selects all the sentences with at least one conjunction and adds
    key with a list of dictionaries, containing conjunction words and information
    about them. Also, adds information about dependencies and token children.

    Returns a dictionary and a list of selected sentences' ids.

    OK
    '''

    # Useful variables declaration
    selected_dict = {}
    selected_dict["sentences"] = []
    selected_ids = []

    '''
    For every sentence in the dictionary:
    a) create keys:
        i. create "dependencies" key storing all the tokens dependencies        USELESS/REMOVED
        ii. create "words_cconj" key storing all words that join conjuncts      USELESS/REMOVED
    b) for every token in the sentence:
        i. count the number of coordinations by looking at the 'conj' deprel
        ii. create "children" key storing id and deprel of every child of 
            the current token 
        iii. create "all_deprels" key storing deprels that go out of the 
                current token
        iv. if the deprel of any token in sentence is equal to 'conj', add as selected
    '''
    for sentence in dict_parsed["sentences"]:
        for token in sentence["tokens"]:
            token["conj_count"] = 0
            token["children"] = []
            token["all_deprels"] = {}

            # Information about word's children
            for t in sentence["tokens"]:
                if t["head"] == token["id"]:
                    token["children"].append({"id": t["id"],
                                              "deprel": t["deprel"]})
                    token["all_deprels"][t["deprel"]] = t["id"]

            if token["deprel"] == "conj":
                selected_ids.append(sentence["id"])

        if sentence["id"] in selected_ids:
            selected_dict["sentences"].append(sentence)

    return selected_dict, selected_ids


def conj_info_extraction(dict_parsed: dict) -> None:  
    ''' 
    PROBLEM: flat and complex coordinations
    
    For every sentence in dictionary:
        a) in a sentence:
            i. create "coordination_info" key with all the information about coordinations
            ii. count all 'conj' edges in sentence
        b) for every token in a sentence:
            i. if deprel is equal to 'conj' and there were 0 conj edges: 
                - set the left head to the first token that has a conj deprel (head of first conjunct)
                - go through children of the left head and check if there are more conj deprels
                    = if there are more than two conjuncts, choose the last one                         WRONG/FIX THIS
        
    '''
    # ----------- NEW -----------
    for sentence in dict_parsed["sentences"]:
        sentence["coordination_info"] = {}
        global_conj_no = 0
        for token in sentence["tokens"]:
            if token["deprel"] == "conj":
                global_conj_no += 1
                left_head_token = sentence["tokens"][token["head"] - 1]
                left_head_token["conj_count"] += 1
                if ("cc" in token["all_deprels"].keys()): 
                    cc_word = sentence["tokens"][token["all_deprels"]["cc"] - 1]
                    cc_word_text = cc_word["text"]
                    cc_tag = cc_word["xpos"]
                    cc_pos = cc_word["upos"]
                    try:
                        cc_ms = cc_word["feats"]
                    except KeyError:
                        cc_ms = ""
                else: 
                    cc_word = ""
                    cc_word_text = ""
                    cc_tag, cc_pos, cc_ms = "", "", ""

                if left_head_token["head"] != 0:
                    governor = sentence["tokens"][left_head_token["head"] - 1]
                else:
                    governor = left_head_token

                if governor["id"] < left_head_token["id"]:
                    # governor is on the left
                    governor_dir = "L"
                elif governor["id"] > left_head_token["id"]:
                    # governor is on the right
                    governor_dir = "R"
                else:
                    # there is no governor
                    governor_dir = "0"

                if governor_dir == "0":
                    governor_text, governor_xpos, governor_upos, governor_ms = " ", " ", " ", " "
                else:
                    governor_text = governor["text"]
                    governor_xpos = governor["xpos"]
                    governor_upos = governor["upos"]
                    try:
                        governor_ms = governor["feats"]
                    except KeyError:
                        governor_ms = " "

                try:
                    left_feats = left_head_token["feats"]
                    right_feats = token["feats"]
                except KeyError:
                    left_feats = " "
                    right_feats = " "
                    
                
                sentence["coordination_info"][global_conj_no] = {
                    "right_head_token": token,
                    "right_feats": right_feats,
                    "left_head_token": sentence["tokens"][token["head"] - 1],
                    "left_feats": left_feats,
                    "governor_text": governor_text,
                    "governor_xpos": governor_xpos,
                    "governor_upos": governor_upos,
                    "governor_ms": governor_ms,
                    "governor_dir": governor_dir,
                    "cc_word": cc_word,
                    "cc_tag": cc_tag,
                    "cc_pos": cc_pos,
                    "cc_ms": cc_ms,
                    "cc_word_text": cc_word_text,
                    "local_conj_no": sentence["tokens"][token["head"] - 1]["conj_count"],
                    "global_conj_no": global_conj_no
                }
        
        for k, v in list(sentence["coordination_info"].items()):
            if (v["local_conj_no"] > 1):
                for k2, v2 in list(sentence["coordination_info"].items()):
                    if (k2 < k
                        and v["left_head_token"] == v2["left_head_token"]
                        and (v["cc_word_text"] == v2["cc_word_text"]
                             or v["cc_word_text"] == "" 
                             or v2["cc_word_text"] == "")):
                        sentence["coordination_info"].pop(k2)
            # if (v["local_conj_no"] > 1 
            #     and (v["cc_word_text"] == sentence["coordination_info"][k - 1]["cc_word_text"]
            #          or v["cc_word_text"] == "" or sentence["coordination_info"][k - 1]["cc_word_text"] == "")):
            #          sentence["coordination_info"].pop(k - 1)
        
    # ----------- OLD -----------
    # for sentence in dict_parsed["sentences"]:
    #     sentence["coordination_info"] = []
    #     all_conj_counter = 0
    #     for token in sentence["tokens"]:

    #         if token["deprel"] == "conj" and sentence["tokens"][token["head"] - 1]["conj_count"] == 0:
    #             all_conj_counter += 1
    #             # the head of the first token that has a conj deprel is the left head (head of first conjunct)
    #             left_token_conj = sentence["tokens"][token["head"] - 1]
    #             right_token_conj = token
    #             try:
    #                 first_cc = right_token_conj["all_deprels"]["cc"]
    #             except KeyError:
    #                 first_cc = ""
    #             # if there are more than two conjuncts, choose the last one
    #             for child in left_token_conj["children"]:
    #                 if (sentence["tokens"][child["id"] - 1]["deprel"] == "conj"
    #                     and sentence["tokens"][child["id"] - 1]["deprel"] != token):
    #                     try:
    #                         next_cc = sentence["tokens"][child["id"] - 1]["all_deprels"]["cc"]
    #                     except KeyError:
    #                         next_cc = ""
    #                     if first_cc == next_cc:
    #                         left_token_conj["conj_count"] += 1
    #                         right_token_conj = sentence["tokens"][child["id"] - 1]
    #                     else:
    #                         right_token_conj = token

    #             for child in right_token_conj["children"]:
    #                 if child["deprel"] == "cc":
    #                     cc_no = all_conj_counter
    #                     cc_word = sentence["tokens"][child["id"] - 1]["text"]
    #                     cc_tag = sentence["tokens"][child["id"] - 1]["xpos"]
    #                     cc_pos = sentence["tokens"][child["id"] - 1]["upos"]
    #                     try:
    #                         cc_ms = sentence["tokens"][child["id"] - 1]["feats"]
    #                     except KeyError:
    #                         cc_ms = ""
    #                 elif ("cc" not in right_token_conj["all_deprels"]):
    #                       #and child["deprel"] == "punct"
    #                       #and child["id"] < right_token_conj["id"]):
    #                     cc_no = all_conj_counter
    #                     cc_word = ""
    #                     cc_tag = ""
    #                     cc_pos = ""
    #                     cc_ms = ""
    #                     # cc_word = sentence["tokens"][child["id"] - 1]["text"]
    #                     # cc_tag = sentence["tokens"][child["id"] - 1]["xpos"]
    #                     # cc_pos = sentence["tokens"][child["id"] - 1]["upos"]
    #                     # try:
    #                     #     cc_ms = sentence["tokens"][child["id"] - 1]["feats"]
    #                     # except KeyError:
    #                     #     cc_ms = ""
                
    #             if left_token_conj["head"] != 0:
    #                 governor = sentence["tokens"][left_token_conj["head"] - 1]
    #             else:
    #                 governor = left_token_conj

    #             if governor["id"] < left_token_conj["id"]:
    #                 # governor is on the left
    #                 governor_dir = "L"
    #             elif governor["id"] > left_token_conj["id"]:
    #                 # governor is on the right
    #                 governor_dir = "R"
    #             else:
    #                 # there is no governor
    #                 governor_dir = "0"

    #             if governor_dir == "0":
    #                 text, xpos, upos, ms = " ", " ", " ", " "
    #             else:
    #                 text = governor["text"]
    #                 xpos = governor["xpos"]
    #                 upos = governor["upos"]
    #                 try:
    #                     ms = governor["feats"]
    #                 except KeyError:
    #                     ms = " "

    #             try:
    #                 left_feats = left_token_conj["feats"]
    #                 right_feats = token["feats"]
    #             except KeyError:
    #                 left_feats = " "
    #                 right_feats = " "
                
    #             sentence["coordination_info"].append({"left_head": left_token_conj,
    #                                                   "right_head": right_token_conj,
    #                                                   "text": {"left": left_token_conj["text"],
    #                                                            "right": right_token_conj["text"]},
    #                                                   "left_deplabel": left_token_conj["deprel"],
    #                                                   "right_deplabel": right_token_conj["deprel"],
    #                                                   "left_tag": left_token_conj["xpos"],
    #                                                   "right_tag": right_token_conj["xpos"],
    #                                                   "left_upos": left_token_conj["upos"],
    #                                                   "right_upos": right_token_conj["upos"],
    #                                                   "left_ms": left_feats,
    #                                                   "right_ms": right_feats,
    #                                                   "governor": text,
    #                                                   "governor_dir": governor_dir,
    #                                                   "governor_tag": xpos,
    #                                                   "governor_pos": upos,
    #                                                   "governor_ms": ms,
    #                                                   "count":  left_token_conj["conj_count"],
    #                                                   "cc": {"word": cc_word,
    #                                                          "tag": cc_tag,
    #                                                          "pos": cc_pos,
    #                                                          "no": cc_no,
    #                                                          "ms": cc_ms}
    #                                                   })
      

def search_for_dependencies(sentence: dict) -> None:
    '''
    Przerobiony kod od Magdy
    '''

    for con in sentence["coordination_info"]:
        # Lists of tokens' ids' in conjuncts
        left_list = []
        right_list = []

        # Lists of tokens' deprels in conjuncts
        left_deprels = []
        right_deprels = []

        # Append conjunct tokens that are directly connected to the left and right 
        # heads of conjuncts to left and right lists 
        for child in sentence["coordination_info"][con]["left_head_token"]["children"]:
            if (sentence["tokens"][child["id"] - 1]["deprel"] != "conj"   # don't add tokens with 'conj' deprel
                and child["id"] < sentence["coordination_info"][con]["right_head_token"]["id"]):
                left_list.append(child["id"])
                left_deprels.append(sentence["tokens"][child["id"] - 1]["deprel"])
        for child in sentence["coordination_info"][con]["right_head_token"]["children"]:
            if (sentence["tokens"][child["id"] - 1]["deprel"] != "cc"):
                    right_list.append(child["id"])
                    right_deprels.append(sentence["tokens"][child["id"] - 1]["deprel"])
       
        # Get all children of tokens that are directly connected to the heads of conjuncts
        for child in left_list:
            for t in sentence["tokens"][child - 1]["children"]:
                left_list.append(t["id"])
        for child in right_list:
            for t in sentence["tokens"][child - 1]["children"]:
                right_list.append(t["id"])
        
        # Append the heads of conjuncts to the whole conjunct 
        left_list.append(sentence["coordination_info"][con]["left_head_token"]["id"])
        right_list.append(sentence["coordination_info"][con]["right_head_token"]["id"])

        # Remove certain tokens from lists 
        for id in left_list[:]:
            if ((id == min(left_list) and sentence["tokens"][id - 1]["text"] == ",")
                or (id == max(left_list) and sentence["tokens"][id - 1]["text"] == ",")
                or (id < sentence["coordination_info"][con]["left_head_token"]["id"]
                    and sentence["tokens"][id - 1]["deprel"] not in right_deprels    # remove every token on the left of left conjunct if the right conjunct doesn't have the same deprels somewhere
                    and min(left_list) >= id)):
                left_list.remove(id)
        for id in right_list[:]:
            if ((id == min(right_list) and sentence["tokens"][id - 1]["text"] == ",")      # remove a comma on the beginning of the right conjunct
                or (id == max(right_list) and sentence["tokens"][id - 1]["text"] == ",")):
                right_list.remove(id)

        # Declare variables storing information about conjuncts
        left = ""
        right = ""
        Rwords = 0
        Lwords = 0
        Rtokens = 0
        Ltokens = 0
        Rsyllables = 0
        Lsyllables = 0

        # Sort lists in ascending order
        left_list.sort()
        right_list.sort()

        # Count tokens, syllables, words and find conjuncts in sentence
        for id in left_list:
            Ltokens += 1
            Lsyllables += syllables(sentence["tokens"][id - 1]["text"])
            if sentence["tokens"][id - 1]["deprel"] != "punct":
                Lwords += 1
            if sentence["tokens"][id - 1]["text"] in ["^", "$", ".", "|", "+", "*", "?", "{", "}", "(", ")", "[", "]"]:
                left += "\\" + sentence["tokens"][id - 1]["text"] + "\s*"
            else:
                left += sentence["tokens"][id - 1]["text"] + "\s*"
        left_match = re.search(left, sentence["text"])        
        for id in right_list:
            Rtokens += 1
            Rsyllables += syllables(sentence["tokens"][id - 1]["text"])
            if sentence["tokens"][id - 1]["deprel"] != "punct":
                Rwords += 1
            if sentence["tokens"][id - 1]["text"] in ["^", "$", ".", "|", "+", "*", "?", "{", "}", "(", ")", "[", "]"]:
                right += "\\" + sentence["tokens"][id - 1]["text"] + "\s*"
            else:
                right += sentence["tokens"][id - 1]["text"] + "\s*"
        right_match = re.search(right, sentence["text"])
        
        # Get the variables and save to dictionary
        # MAY BE AN EASIER WAY TO DO
        if right_match != None:
            sentence["coordination_info"][con]["right_text"] = right_match.group(0)
        else:
            print(right)
            sentence["coordination_info"][con]["right_text"] = ""
        if left_match != None:
            sentence["coordination_info"][con]["left_text"] = left_match.group(0)
        else:
            print(left)
            sentence["coordination_info"][con]["left_text"] = ""

        sentence["coordination_info"][con]["Rwords"] = Rwords
        sentence["coordination_info"][con]["Lwords"] = Lwords

        sentence["coordination_info"][con]["Rtokens"] = Rtokens
        sentence["coordination_info"][con]["Ltokens"] = Ltokens

        sentence["coordination_info"][con]["Rsyllables"] = Rsyllables
        sentence["coordination_info"][con]["Lsyllables"] = Lsyllables


def search_for_id(dict_parsed: dict) -> re.Match[str]:
    '''
    Returns a matched string with line id from the corpus.
    '''
    match = re.search(r"@@\d*", dict_parsed["text"])
    return match.group(0)


def addline(conj: dict, 
            sentence: dict, 
            file_path: str, 
            genre: str, 
            sent_id: str
    ) -> dict:
    line = {"governor.position": conj["governor_dir"],
            "governor.word": conj["governor_text"],
            "governor.tag": conj["governor_xpos"],
            "governor.pos": conj["governor_upos"],
            "governor.ms": conj["governor_ms"],
            "conjunction.word": conj["cc_word_text"],
            "conjunction.tag": conj["cc_tag"],
            "conjunction.pos": conj["cc_pos"],
            "conjunction.ms": conj["cc_ms"],
            "no.conjuncts": conj["left_head_token"]["conj_count"] + 1,
            "L.conjunct": conj["left_text"],
            "L.dep.label": conj["left_head_token"]["deprel"],
            "L.head.word": conj["left_head_token"]["text"],
            "L.head.tag": conj["left_head_token"]["xpos"],
            "L.head.pos": conj["left_head_token"]["upos"],
            "L.head.ms": conj["left_feats"],
            "L.words": conj["Lwords"],
            "L.tokens": conj["Ltokens"],
            "L.syllables": conj["Lsyllables"],
            "L.chars": len(conj["left_text"]),
            "R.conjunct": conj["right_text"],
            "R.dep.label": conj["right_head_token"]["deprel"],
            "R.head.word": conj["right_head_token"]["text"],
            "R.head.tag": conj["right_head_token"]["xpos"],
            "R.head.pos": conj["right_head_token"]["upos"],
            "R.head.ms": conj["right_feats"],
            "R.words": conj["Rwords"],
            "R.tokens": conj["Rtokens"],
            "R.syllables": conj["Rsyllables"],
            "R.chars": len(conj["right_text"]),
            "sentence": sentence["text"],
            "sent.id": sent_id,
            "genre": genre,
            "converted.from.file": file_path
}

    return line