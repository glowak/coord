from coord.tools.sentences import sentence_split_exporting

EXPORT_PATH = "data/txt/trankit_split_sentences_acad_test.tsv"
DATA_PATH = "data/samples/coca-samples/text_acad_2000.txt"

if __name__ == "__main__":
    sentence_split_exporting(DATA_PATH, EXPORT_PATH, "tsv")