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
CSV_PATH = "data/csv/text_test_sample_another_base.csv"
CREATE_CONLL = True


def main():
    # time counter
    time_start = time.perf_counter()
    # initialize the pipeline
    eng_pipeline = Pipeline("english",
                            gpu=True,
                            cache_dir="cache",
                            embedding='xlm-roberta-base')
    # extract the genre from filename
    # genre = CORPUS_PATH.split("_")[1].split(".")[0]
    # load the data
    text = other.load_data(SENTENCES_PATH, type="tsv")
    # load the template of data
    template = other.create_template_from_csv(TEMPLATE_PATH)
    # create data storing object
    info_csv = CSVInfo(template)
    # create conllu docs
    # Looping through lines in file
    for i in tqdm(range(0    , len(text))):
        # empty cuda memory after every iteration
        torch.cuda.empty_cache()
        genre = text["FILE"][i].split("_")[1].split(".")[0]
        # create placeholder dict for storing a sentence
        # (in order to not change the code)
        placeholder_dict = {"sentences": []}  # FIX THIS
        # parse sentences
        dict_sentence = sentences.depparse_sentences(eng_pipeline,
                                                     text["SENT"][i],
                                                     sent=True)
        # get id from sentences tsv
        dict_sentence["id"] = text["0"][i]
        # append sentence dict to the placeholder dict
        placeholder_dict["sentences"].append(dict_sentence)
        # select only these sentences that have coordinations
        conj_depparsed, selected_ids = extract.select_conj(placeholder_dict)
        # create conllu docs
        if CREATE_CONLL and len(selected_ids) > 0:
            other.toconllu(conj_depparsed,
                           f"data/conll/conllu_conj{text['0'][i]}_{genre}.conll")
        # extract all the info about coordinations ???
        extract.conj_info_extraction(conj_depparsed)
        # Adding info
        for sentence in conj_depparsed["sentences"]:
            extract.search_for_dependencies(sentence)
            for key in sentence["coordination_info"]:
                # add row to info object
                info_csv.add_row(extract.addline(
                    sentence["coordination_info"][key],
                    sentence,
                    text["FILE"][i],
                    genre,
                    f"{text['PARA ID'][i]}-{text['0'][i]}"
                ))
        # export info object
        info_csv.export(CSV_PATH)

    # Time and resources
    time_elapsed = (time.perf_counter() - time_start)
    memMb = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
    print("%5.1f secs %5.1f MByte" % (time_elapsed, memMb))


if __name__ == "__main__":
    main()