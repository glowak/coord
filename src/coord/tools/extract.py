import re
from collections import OrderedDict
from coord.tools.syllables import syllables


def select_conj(dict_parsed: dict) -> tuple[dict, list[int]]:
    '''
    Selects all the sentences with at least one conjunction and adds
    key with a list of dictionaries, containing conjunction words and information
    about them. Also, adds information about dependencies and token children.

    Returns a dictionary and a list of selected sentences' ids.
    '''

    selected_dict = {}
    selected_dict["text"] = dict_parsed["text"]
    selected_dict["sentences"] = []

    selected_ids = []

    for sentence in dict_parsed["sentences"]:
        sentence["dependencies"] = []
        sentence["words_cconj"] = []

        for token in sentence["tokens"]:
            token["conj_count"] = 0
            token["children"] = []
            token["all_deprels"] = []
            #sentence["dependencies"].append(
            #    (token["head"], token["id"], token["deprel"]))

            # Information about word's children
            for t in sentence["tokens"]:
                if t["head"] == token["id"]:
                    token["children"].append({"id": t["id"],
                                              "deprel": t["deprel"]})
                    token["all_deprels"].append(t["deprel"])

            # if (token["deprel"] == "cc" and 
            #     sentence["tokens"][token["head"] - 1]["deprel"] == "conj"):
            #     conj_counter += 1
            #     sentence["words_cconj"].append({"no": conj_counter,
            #                                     "word": token["text"],
            #                                     "tag": token["xpos"],
            #                                     "pos": token["upos"],
            #                                     "ms": " "})

            if token["deprel"] == "conj":
                selected_ids.append(sentence["id"])

        if sentence["id"] in selected_ids:
            selected_dict["sentences"].append(sentence)

    return selected_dict, selected_ids


def conj_info_extraction(dict_parsed: dict) -> None:  
    for sentence in dict_parsed["sentences"]:
        sentence["coordination_info"] = []
        all_conj_counter = 0
        for token in sentence["tokens"]:

            if token["deprel"] == "conj" and sentence["tokens"][token["head"] - 1]["conj_count"] == 0:
                all_conj_counter += 1
                # the head of the first token that has a conj deprel is the left head (head of first conjunct)
                left_token_conj = sentence["tokens"][token["head"] - 1]

                # if there are more than two conjuncts, choose the last one
                for child in left_token_conj["children"]:
                    if sentence["tokens"][child["id"] - 1]["deprel"] == "conj":
                        left_token_conj["conj_count"] += 1
                        right_token_conj = sentence["tokens"][child["id"] - 1]

                for child in right_token_conj["children"]:
                    if child["deprel"] == "cc":
                        cc_no = all_conj_counter
                        cc_word = sentence["tokens"][child["id"] - 1]["text"]
                        cc_tag = sentence["tokens"][child["id"] - 1]["xpos"]
                        cc_pos = sentence["tokens"][child["id"] - 1]["upos"]
                        try:
                            cc_ms = sentence["tokens"][child["id"] - 1]["feats"]
                        except KeyError:
                            cc_ms = ""
                    elif ("cc" not in right_token_conj["all_deprels"]):
                          #and child["deprel"] == "punct"
                          #and child["id"] < right_token_conj["id"]):
                        cc_no = all_conj_counter
                        cc_word = ""
                        cc_tag = ""
                        cc_pos = ""
                        cc_ms = ""
                        # cc_word = sentence["tokens"][child["id"] - 1]["text"]
                        # cc_tag = sentence["tokens"][child["id"] - 1]["xpos"]
                        # cc_pos = sentence["tokens"][child["id"] - 1]["upos"]
                        # try:
                        #     cc_ms = sentence["tokens"][child["id"] - 1]["feats"]
                        # except KeyError:
                        #     cc_ms = ""
                
                if left_token_conj["head"] != 0:
                    governor = sentence["tokens"][left_token_conj["head"] - 1]
                else:
                    governor = left_token_conj

                if governor["id"] < left_token_conj["id"]:
                    # governor is on the left
                    governor_dir = "L"
                elif governor["id"] > left_token_conj["id"]:
                    # governor is on the right
                    governor_dir = "R"
                else:
                    # there is no governor
                    governor_dir = "0"

                if governor_dir == "0":
                    text, xpos, upos, ms = " ", " ", " ", " "
                else:
                    text = governor["text"]
                    xpos = governor["xpos"]
                    upos = governor["upos"]
                    try:
                        ms = governor["feats"]
                    except KeyError:
                        ms = " "

                try:
                    left_feats = left_token_conj["feats"]
                    right_feats = token["feats"]
                except KeyError:
                    left_feats = " "
                    right_feats = " "
                
                sentence["coordination_info"].append({"left_head": left_token_conj,
                                                      "right_head": right_token_conj,
                                                      "text": {"left": left_token_conj["text"],
                                                               "right": right_token_conj["text"]},
                                                      "left_deplabel": left_token_conj["deprel"],
                                                      "right_deplabel": right_token_conj["deprel"],
                                                      "left_tag": left_token_conj["xpos"],
                                                      "right_tag": right_token_conj["xpos"],
                                                      "left_upos": left_token_conj["upos"],
                                                      "right_upos": right_token_conj["upos"],
                                                      "left_ms": left_feats,
                                                      "right_ms": right_feats,
                                                      "governor": text,
                                                      "governor_dir": governor_dir,
                                                      "governor_tag": xpos,
                                                      "governor_pos": upos,
                                                      "governor_ms": ms,
                                                      "count":  left_token_conj["conj_count"],
                                                      "cc": {"word": cc_word,
                                                             "tag": cc_tag,
                                                             "pos": cc_pos,
                                                             "no": cc_no,
                                                             "ms": cc_ms}
                                                      })
      

