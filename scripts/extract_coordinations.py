import time
import resource
import argparse
import torch
import pandas as pd

from trankit import Pipeline
from tqdm import tqdm

from coord.utils import other, cleaning, data
from coord.tools import extract, sentences


def parse_and_add_info_tsv(text, pipeline, create_conll, csv_file):
    for i in tqdm(range(0, len(text))):
        # empty cuda memory after every iteration
        torch.no_grad()
        torch.cuda.empty_cache()
        genre = text["FILE"][i].split("_")[1].split(".")[0]
        placeholder_dict = {"sentences": []} 
        sent = cleaning.remove_whitespaces(text["SENT"][i])
        dict_sentence = sentences.depparse_sentences(pipeline,
                                                     sent,
                                                     sent=True)
        # get id from sentences tsv
        dict_sentence["id"] = text["0"][i]
        # append sentence dict to the placeholder dict
        placeholder_dict["sentences"].append(dict_sentence)
        # select only these sentences that have coordinations
        conj_depparsed, selected_ids = extract.select_conj(placeholder_dict)
        # create conllu docs
        if create_conll and len(selected_ids) > 0:
            other.toconllu(conj_depparsed,
                           f"conllu_conj_{genre}_{str(int(text['YEAR'][i]))}.conll",
                           f"{text['PARA ID'][i]}-{str(int(text['0'][i]))}",
                           sent)

        extract.conj_info_extraction(conj_depparsed)

        # Adding info
        for sentence in conj_depparsed["sentences"]:
            extract.search_for_dependencies(sentence)
            for key in sentence["coordination_info"]:
                # add row to info object
                csv_file.add_row(extract.addline(
                    sentence["coordination_info"][key],
                    sentence,
                    text["FILE"][i],
                    genre,
                    f"{text['PARA ID'][i]}-{str(int(text['0'][i]))}"
                ))
    # export info object
    csv_file.export(f"trankit_coordinations_{genre}_{str(int(text['YEAR'][1]))}.csv")   


def parse_and_add_info_txt(text, pipeline, create_conll, csv_file, filename):
    for i in tqdm(range(1, len(text))):
        torch.no_grad()
        torch.cuda.empty_cache()
        genre = filename.split("_")[-2]
        year = filename.split("_")[-1].split('.')[0]
        text[i] = cleaning.clean_text(text[i])
        dict_sentences = sentences.depparse_sentences(pipeline,
                                                      text[i],
                                                      sent=False)
        clean_sentences, _ = cleaning.clean_parsed(dict_sentences)
        sent_id = extract.search_for_id(clean_sentences)
        conj_sentences, selected_ids = extract.select_conj(clean_sentences)
        extract.conj_info_extraction(conj_sentences)
    
    for sentence in conj_sentences["sentences"]:
        sentence["text"] = cleaning.remove_whitespaces(sentence["text"])
        if create_conll and len(selected_ids) > 0:
            other.toconllu(conj_sentences,
                           f"conllu_conj_{genre}_{year}.conll",
                           f"{sent_id}-{int(sentence['id']) - 1}",
                           sentence["text"])
        extract.search_for_dependencies(sentence)
        for key in sentence["coordination_info"]:
            # add row to info object
            csv_file.add_row(extract.addline(
                sentence["coordination_info"][key],
                sentence,
                filename,
                genre,
                f"{sent_id}-{int(sentence['id']) - 1}"
            ))
    # export info object
    csv_file.export(f"trankit_coordinations_{genre}_{year}.csv")   
        

def main(file_path, use_gpu, create_conll):
    torch.no_grad()
    torch.cuda.empty_cache()
    info_csv = data.CSVInfo(cols=[
        "governor.position", "governor.word", "governor.tag",
        "governor.pos", "governor.ms", "conjunction.word",
        "conjunction.tag", "conjunction.pos", "conjunction.ms",
        "no.conjuncts", "L.conjunct", "L.dep.label",
        "L.head.word", "L.head.tag", "L.head.pos",
        "L.head.ms", "L.words", "L.tokens",
        "L.syllables", "L.chars", "R.conjunct",
        "R.dep.label", "R.head.word", "R.head.tag",
        "R.head.pos", "R.head.ms", "R.words",
        "R.tokens", "R.syllables", "R.chars", 
        "sentence", "sent.id", "genre",
        "converted.from.file"])
    # time counter
    time_start = time.perf_counter()
    # initialize the pipeline
    eng_pipeline = Pipeline("english",
                            gpu=use_gpu,
                            cache_dir="cache",
                            embedding='xlm-roberta-base')
    if file_path.split(".")[-1] == "txt":
        text = other.load_data(file_path, type="txt")
        parse_and_add_info_txt(text, eng_pipeline, 
                               create_conll, info_csv, file_path)
    elif file_path.split(".")[-1] == "tsv":
        text = other.load_data(file_path, type="tsv")
        parse_and_add_info_tsv(text, eng_pipeline, create_conll, info_csv) 
    else:
        raise TypeError("Unknown type of input file, should be"
                        "either .txt or .tsv")
    
    # Time and resources
    time_elapsed = (time.perf_counter() - time_start)
    memMb = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
    print("%5.1f secs %5.1f MByte" % (time_elapsed, memMb))


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(
        description="Extract coordination info from corpora or sentence files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argument_parser.add_argument("-f", 
                                 "--files",
                                 nargs="+",
                                 type=str,
                                 help="input files to parse")
    argument_parser.add_argument("-g",
                                 "--gpu",
                                 action="store_true",
                                 help="use gpu for parsing")
    argument_parser.add_argument("-c",
                                 "--conll",
                                 action="store_true",
                                 help="generate conll file")
    args = argument_parser.parse_args()

    for file in args.files:
        main(file, args.gpu, args.conll)
