from rpft.converters import google_sheets_as_csv

def main():

    output_folder = "./test_output"

    localised_sheets = "13do_Qnc0VKC6Ao4N7YY3skUFKJMuwOixj2GyMVwnRLM"

    #Dowload all content to csv
    sheet_ids = [localised_sheets]

    google_sheets_as_csv(sheet_ids, output_folder)
    
if __name__ == '__main__':    
    main()
