from trankit import Pipeline
from tqdm import tqdm

from coord.utils.other import load_data
from coord.tools.extract import search_for_id, select_conj
from coord.utils.data import CSVInfo, TSVInfo
from coord.utils import cleaning


def sentence_split_exporting(data_path: str,
                             export_path: str,
                             export_to: str) -> None:

    p = Pipeline("english", gpu=True)
    
    
    document = load_data(data_path)
    if export_to == "csv":
        csv = CSVInfo(cols=["sentence", "id_trankit", "id_global"])
    elif export_to == "txt":
        file = open(export_path, "w")
    elif export_to == "tsv":
        tsv = TSVInfo(cols=["0", "SENT", "TYPE", "YEAR", "FILE", "PARA ID"])

    id = 1
    for i in tqdm(range(0, len(document))):
        document[i] = cleaning.remove_whitespaces(cleaning.clean_text(document[i]))
        split = p.ssplit(document[i])
        clean, rm_ids = cleaning.clean_parsed(split)
        
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
                                 "FILE": data_path.split("/")[3],
                                 "PARA ID": para_id})
                    id += 1
                
    if export_to == "csv":
        csv.export(export_path)
    elif export_to == "txt":
        file.close()
    elif export_to == "tsv":
        tsv.export(export_path)


def depparse_sentences(pipeline: Pipeline,
                       data: str) -> dict:
    
    sentences = pipeline.posdep(data)
    return sentences