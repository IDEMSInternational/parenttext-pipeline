import json
from itertools import islice

import openpyxl


def process_keywords_to_file(sources, output):
    with open(output, "w") as outfile:
        json.dump(process_keywords(sources), outfile, indent=4)


def process_keywords(sources):
    return merge_dictionaries(
        {source.get("key", "unknown"): process_source(source) for source in sources}
    )


def process_source(source):
    input_file = source.get("location") or source["path"]
    language = source["key"]
    book = openpyxl.load_workbook(input_file, read_only=True)
    all_tables = {}

    for sheet in book.worksheets:
        try:
            all_tables[sheet.title] = process_sheet(sheet, language)
        except TableNotFoundError:
            continue

    return all_tables


def process_sheet(sheet, language):
    row_start = find_table_row_start(sheet) + 1
    misspellings_start = find_misspellings_col_start(sheet)
    pairs = batch(sheet.iter_rows(min_row=row_start), 2)

    return [
        wordset
        for source, translation in pairs
        if (
            wordset := create_wordset(language, misspellings_start, source, translation)
        )
    ]


def create_wordset(language, misspellings_start, source, translation):
    words = [
        read_cols(source, 1, misspellings_start),
        read_cols(source, misspellings_start),
        read_cols(translation, 1, misspellings_start),
        read_cols(translation, misspellings_start),
    ]

    if any(words):
        return {
            "English": {
                "keywords": words[0],
                "mispellings": words[1],
            },
            "Translation": {
                language: {
                    "keywords": words[2],
                    "mispellings": words[3],
                },
            },
        }
    else:
        return None


def find_table_row_start(sheet):
    """We assume that the table starts in the first column,
    in the left-most cell in the row before it we have a
    cell containing the matching string.

    Note: We assume there's only one such table per sheet.
    """
    MATCHING_STRING = (
        "Please insert translation of each word under each corresponding cell. If the "
        "particular word does not translate into the chosen language, please leave it "
        "blank"
    )
    index = index_of(
        [row[0] for row in sheet["A1":"A10"]],
        MATCHING_STRING,
    )

    if index == -1:
        raise TableNotFoundError()

    # to reference the next row
    return index + 1


def find_misspellings_col_start(sheet):
    HEADER2 = "Range of possible misspellings and common slang used by the population"
    index = -1

    for row in sheet.iter_rows():
        index = index_of(row, HEADER2)
        if index > -1:
            return index


def index_of(seq, value):
    try:
        return [i.value for i in seq].index(value)
    except ValueError:
        return -1


def read_cols(row, start, end=None):
    return [
        str(cell.value).strip() for cell in row[start:end] if cell.value is not None
    ]


def merge_dictionaries(dictionaries):
    it = iter(dictionaries.items())
    merged = next(it)[1]
    for lang, dic in it:
        for sheet in merged:
            if sheet in dic:
                for count, value in enumerate(merged[sheet]):
                    key_src = value["English"]["keywords"][0]
                    key_ref = next(
                        iter(dic[sheet][count]["English"]["keywords"]),
                        None,
                    )
                    if key_src == key_ref:
                        merged[sheet][count]["Translation"][lang] = dic[sheet][count][
                            "Translation"
                        ][lang]
                    else:
                        print(
                            f"There is a match problem in '{sheet}' sheet, please "
                            f"check all the spreadsheets have the same english rows in"
                            f"the same order"
                        )
                        break

    return merged


def batch(iterable, n):
    """Batch data into tuples of length n.
    Stops when a batch has fewer than n items.
    batch('ABCDEFG', 3) --> ABC DEF"""
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while len(batch := tuple(islice(it, n))) == n:
        yield batch


class TableNotFoundError(Exception):
    pass
