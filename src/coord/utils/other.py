import pandas as pd
import csv

from trankit import trankit2conllu


def load_data(path: str,
              type: str):
    '''
    Load data from specified file.
    '''
    if type == "txt":
        with open(path, "r") as file:
            document = file.readlines()
    elif type == "tsv":
        document = pd.read_csv(path, sep="\t", quoting=csv.QUOTE_NONE, escapechar="\n")
    return document


def create_template_from_csv(columns_info_path: str) -> pd.DataFrame:
    ''' 
    Create csv file template from another csv.
    '''
    template = pd.read_csv(columns_info_path)
    return template


def toconllu(parsed_data: dict, 
             filename: str,
             id,
             sent) -> None:
    '''
    Convert sentences to conllu and append to a file.
    '''
    conllu_doc = trankit2conllu(parsed_data)
    with open(filename, "a") as file:
        file.write(f"# ID : {id}\n")
        file.write(f"# SENTENCE : {sent}\n")
        file.write(conllu_doc)
        file.write("\n")
