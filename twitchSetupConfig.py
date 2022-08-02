
import os
from twitchAPI.twitch import Twitch
from twitchAPI.twitch import AuthScope
import yaml
import argparse
from datetime import date
from dotenv import load_dotenv

"""
Twitch Report
Last Updated: July 27, 2022

This script generates a yaml config containing a list of streamers with emotes

Run through command prompt/terminal

Input:
Windows
py -3 twitchReport.py (Input text file) --savepath (Save Path) 

Mac
python3 twitchReport.py (Input text file) --savepath (Save Path) 
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_txt_file")
    parser.add_argument(
        "--savepath",
        dest="output_path",
        help="specify a filepath to save your files"
    )

    parsed_args = parser.parse_args()

    run(
        parsed_args.input_txt_file,
        parsed_args.output_path
    )


def run(input_txt_file, output_path):

    # Authentication requires .env file
    configure()
    twitch_app_key = os.getenv('twitch_auth_key')
    twitch_app_secret = os.getenv('twitch_auth_secret')

    twitch = Twitch(
        twitch_app_key,
        twitch_app_secret,
        target_app_auth_scope=[AuthScope.USER_EDIT]
    )

    # Generate twitch_streamer list from text file
    with open(input_txt_file, "r") as file:
        twitch_streamers = [streamer.strip() for streamer in file]
        twitch_streamers.sort()
        print(twitch_streamers)

    twitch_streamers_emote_list = []
    streamer_id = []
    streamer_dict = dict()

    # Obtain streamer logins
    broadcaster_id_dict = twitch.get_users(logins=twitch_streamers)

    # Obtain streamer broadcast ID
    streamer_info(twitch_streamers, broadcaster_id_dict, streamer_id)

    # Using broadcast ID, obtain streamer emotes
    obtain_streamer_emotes(streamer_id, twitch_streamers_emote_list, twitch)

    # Create dict -- "Streamer": "emote_1", "emote_2", "emote_3"
    setup_streamer_dict(streamer_dict, twitch_streamers, twitch_streamers_emote_list)

    for streamer_name in streamer_dict:
        print(streamer_name)
        print(streamer_dict[streamer_name])

    print(f"...\n{streamer_dict}")

    # Generate file creation date
    present_day = date.today()
    present_day = present_day.strftime('%Y%m%d')
    # Generate config file containing streamer w/ list of emotes
    yaml_filename = f"streamer_config_{present_day}.yaml"
    yaml_output = os.path.join(output_path, yaml_filename)
    with open(yaml_output, "w") as file:
        yaml.dump(streamer_dict, file)
    print(yaml.dump(streamer_dict))


def configure():
    load_dotenv()


def streamer_info(streamer_list, broadcaster_info_dict, broadcast_id_list):
    for streamer in range(len(streamer_list)):
        new_id = broadcaster_info_dict['data'][streamer]['id']
        broadcast_id_list.append(new_id)
    return broadcast_id_list


def obtain_streamer_emotes(broadcast_id_list, streamer_emote_list, twitch_auth):
    for single_id in broadcast_id_list:
        emote_dict = twitch_auth.get_channel_emotes(broadcaster_id=single_id)
        broadcaster_emote_list = []
        for data_position in range(len(emote_dict['data'])):
            for index in emote_dict['data']:
                for key in index.keys():
                    if key == 'name':
                        streamer_emote = emote_dict['data'][data_position]['name']
                        if streamer_emote not in broadcaster_emote_list:
                            broadcaster_emote_list.append(streamer_emote)
        streamer_emote_list.append(broadcaster_emote_list)
    return streamer_emote_list


def setup_streamer_dict(dict_of_streamer_data, streamer_list, emote_list):
    for index, streamer in enumerate(streamer_list):
        dict_of_streamer_data[streamer] = emote_list[index]
        print(index, streamer)
        print(dict_of_streamer_data)
    return dict_of_streamer_data, streamer_list, emote_list


if __name__ == "__main__":
    main()
