import json
import openpyxl

MATCHING_STRING = "Please insert translation of each word under each corresponding cell. If the particular word does not translate into the chosen language, please leave it blank"
HEADER1 = "High-risk key words"
HEADER2 = "Range of possible misspellings and common slang used by the population"
# Replace the filename equal to the new file name needed to process.
#FILENAME = "finalHigh-risk Keywords- Safeguarding_20210608JML.xlsx"
#FILENAME = "./keywords/keywords_excel/safeguarding_template_drug.xlsx"
FILENAME = "./keywords/keywords_excel/safeguarding_template_srh.xlsx"

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

book = openpyxl.load_workbook(FILENAME)
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
		lang1 = "English" #row1[0].value  # 
		lang2 = "Translation" #row2[0].value  # 


		high_risk_entries_lang1, high_risk_entries_lang2 = read_entries_from_range(1, misspelling_x, row1, row2)
		misspelling_entries_lang1, misspelling_entries_lang2 = read_entries_from_range(misspelling_x, len(row1), row1, row2)

		# This version keeps rows which don't have any entries
		# lang1_entry = {
		# 	HEADER1: high_risk_entries_lang1,
		# 	HEADER2: misspelling_entries_lang1,
		# }
		# lang2_entry = {
		# 	HEADER1: high_risk_entries_lang2,
		# 	HEADER2: misspelling_entries_lang2,
		# }

		# joint_entry = {
		# 	lang1 : lang1_entry,
		# 	lang2 : lang2_entry,
		# }

		# if high_risk_entries_lang1 or high_risk_entries_lang2 or misspelling_entries_lang1 or misspelling_entries_lang2:
		# 	# only store the entry if at least one of the lists is non-empty
		# 	table_content.append(joint_entry)


		# This version removes rows which don't have any entries
		
		joint_entry = dict()
		if high_risk_entries_lang1 or misspelling_entries_lang1:
			lang1_entry = {
				"keywords": high_risk_entries_lang1,
				"mispellings": misspelling_entries_lang1,
			}
			joint_entry[lang1] = lang1_entry
			joint_entry[lang2] = {
				"keywords": [],
				"mispellings": [],
			}

		# Copying the code from above like here is not good style.
		# TODO: write a function to do this.
		if high_risk_entries_lang2 or misspelling_entries_lang2:
			lang2_entry = {
				"keywords": high_risk_entries_lang2,
				"mispellings": misspelling_entries_lang2,
			}
			joint_entry[lang2] = lang2_entry

			

		if joint_entry:
			# only store the entry if at least one of the lists is non-empty
			table_content.append(joint_entry)


	all_tables[sheet.title] = table_content

#Always change the output name when processing new xlsx file to avoid overwritting.
#with open("./keywords/keywords_json/safeguarding_template_drug_2.json", "w") as outfile:
with open("./keywords/keywords_json/safeguarding_template_srh.json", "w") as outfile:
	json.dump(all_tables, outfile, indent=4)

