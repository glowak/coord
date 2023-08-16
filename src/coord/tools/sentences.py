from trankit import Pipeline
from tqdm import tqdm

from coord.utils.other import load_data
from coord.tools.extract import search_for_id
from coord.utils.data import CSVInfo
from coord.utils import cleaning


def sentence_split_exporting(data_path: str,
                             export_path: str,
                             export_to: str) -> None:

    p = Pipeline("english", gpu=False)
    
    
    document = load_data(data_path)
    if export_to == "csv":
        csv = CSVInfo(cols=["sentence", "id_trankit", "id_global"])
    elif export_to == "txt":
        file = open(export_path, "w")

    for i in tqdm(range(0, len(document))):
        document[i] = cleaning.remove_whitespaces(cleaning.clean_text(document[i]))
        split = p.ssplit(document[i])
        clean, rm_ids = cleaning.clean_parsed(split)
        
        for sentence in split["sentences"]:
            if export_to == "csv":
                csv.add_row({"sentence": sentence["text"],
                             "id_trankit": sentence["id"],
                             "id_global": "{}-{}".format(search_for_id(split), str(sentence["id"] - 1))
                             })
            elif export_to == "txt":
                    file.write(sentence["text"] + "\n")
                
    if export_to == "csv":
        csv.export(export_path)
    elif export_to == "txt":
        file.close()


def depparse_sentences(pipeline: Pipeline,
                       data: str) -> dict:
    
    sentences = pipeline.posdep(data)
    return sentences