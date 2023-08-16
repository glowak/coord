from coord.tools.sentences import sentence_split_exporting

EXPORT_PATH = "data/txt/trankit_split_sentences_test.txt"
DATA_PATH = "data/samples/coca-samples/text_test_sample.txt"

if __name__ == "__main__":
    sentence_split_exporting(DATA_PATH, EXPORT_PATH, "txt")