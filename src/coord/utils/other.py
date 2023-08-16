import pandas as pd
from trankit import trankit2conllu


def load_data(corpus: str) -> list[str]:
    with open(corpus, "r") as file:
        document = file.readlines()
    return document

def create_template_from_csv(columns_info_path: str) -> pd.DataFrame:
    template = pd.read_csv(columns_info_path)
    return template

def toconllu(parsed_data: dict, 
             filename: str) -> None:
    conllu_doc = trankit2conllu(parsed_data)
    with open(filename, "w") as file:
        file.write(conllu_doc)