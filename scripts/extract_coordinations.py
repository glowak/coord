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

CORPUS_PATH = "data/samples/coca-samples/text_test_sample.txt"
TEMPLATE_PATH = "data/csv/UD_Polish-LFG.csv"
CSV_PATH = "data/csv/text_test_sample_another.csv"

def main():

    time_start = time.perf_counter()

    eng_pipeline = Pipeline("english", gpu=True, cache_dir="cache")

    genre = CORPUS_PATH.split("_")[1].split(".")[0]
    text = other.load_data(CORPUS_PATH)

    template = other.create_template_from_csv(TEMPLATE_PATH)
    info_csv = CSVInfo(template)

    create_conll = True

    # Looping through lines in .txt file
    for i in tqdm(range(0, len(text))):
        torch.cuda.is_available()
        torch.cuda.empty_cache()
        text[i] = cleaning.clean_text(text[i])

        dict_of_sentences = sentences.depparse_sentences(eng_pipeline, text[i])
        clean_depparsed, removed_ids = cleaning.clean_parsed(dict_of_sentences)
        conj_depparsed, selected_ids = extract.select_conj(clean_depparsed)
        
        if create_conll:
            other.toconllu(conj_depparsed, f"data/conll-docs/conllu_conj{i}_{genre}.conll")

        sent_id = extract.search_for_id(clean_depparsed)

        extract.conj_info_extraction(conj_depparsed)

        # Adding info
        for sentence in conj_depparsed["sentences"]:
            extract.search_for_dependencies(sentence)

            for i in range(len(sentence["coordination_info"])):

                try:
                    word = sentence["words_cconj"][i]
                except IndexError:
                    word_first = {"no": "",
                                  "word": "",
                                  "tag": "",
                                  "pos": "",
                                  "ms": ""}

                conj = sentence["coordination_info"][i]

                info_csv.add_row(extract.addline(conj, conj["cc"], sentence, CORPUS_PATH.split("/")[3], genre, sent_id))
        info_csv.export(CSV_PATH)

    # Time and resources
    time_elapsed = (time.perf_counter() - time_start)
    memMb = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
    print("%5.1f secs %5.1f MByte" % (time_elapsed, memMb))


if __name__ == "__main__":
    main()