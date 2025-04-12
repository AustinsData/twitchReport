
import argparse
import os
import re
import openpyxl
import pandas as pd
from datetime import date
import yaml
import random

"""
Twitch Report
Last Updated: August 1, 2022

This script generates a new file containing an analysis from Twitch Chat CSVs

Run through command prompt/terminal

Input:
Windows
py twitchReport.py (Streamer Title) (Input folder) (Generated File Name) (Config Path) (Excel Template Path) --savepath (Save Path) 

Mac
python3 twitchReport.py (Streamer Title) (Input folder) (Generated File Name) (Config Path) (Excel Template Path) --savepath (Save Path)  
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("streamer_title")
    parser.add_argument("input_folder")
    parser.add_argument("output_file")
    parser.add_argument("config_file_path")
    parser.add_argument("excel_template")
    parser.add_argument(
        "--savepath",
        dest="output_path",
        help="specify a filepath to save your files"
    )

    parsed_args = parser.parse_args()

    run(
        parsed_args.streamer_title,
        parsed_args.input_folder,
        parsed_args.output_file,
        parsed_args.config_file_path,
        parsed_args.excel_template,
        parsed_args.output_path
    )


def run(streamer_title, input_folder_path, output_file, config_file_path, excel_template, output_path):

    # Load config
    config_data = yaml_loader(config_file_path)

    # Load emote list
    streamer_emote_list = []
    
    for streamer, data in config_data.items():
        if streamer == streamer_title:
            for emote in data['emotes']:
                streamer_emote_list.append(emote['name'])
    print(streamer_emote_list)

    # Read CSVs
    df_list = []
    # Convert CSVs into temporary dataframes
    for file in os.listdir(input_folder_path):
        if file.endswith(".csv"):
            csv_location = f"{input_folder_path}\\{file}"
            temp_df = pd.read_csv(csv_location)
            # Add to list of dfs
            df_list.append(temp_df)

    # Generate base_df
    # Concat temp_dfs into base_df
    base_df = pd.concat(df_list)

    # Generate User list
    user_series = base_df.iloc[:, 2]
    user_list = user_series.tolist()
    user_freq = {}
    for user in user_list:
        if user not in user_freq:
            user_freq[user] = 0
        user_freq[user] += 1
    ordered_dict = dict(sorted(user_freq.items(), key=lambda item: item[1], reverse=True))
    unique_users = list(ordered_dict.keys())
    unique_user_chat_count = list(ordered_dict.values())

    # Calculate gifted subs
    gifted_count = []
    gifter_list = []
    gifted_sub_dict = {}
    gifted_sub_df = base_df[base_df['Utterance'].str.contains("community! They've gifted a total of")]
    for utterance in gifted_sub_df['Utterance']:
        num_pattern = r"(\d+) in"
        gifted_num = re.findall(num_pattern, utterance)
        gifted_num = int(gifted_num[0])
        gifted_count.append(gifted_num)

        user_pattern = r"^(\w+) is gifting"
        gifter = re.findall(user_pattern, utterance)
        gifter = gifter[0]
        gifter_list.append(gifter)
    print(gifter_list)
    print(gifted_count)

    for key, value in zip(gifter_list, gifted_count):
        gifted_sub_dict[key] = value

    ordered_gifted_sub_dict = dict(sorted(gifted_sub_dict.items(), key=lambda item: item[1], reverse=True))
    print(ordered_gifted_sub_dict)

    ordered_gifter_list = list(ordered_gifted_sub_dict.keys())
    print(ordered_gifter_list)

    ordered_gifted_count = list(ordered_gifted_sub_dict.values())
    print(ordered_gifted_count)

    # Create Sample from each CSV file
    print("Creating Sample...")
    temp_base_df_list = []
    for df in df_list:
        temp_base_df = [df.iloc[index * 100:index * 100 + 100] for index in sorted(random.sample(range(0, 100), 2))].copy()
        temp_base_df = pd.concat(temp_base_df)
        temp_base_df_list.append(temp_base_df)
    reduced_base_df = pd.concat(temp_base_df_list)
    print(f"Reduced base_df: \n{reduced_base_df}")

    # Generate Series from reduced_base_df
    date_sample_series = reduced_base_df['Date']
    time_sample_series = reduced_base_df['Time (UTC)']
    user_sample_series = reduced_base_df['User']
    utt_sample_series = reduced_base_df['Utterance']

    # Sampled Series to list
    date_sample = date_sample_series.tolist()
    time_sample = time_sample_series.tolist()
    user_sample = user_sample_series.tolist()
    utt_sample = utt_sample_series.tolist()
    print("Finished sample creation...")

    # Emote Count DataFrame
    print(f"Starting emote count creation...")
    emote_col = streamer_emote_list
    emote_df = pd.DataFrame()
    utterance_series_primary = base_df['Utterance']
    emote_df['Utterance'] = utterance_series_primary

    # Create emote headers & count emotes in utterances
    emote_totals = []
    emote_count_df = pd.DataFrame()
    for col in emote_col:
        emote_df[col] = emote_df['Utterance'].apply(metric_counter, pattern=col)
        # Totaling emotes
        temp_summation = []
        new_col = f"Total {col}"
        total_count = emote_df[col].sum()
        temp_summation.append(total_count)
        emote_totals.append(total_count)
        new_series = pd.Series(temp_summation)
        emote_count_df[new_col] = new_series
    print("Finished emote count creation...")

    # Summary DataFrame
    print(f"Starting summary creation...")
    summary_col = [
        'Emote',
        'Emote Count',
        'E-Percentage',
        'User',
        'User Count',
        'User Percentage',
        'Gifter',
        'Gift Count',
        'Gift Percentage'
    ]

    summary_df = pd.DataFrame(columns=[summary_col])

    # Load Emote column
    summary_sh_emote_names = pd.Series(streamer_emote_list)
    summary_df['Emote'] = summary_sh_emote_names

    # Load Emote Count column
    summary_sh_emote_count = pd.Series(emote_totals)
    summary_df['Emote Count'] = summary_sh_emote_count
    print("Finished summary creation...")

    # Excel Sheets by order of appearance
    summary_sheet_name = "Summary"
    emote_count_sheet_name = "Emote Totals"
    sample_data_sheet_name = "Sample"

    # Load Excel sheet template
    primary_wb = openpyxl.load_workbook(excel_template)
    summary_sh = primary_wb[summary_sheet_name]
    count_sh = primary_wb[emote_count_sheet_name]
    sample_sh = primary_wb[sample_data_sheet_name]

    # Populate Emote Count sheet
    construct_column_ignore_title(count_sh, "A", streamer_emote_list)
    construct_column_ignore_title(count_sh, "B", emote_totals)

    # Populate Summary sheet
    construct_column_ignore_title(summary_sh, "A", streamer_emote_list)
    construct_column_ignore_title(summary_sh, "B", emote_totals)
    construct_column_ignore_title(summary_sh, "D", unique_users)
    construct_column_ignore_title(summary_sh, "E", unique_user_chat_count)
    construct_column_ignore_title(summary_sh, "G", ordered_gifter_list)
    construct_column_ignore_title(summary_sh, "H", ordered_gifted_count)
    construct_percentage_column(summary_sh, "C", "B", emote_totals)
    construct_percentage_column(summary_sh, "F", "E", unique_user_chat_count)
    construct_percentage_column(summary_sh, "I", "H", ordered_gifted_count)



    # Populate Sample sheet
    construct_column_ignore_title(sample_sh, "A", date_sample)
    construct_column_ignore_title(sample_sh, "B", time_sample)
    construct_column_ignore_title(sample_sh, "C", user_sample)
    construct_column_ignore_title(sample_sh, "D", utt_sample)

    # Generate file creation date
    present_day = date.today()
    present_day = present_day.strftime('%Y%m%d')
    # Generate excel file containing analysis
    excel_output_path = os.path.join(output_path, output_file)
    excel_filename = f"{excel_output_path}_{present_day}.xlsx"
    print(f"Writing {excel_output_path} ... ")
    primary_wb.save(excel_filename)
    print(f"Saved {excel_output_path}!")

    print(f"Finished...")


def yaml_loader(filepath):
    with open(filepath, "r") as config:
        config_data = yaml.safe_load(config)
    return config_data


def yaml_dump(filepath, config_data):
    with open(filepath, "w") as config:
        yaml.dump(config_data, config)


def metric_counter(word: str, pattern: str) -> int:
    return len(re.findall(pattern, word))


def remove_metric_duplicates(metric_list):
    return list(dict.fromkeys(metric_list))


def construct_column(worksheet, column, value):
    for i in range(len(value)):
        row = i + 1
        worksheet[f"{column}{row}"] = value[i]


def construct_column_ignore_title(worksheet, column, value):
    for i in range(len(value)):
        row = i + 2
        worksheet[f"{column}{row}"] = value[i]


# Value length is calculated by providing the list of actual values
def construct_percentage_column(worksheet, column, value_column, value_length):
    for i in range(len(value_length)):
        row = i + 2
        percentage_formulae = f"=ROUND(({value_column}{row}/(SUM({value_column}2:{value_column}{len(value_length)})) * 100), 2)"
        worksheet[f"{column}{row}"] = percentage_formulae


if __name__ == "__main__":
    main()
