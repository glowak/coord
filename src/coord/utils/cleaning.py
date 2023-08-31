import re


def clean_text(text: str) -> str:
    ''' 
    Remove tags and strings "@!" from text.
    '''
    text_sub = re.sub(r'<p>|<h>|@!',"", text)
    return text_sub


def remove_whitespaces(data: str) -> str:
    ''' 
    Remove all whitespaces between punctuation marks and contractions.
    '''
    patterns = [
        (r'"\s*([^"]*?)\s*"', r'"\1"'),
        (r"\b(\w+)\s+'(\w+)\b", lambda match: match.group(1) + "'" + match.group(2)),
        (r'\s+([,\.])', r'\1'),
        (r'\s+(?=\))|(?<=\()\s+', ''),
        (r'\s+([:;!?])', r'\1'),
        (r'\s+(n\'t)', r"\1")
    ]

    for pattern, replacement in patterns:
        data = re.sub(pattern, replacement, data)
    
    return data


def clean_parsed(dict_parsed: dict) -> tuple[dict, list]:
    '''
    Removes all sentences that contain copyright-avoiding string "@ @ @ ...".
    Returns a dictionary with correct sentences and list of removed sentences' ids.
    '''

    clean_dict = {"sentences": []}
    clean_dict["text"] = dict_parsed["text"]
    removed_sentences_ids = []
    for sentence in dict_parsed["sentences"]:
        if re.search(r'@(\s@){8}\s@', sentence["text"]):
            removed_sentences_ids.append(sentence["id"])

        if sentence["id"] not in removed_sentences_ids:
            clean_dict["sentences"].append(sentence)

    return clean_dict, removed_sentences_ids
