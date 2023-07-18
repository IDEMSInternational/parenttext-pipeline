import json
import openpyxl


def process_keywords(sources, output):

	MATCHING_STRING = "Please insert translation of each word under each corresponding cell. If the particular word does not translate into the chosen language, please leave it blank"
	HEADER1 = "High-risk key words"
	HEADER2 = "Range of possible misspellings and common slang used by the population"

	dictionaries = {}	
	
	for source in sources:

		input_file = source["path"]
		language = source["key"]

		book = openpyxl.load_workbook(input_file)
		all_tables = dict()
		for sheet in book.worksheets:
			print("Processing sheet " + sheet.title)
			rows = list(sheet.iter_rows())
			table_found = False
			for y, row in enumerate(rows):
				# We assume that the table starts in the first column,
				# in the left-most cell in the row before it we have a
				# cell containing the matching string.
				if len(row) >= 1 and row[0].value == MATCHING_STRING:
					table_found = True
					# I simply assume that the misspellings start in column 5.
					# If that's not always the case, you can write some code
					# looking for the cell in row y-1 which contains HEADER2.
					misspelling_x = 5
					assert rows[y-1][1].value == HEADER1
					assert rows[y-1][misspelling_x].value == HEADER2
					y_start = y+1
					
					# We found the table, so stop searching.
					# Note: We assume there's only one such table per sheet.
					break
			if not table_found:
				continue

			table_content = []
			for y in range(y_start, len(rows)-1, 2):
				# Go through the rows of the table in pairs
				row1 = rows[y]
				row2 = rows[y+1]
				lang1 = "English" 
				lang2 = language 

				high_risk_entries_lang1, high_risk_entries_lang2 = read_entries_from_range(1, misspelling_x, row1, row2)
				misspelling_entries_lang1, misspelling_entries_lang2 = read_entries_from_range(misspelling_x, len(row1), row1, row2)
				
				joint_entry = dict()
				if high_risk_entries_lang1 or misspelling_entries_lang1:
					lang1_entry = {
						"keywords": high_risk_entries_lang1,
						"mispellings": misspelling_entries_lang1,
					}
					joint_entry[lang1] = lang1_entry
					joint_entry["Translation"] = {}
					joint_entry["Translation"][lang2] = {
						"keywords": [],
						"mispellings": [],
					}

				if high_risk_entries_lang2 or misspelling_entries_lang2:
					lang2_entry = {
						"keywords": high_risk_entries_lang2,
						"mispellings": misspelling_entries_lang2,
					}
					joint_entry["Translation"][lang2] = lang2_entry

				if joint_entry:
					# only store the entry if at least one of the lists is non-empty
					table_content.append(joint_entry)

			all_tables[sheet.title] = table_content

		#Always change the output name when processing new xlsx file to avoid overwritting.
		#with open("./keywords/keywords_json/safeguarding_template_drug_2.json", "w") as outfile:
		with open(output_file, "w") as outfile:
			json.dump(all_tables, outfile, indent=4)

		dictionaries[language] = all_tables

	full_dictionary = merge_dictionaries(dictionaries)

	with open(output + "safeguarding_words.json", "w") as outfile:
			json.dump(full_dictionary, outfile, indent=4)

def read_entries_from_range(xmin, xmax, row1, row2):
		entries = []
		lang1_list = []
		lang2_list = []
		for x in range(xmin, xmax):
			if row1[x].value is not None:
				lang1_list.append(str(row1[x].value).strip())
			if row2[x].value is not None:
				lang2_list.append(str(row2[x].value).strip())
		return lang1_list, lang2_list

def merge_dictionaries(dictionaries):
	merged_dict = {}
	for lang in dictionaries:
		dic = dictionaries[lang]
		if merged_dict == {}:
			merged_dict = dic
		else:
			for sheet_ref in merged_dict:
				for sheet in dic:
					if sheet == sheet_ref:
						for count, value in enumerate(merged_dict[sheet]):
							original_english = value["English"]["keywords"][0]
							try:
								ref_english = dic[sheet][count]["English"]["keywords"][0]
							except KeyError:
								ref_english = None
							if original_english == ref_english:
								additional_translation = {}
								additional_translation =  dic[sheet][count]["Translation"][lang]
								merged_dict[sheet][count]["Translation"][lang] = additional_translation
							else:
								print("There is a match problem in '" + sheet + "' sheet, please check all the spreadsheets have the same english rows in the same order")
						
						
	return merged_dict



		
