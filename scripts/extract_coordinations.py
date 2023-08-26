from trankit import Pipeline
from tqdm import tqdm
import time
import resource
import torch

from coord.utils.data import CSVInfo
from coord.utils import other
from coord.utils import cleaning
from coord.tools import extract
from coord.tools import sentences

# Constant variables
CORPUS_PATH = "data/samples/coca-samples/text_acad_1990.txt"
SENTENCES_PATH = "data/csv/trankit_sentences_acad_1990.tsv"
TEMPLATE_PATH = "data/csv/UD_Polish-LFG.csv"
CSV_PATH = "data/csv/text_test_sample_another.csv"

def main():

    time_start = time.perf_counter()                                # time counter

    eng_pipeline = Pipeline("english", gpu=True, cache_dir="cache", embedding='xlm-roberta-base') # initialize the pipeline

    genre = CORPUS_PATH.split("_")[1].split(".")[0]                 # extract the genre from filename
    text = other.load_data(SENTENCES_PATH, type="tsv")              # load the data
    # text = other.load_data(CORPUS_PATH, type="txt")

    template = other.create_template_from_csv(TEMPLATE_PATH)        # load the template of data
    info_csv = CSVInfo(template)                                    # create data storing object

    create_conll = True                                             # create conllu docs

    # Looping through lines in .txt file
    for i in tqdm(range(114, 1800)):
        # empty cuda memory after every iteration
        torch.cuda.empty_cache()

        # create placeholder dict for storing a sentence (in order to not change the code) 
        placeholder_dict = {"sentences": []}                                    # FIX THIS

        dict_sentence = sentences.depparse_sentences(eng_pipeline,              # parse sentences
                                                     text["SENT"][i], 
                                                     sent=True)
        dict_sentence["id"] = text["0"][i]                                      # get id from sentences tsv
        placeholder_dict["sentences"].append(dict_sentence)                     # append sentence dict to the placeholder dict
        conj_depparsed, selected_ids = extract.select_conj(placeholder_dict)    # select only these sentences that have coordinations
        
        # create conllu docs
        if create_conll:
            other.toconllu(dict_sentence, f"data/conll/conllu_conj{i}_{genre}.conll")

        extract.conj_info_extraction(conj_depparsed)                            # extract all the info about coordinations ???

        # Adding info
        for sentence in conj_depparsed["sentences"]:
            extract.search_for_dependencies(sentence)                           # ???

            for key in sentence["coordination_info"]:                 # ???
                info_csv.add_row(extract.addline(sentence["coordination_info"][key],                          # add row to info object
                                                 sentence, 
                                                 CORPUS_PATH.split("/")[3], 
                                                 genre, 
                                                 text["PARA ID"][i]))
        info_csv.export(CSV_PATH)                                               # export info object

    # Time and resources
    time_elapsed = (time.perf_counter() - time_start)
    memMb = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
    print("%5.1f secs %5.1f MByte" % (time_elapsed, memMb))


if __name__ == "__main__":
    main()