def search_for_dependencies(sentence: dict) -> None:
    '''
    Przerobiony kod od Magdy
    '''

    for con in sentence["coordination_info"]:
        left_list = []
        right_list = []

        left_deprels = []
        right_deprels = []
        for child in con["left_head"]["children"]:
            if (sentence["tokens"][child["id"] - 1]["id"] != con["right_head"]["id"]
                and sentence["tokens"][child["id"] - 1]["deprel"] != "cc"
                and sentence["tokens"][child["id"] - 1]["text"] != "."
                and sentence["tokens"][child["id"] - 1]["deprel"] != "conj"
                and child["id"] < con["right_head"]["id"]):
                left_list.append(child["id"])
                left_deprels.append(sentence["tokens"][child["id"] - 1]["deprel"])

        for child in con["right_head"]["children"]:
            if (sentence["tokens"][child["id"] - 1]["deprel"] != "cc"):
                right_list.append(child["id"])
                right_deprels.append(sentence["tokens"][child["id"] - 1]["deprel"])
       
        for id in left_list[:]:
            if ((id < con["left_head"]["id"]
                and sentence["tokens"][id - 1]["deprel"] not in right_deprels
                and min(left_list) >= id)
                or (sentence["tokens"][max(left_list) - 1]["text"] == ",")
                or (sentence["tokens"][min(left_list) - 1]["text"] == ",")):
                left_list.remove(id)

        for id in right_list[:]:
            if (id == min(right_list) 
                and sentence["tokens"][id - 1]["text"] == ","):
                right_list.remove(id)

        for child in left_list:
            for t in sentence["tokens"][child - 1]["children"]:
                left_list.append(t["id"])
        for child in right_list:
            for t in sentence["tokens"][child - 1]["children"]:
                right_list.append(t["id"])
        
        left_list.append(con["left_head"]["id"])
        right_list.append(con["right_head"]["id"])

        left = ""
        right = ""

        Rwords = 0
        Lwords = 0

        Rtokens = 0
        Ltokens = 0

        Rsyllables = 0
        Lsyllables = 0

        left_list.sort()
        right_list.sort()

        for id in left_list:
            Ltokens += 1
            Lsyllables += syllables(sentence["tokens"][id - 1]["text"])

            if sentence["tokens"][id - 1]["deprel"] != "punct":
                Lwords += 1

            left += sentence["tokens"][id - 1]["text"]

            if (sentence["tokens"][id]["text"] in [",", ".", ";", ":", ")", "%", "-"] or
                sentence["tokens"][id - 1]["text"] in ["(", "-"]):
                left += ""
            elif id < max(left_list):
                left += " "
            # if id < max(left_list):
            #     left += " "
                
        for id in right_list:
            Rtokens += 1
            Rsyllables += syllables(sentence["tokens"][id - 1]["text"])

            if sentence["tokens"][id - 1]["deprel"] != "punct":
                Rwords += 1
            right += sentence["tokens"][id - 1]["text"]
            if (sentence["tokens"][id]["text"] in [",", ".", ";", ":", ")", "%", "-"] or
                sentence["tokens"][id - 1]["text"] in ["(", "-"]):
                right += ""
            elif id < max(right_list):
                right += " "
            # TO DO : FIX THIS
            # if id < max(right_list): 
            #     right += " "

        # quote marks
        # \(\s*([^()]*?)\s*\)
        right = re.sub(r'"\s*([^"]*?)\s*"', r'"\1"', right)
        left = re.sub(r'"\s*([^"]*?)\s*"', r'"\1"', left)
        # contractions
        right = re.sub(r"\b(\w+)\s+'(\w+)\b", lambda match: match.group(1) + "'" + match.group(2), right)
        left = re.sub(r"\b(\w+)\s+'(\w+)\b", lambda match: match.group(1) + "'" + match.group(2), left)
        # parenthesis
        # right = re.sub(r'\(\s*([^()]*?)\s*\)', r'(\1)', right)
        # left = re.sub(r'\(\s*([^()]*?)\s*\)', r'(\1)', left)       

        con["right_text"] = right
        con["left_text"] = left

        con["Rwords"] = Rwords
        con["Lwords"] = Lwords

        con["Rtokens"] = Rtokens
        con["Ltokens"] = Ltokens

        con["Rsyllables"] = Rsyllables
        con["Lsyllables"] = Lsyllables


