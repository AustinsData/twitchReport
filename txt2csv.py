
import os
import re
import pandas as pd
import argparse
from datetime import date

"""
Twitch Text to CSV
Last Updated: July 27, 2022

This script generates a folder of CSV files -- converting txt files to csv

Run through command prompt/terminal

Input:
Windows
py -3 txt2csv.py (Input folder) (Generated Folder Name) --savepath (Save Path) 

Mac
python3 txt2csv.py (Input folder) (Generated Folder Name) --savepath (Save Path) 
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_folder")
    parser.add_argument("output_folder")
    parser.add_argument(
        "--savepath",
        dest="output_path",
        help="specify a filepath to save your files"
    )

    parsed_args = parser.parse_args()

    run(
        parsed_args.input_folder,
        parsed_args.output_folder,
        parsed_args.output_path
    )


def run(input_folder_path, output_folder, output_path):

    for file in os.listdir(input_folder_path):
        if file.endswith(".txt"):
            file_location = f"{input_folder_path}\\{file}"
            with open(file_location, 'r', encoding='utf-8') as twitch_txt_file:

                date_stamp = []
                timestamp = []
                twitch_user = []
                utterance = []

                # Parse lines into separate values
                for line in twitch_txt_file:

                    # Col A: Date
                    date_pattern = "(\d\d\d\d-\d\d-\d\d)"
                    date_parse = re.search(date_pattern, line)
                    date_twitch = date_parse.group()
                    date_stamp.append(date_twitch)

                    # Col B: Time (UTC)
                    time_pattern = "(\d\d:\d\d:\d\d)"
                    time_parse = re.search(time_pattern, line)
                    time_twitch = time_parse.group()
                    timestamp.append(time_twitch)

                    # Col C: Twitch User
                    twitch_user_pattern = "]\s(.*):"
                    twitch_user_parse = re.search(twitch_user_pattern, line)
                    user = twitch_user_parse.group()
                    twitch_user.append(user)

                    # Col D: Utterance
                    utterance_pattern = ":\s(.*)"
                    utterance_parse = re.search(utterance_pattern, line)
                    utterance_message = utterance_parse.group()
                    utterance.append(utterance_message)

                # Generate dataframe
                twitchChat_df = pd.DataFrame()
                date_series = pd.Series(date_stamp)
                time_series = pd.Series(timestamp)
                user_series = pd.Series(twitch_user)
                utterance_series = pd.Series(utterance)
                twitchChat_df['Date'] = date_series
                twitchChat_df['Time (UTC)'] = time_series
                twitchChat_df['User'] = user_series
                twitchChat_df['Utterance'] = utterance_series

                # Apply data types
                twitchChat_df['Date'] = twitchChat_df['Date'].apply(pd.to_datetime)
                twitchChat_df['Time (UTC)'] = twitchChat_df['Time (UTC)'].apply(str)
                twitchChat_df['User'] = twitchChat_df['User'].apply(str)
                twitchChat_df['Utterance'] = twitchChat_df['Utterance'].apply(str)

                # Clean Data
                twitchChat_df['User'] = twitchChat_df['User'].apply(normalise_twitch_usernames)
                twitchChat_df['Utterance'] = twitchChat_df['Utterance'].apply(normalise_utterance)

                # Generate new folder to contain csv files
                csv_output_folder = output_folder + "CSV"
                csv_output_folder_path = os.path.join(output_path, csv_output_folder)
                os.makedirs(csv_output_folder_path, exist_ok=True)
                # Generate file creation date
                present_day = date.today()
                present_day = present_day.strftime('%Y%m%d')
                # Generate one csv file per txt file
                csv_file_name = f"{file}_{present_day}.csv"
                csv_data_output = os.path.join(csv_output_folder_path, csv_file_name)
                twitchChat_df.to_csv(csv_data_output, index=False)


def normalise_twitch_usernames(text):
    text = re.sub(r"(]\s)", "", text)
    text = re.sub(r":", "", text)
    return text


def normalise_utterance(text):
    text = re.sub(r"^:\s", "", text)
    return text


if __name__ == "__main__":
    main()