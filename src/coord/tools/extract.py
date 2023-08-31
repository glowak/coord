import re

from coord.tools.syllables import count_word


def select_conj(dict_parsed: dict) -> tuple[dict, list[int]]:
    '''
    Selects all the sentences with at least one conjunction and adds
    key with a list of dictionaries, containing conjunction words and 
    information about them. Also, adds information about dependencies 
    and token children.

    Returns a dictionary and a list of selected sentences' ids.
    '''

    selected_dict = {}
    selected_dict["sentences"] = []
    selected_ids = []

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
    
    '''
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
                    governor_text = " "
                    governor_xpos = " "
                    governor_upos = " "
                    governor_ms = " "
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
        

def get_children(id_list, sentence):
        for child in id_list:
            for t in sentence["tokens"][child - 1]["children"]:
                id_list.append(t["id"])


def match_conjuncts(conj_match, sentence, current_conj, id_list, side):
    if conj_match != None:
        sentence["coordination_info"][current_conj][f"{side}_text"] = conj_match.group(0)
    else:
        sentence["coordination_info"][current_conj][f"{side}_text"] = sentence["tokens"][id_list[0] - 1]["text"]
        for i in range(0, len(id_list) - 3):
            pattern = re.escape(sentence["tokens"][id_list[i] - 1]["text"]) + r"(\s*)" + re.escape(sentence["tokens"][id_list[i + 1] - 1]["text"])
            match_text = re.search(pattern, sentence["text"])
            if match_text != None:
                sentence["coordination_info"][current_conj][f"{side}_text"] += match_text.group(1)
            # else:
                # sentence["coordination_info"][current_conj][f"{side}_text"] += " "
            
            sentence["coordination_info"][current_conj][f"{side}_text"] += sentence["tokens"][id_list[i + 1] - 1]["text"]


def count_and_find_conjs(id_list, sentence, current_conj, side):
    side_tokens = f"{side}tokens"
    side_syll = f"{side}syllables"
    side_words = f"{side}words"
    conj_match = ""
    for id in id_list:
        sentence["coordination_info"][current_conj][side_tokens] += 1
        sentence["coordination_info"][current_conj][side_syll] += count_word(sentence["tokens"][id - 1]["text"])
        if sentence["tokens"][id - 1]["deprel"] != "punct":
            sentence["coordination_info"][current_conj][side_words] += 1
        conj_match += re.escape(sentence["tokens"][id - 1]["text"]) + "\s*"
    return re.search(conj_match, sentence["text"])        

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
        # Append conjunct tokens that are directly connected to the left and 
        # right heads of conjuncts to left and right lists 
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
        get_children(left_list, sentence) 
        get_children(right_list, sentence)
        
        # Append the heads of conjuncts to the whole conjunct 
        left_list.append(sentence["coordination_info"][con]["left_head_token"]["id"])
        right_list.append(sentence["coordination_info"][con]["right_head_token"]["id"])

        # Sort lists in ascending order
        left_list.sort()
        right_list.sort()

        # Remove certain tokens from lists 
        for id in left_list[:]:
                # remove punctuation
            if ((id == min(left_list) and sentence["tokens"][id - 1]["text"] in [",", ";", "-"])
                or (id == max(left_list) and sentence["tokens"][id - 1]["text"] in [",", "."])
                # remove every token on the left of left conjunct if the 
                # right conjunct doesn't have the same deprels somewhere
                or (id < sentence["coordination_info"][con]["left_head_token"]["id"]
                    and sentence["tokens"][id - 1]["deprel"] not in right_deprels    
                    and min(left_list) >= id)):
                left_list.remove(id)
        for id in right_list[:]:
                # remove a comma on the beginning or end the right conjunct
            if ((id == min(right_list) and sentence["tokens"][id - 1]["text"] == ",")     
                or (id == max(right_list) and sentence["tokens"][id - 1]["text"] == ",")):
                right_list.remove(id)

        # Declare variables storing information about conjuncts
        sentence["coordination_info"][con]["Rwords"] = 0
        sentence["coordination_info"][con]["Lwords"] = 0
        sentence["coordination_info"][con]["Rtokens"] = 0
        sentence["coordination_info"][con]["Ltokens"] = 0
        sentence["coordination_info"][con]["Rsyllables"] = 0
        sentence["coordination_info"][con]["Lsyllables"] = 0

        # Count tokens, syllables, words and find conjuncts in sentence
        right_match = count_and_find_conjs(right_list, sentence, con, "R")
        left_match = count_and_find_conjs(left_list, sentence, con, "L")
        
        # Get the variables and save to dictionary
        match_conjuncts(right_match, sentence, con, right_list, "right") 
        match_conjuncts(left_match, sentence, con, left_list, "left") 


def search_for_id(dict_parsed: dict) -> re.Match[str]:
    '''
    Matches a string with line id.
    
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
    ''' 
    Generates a line with relevant information that can be appended 
    to a .csv file.
    '''
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
            "L.chars": len(conj["left_text"].strip()),
            "R.conjunct": conj["right_text"],
            "R.dep.label": conj["right_head_token"]["deprel"],
            "R.head.word": conj["right_head_token"]["text"],
            "R.head.tag": conj["right_head_token"]["xpos"],
            "R.head.pos": conj["right_head_token"]["upos"],
            "R.head.ms": conj["right_feats"],
            "R.words": conj["Rwords"],
            "R.tokens": conj["Rtokens"],
            "R.syllables": conj["Rsyllables"],
            "R.chars": len(conj["right_text"].strip()),
            "sentence": sentence["text"],
            "sent.id": sent_id,
            "genre": genre,
            "converted.from.file": file_path
}
    return line