def search_for_id(dict_parsed: dict) -> re.Match[str]:
    '''
    Returns a matched string with line id from the corpus.
    '''
    match = re.search(r"@@\d*", dict_parsed["text"])
    return match.group(0)


def addline(conj: dict,
            word: dict, 
            sentence: dict, 
            file_path: str, 
            genre: str, 
            sent_id: str
    ) -> dict:
    line = {"governor.position": conj["governor_dir"],
            "governor.word": conj["governor"],
            "governor.tag": conj["governor_tag"],
            "governor.pos": conj["governor_pos"],
            "governor.ms": conj["governor_ms"],
            "conjunction.word": word["word"],
            "conjunction.tag": word["tag"],
            "conjunction.pos": word["pos"],
            "conjunction.ms": word["ms"],
            "no.conjuncts": conj["count"] + 1,
            "L.conjunct": conj["left_text"],
            "L.dep.label": conj["left_deplabel"],
            "L.head.word": conj["text"]["left"],
            "L.head.tag": conj["left_tag"],
            "L.head.pos": conj["left_upos"],
            "L.head.ms": conj["left_ms"],
            "L.words": conj["Lwords"],
            "L.tokens": conj["Ltokens"],
            "L.syllables": conj["Lsyllables"],
            "L.chars": len(conj["left_text"]),
            "R.conjunct": conj["right_text"],
            "R.dep.label": conj["right_deplabel"],
            "R.head.word": conj["text"]["right"],
            "R.head.tag": conj["right_tag"],
            "R.head.pos": conj["right_upos"],
            "R.head.ms": conj["right_ms"],
            "R.words": conj["Rwords"],
            "R.tokens": conj["Rtokens"],
            "R.syllables": conj["Rsyllables"],
            "R.chars": len(conj["right_text"]),
            "sentence": sentence["text"],
            "sent.id": sent_id + "-" + str(sentence["id"] - 1),
            "genre": genre,
            "converted.from.file": file_path
}

    return line