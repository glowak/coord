import argparse
import pandas as pd

from trankit import Pipeline
from tqdm import tqdm

from coord.utils.other import load_data
from coord.tools.extract import search_for_id
from coord.utils.cleaning import clean_text, clean_parsed
from coord.utils.data import CSVInfo, TSVInfo


def sentence_split_exporting(data_path: str,
                             export_path: str,
                             export_to: str,
                             use_gpu,
                             use_base) -> None:

    if use_base: p = Pipeline("english", gpu=use_gpu, embedding='xlm-roberta-base')
    else: p = Pipeline("english", gpu=use_gpu, embedding='xlm-roberta-large')
    
    document = load_data(data_path)
    if export_to == "csv":
        csv = CSVInfo(cols=["sentence", "id_trankit", "id_global"])
    elif export_to == "txt":
        file = open(export_path, "w")
    elif export_to == "tsv":
        tsv = TSVInfo(cols=["0", "SENT", "TYPE", "YEAR", "FILE", "PARA ID"])

    id = 1
    for i in tqdm(range(1, len(document))):
        # document[i] = remove_whitespaces(clean_text(document[i]))
        document[i] = clean_text(document[i])
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

    
if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description="Split sentences using trankit and export to file.",
                                              formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argument_parser.add_argument("-t", "--type", type=str, help="type of output: [csv, txt, tsv]", default="tsv")
    argument_parser.add_argument("src", help="source file location (.txt file with corpus text)")
    argument_parser.add_argument("saved", help="saved file location")
    argument_parser.add_argument("-b", "--base", help="use base model", action="store_true", default=False)
    argument_parser.add_argument("-g", "--gpu", action="store_true", help="use gpu", default=False)
    args = argument_parser.parse_args()
   
    sentence_split_exporting(args.src, args.saved, args.type, args.gpu, args.base)