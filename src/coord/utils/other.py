import pandas as pd
import csv
from trankit import trankit2conllu


def load_data(path: str,
              type: str):
    if type == "txt":
        with open(path, "r") as file:
            document = file.readlines()
    elif type == "tsv":
        document = pd.read_csv(path, sep="\t", quoting=csv.QUOTE_NONE, escapechar="\n")
    return document

def create_template_from_csv(columns_info_path: str) -> pd.DataFrame:
    template = pd.read_csv(columns_info_path)
    return template

def toconllu(parsed_data: dict, 
             filename: str) -> None:
    conllu_doc = trankit2conllu(parsed_data)
    with open(filename, "w") as file:
        file.write(conllu_doc)