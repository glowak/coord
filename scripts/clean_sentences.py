from tqdm import tqdm
import re
from coord.utils.cleaning import clean_text, remove_whitespaces
from coord.utils.other import load_data
from coord.tools.extract import search_for_id
from coord.utils.data import TSVInfo

DATA_PATH = "data/txt/trankit_sentences_acad_1990.txt"
EXPORT_PATH = "data/csv/trankit_sentences_acad_1990_t.tsv"

document = load_data(DATA_PATH)

tsv = TSVInfo(cols=["0", "SENT", "TYPE", "YEAR", "FILE", "PARA ID"])

id = 1
for i in tqdm(range(0, len(document))):
    document[i] = remove_whitespaces(clean_text(document[i]))
    if document[i].startswith("@@"):
        para_id = re.match(r"@@\d*", document[i].strip())
    else:
        tsv.add_row({"0": id,
                    "SENT": document[i].strip(),
                    "TYPE": "acad",
                    "YEAR": "1990",
                    "FILE": "text_acad_1990.txt",
                    "PARA ID": para_id.group(0)})
        id += 1

tsv.export(EXPORT_PATH)