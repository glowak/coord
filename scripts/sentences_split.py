import argparse
import re
from typing import Optional
from abc import ABC, abstractmethod

import pandas as pd
from trankit import Pipeline
from tqdm import tqdm

class Info(ABC):
    ''' 
    An abstract class representing a pandas DataFrame with information.
    '''
    def __init__(self,
                 template: Optional[pd.DataFrame] = None,
                 cols: Optional[list] = None):
        assert template is not None or cols is not None, "columns or template must be specified"
        
        if template is not None:
            self.table = pd.DataFrame(columns=template.columns)
        else:
            self.table = pd.DataFrame(columns=cols)
            
    def add_row(self,
                info: dict) -> None:
        self.table.loc[len(self.table)] = info
    
    @abstractmethod
    def export(self,
               path: str) -> None:
        pass

class CSVInfo(Info):
    '''
    A class representing a .csv document with information.
    '''
    def __init__(self, 
                 template: Optional[pd.DataFrame] = None, 
                 cols: Optional[list] = None):
        super().__init__(template, cols)

    def export(self,
               path: str) -> None:
        self.table.to_csv(path, index=False)
        
class TSVInfo(Info):
    '''
    A class representing a .tsv document with information.
    '''
    def __init__(self, 
                 template: Optional[pd.DataFrame] = None, 
                 cols: Optional[list] = None):
        super().__init__(template, cols)
    
    def export(self, 
               path: str) -> None:
        self.table.to_csv(path, sep="\t", index=False)

def load_data(corpus: str) -> list[str]:
    with open(corpus, "r") as file:
        document = file.readlines()
    return document

def remove_whitespaces(data: str):
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

def clean_text(text: str) -> str:
    text_sub = re.sub(r'<p>|<h>|@!',"", text)
    return text_sub

def clean_parsed(dict_parsed: dict) -> tuple[dict, list]:
    '''
    Removes all sentences that contain copyright-avoiding string "@ @ @ ..." and header tags.
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

def search_for_id(dict_parsed: dict) -> re.Match[str]:
    '''
    Returns a matched string with line id from the corpus.
    '''
    match = re.search(r"@@\d*", dict_parsed["text"])
    return match.group(0)

def sentence_split_exporting(data_path: str,
                             export_path: str,
                             export_to: str,
                             use_gpu) -> None:

    p = Pipeline("english", gpu=use_gpu)
    
    document = load_data(data_path)
    if export_to == "csv":
        csv = CSVInfo(cols=["sentence", "id_trankit", "id_global"])
    elif export_to == "txt":
        file = open(export_path, "w")
    elif export_to == "tsv":
        tsv = TSVInfo(cols=["0", "SENT", "TYPE", "YEAR", "FILE", "PARA ID"])

    id = 1
    for i in tqdm(range(0, len(document))):
        assert document[0] != " ", "blank line"
        document[i] = remove_whitespaces(clean_text(document[i]))
        split = p.ssplit(document[i])
        
        clean, rm_ids = clean_parsed(split)
        
        for sentence in clean["sentences"]:
            if export_to == "csv":
                csv.add_row({"sentence": sentence["text"],
                             "id_trankit": sentence["id"],
                             "id_global": "{}-{}".format(search_for_id(split), str(sentence["id"] - 1))
                             })
            elif export_to == "txt":
                file.write(sentence["text"] + "\n")
            elif export_to == "tsv":
                if sentence["text"].startswith("@@"):
                    para_id = sentence["text"]
                else:
                    tsv.add_row({"0": id,
                                 "SENT": sentence["text"],
                                 "TYPE": data_path.split("_")[1].split(".")[0],
                                 "YEAR": data_path.split("_")[2].split(".")[0],
                                 "FILE": data_path.split("/")[-1],
                                 "PARA ID": para_id})
                    id += 1
                
    if export_to == "csv":
        csv.export(export_path)
    elif export_to == "txt":
        file.close()
    elif export_to == "tsv":
        tsv.export(export_path)

def main():
    argument_parser = argparse.ArgumentParser(description="Split sentences using trankit and export to file.",
                                              formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argument_parser.add_argument("-t", "--type", type=str, help="type of output: [csv, txt, tsv]", default="tsv")
    argument_parser.add_argument("src", help="source file location (.txt file with corpus text)")
    argument_parser.add_argument("saved", help="saved file location")
    argument_parser.add_argument("-g", "--gpu", action="store_true", help="use gpu", default=False)
    args = argument_parser.parse_args()
   
    sentence_split_exporting(args.src, args.saved, args.type, args.gpu)
    
if __name__ == "__main__":
    main()