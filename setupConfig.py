import os
import yaml
import argparse
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("streamer_list", help="Path to the text file containing streamer names")
    parser.add_argument(
        "--savepath",
        dest="output_path",
        help="specify a filepath to save your files"
    )

    parsed_args = parser.parse_args()

    run(parsed_args.streamer_list, parsed_args.output_path)


def run(streamer_list_path, output_path):
    # Get Twitch API credentials from environment variables
    app_id = os.getenv('APP_ID')
    app_secret = os.getenv('APP_SECRET')

    # Get the app access token
    app_access_token = get_app_access_token(app_id, app_secret)

    # Headers needed for all API requests
    headers = {
        'Client-ID': app_id,
        'Authorization': f'Bearer {app_access_token}'
    }

    streamer_list = []

    # Read the streamer list from the file
    with open(streamer_list_path, 'r') as f:
        for line in f:
            streamer_list.append(line.strip())

    streamer_dict = {}

    # Get the user IDs for each streamer
    for streamer in streamer_list:
        user_params = {}

        user_params['login'] = streamer

        users_url = 'https://api.twitch.tv/helix/users'
        users_response = requests.get(users_url, headers=headers, params=user_params)
        users_data = users_response.json()
        streamer_id = users_data['data'][0]['id']
        streamer_login = users_data['data'][0]['login']
        streamer_display_name = users_data['data'][0]['display_name']

        streamer_dict[streamer_display_name] = {}
        streamer_dict[streamer_display_name]['id'] = streamer_id
        streamer_dict[streamer_display_name]['login'] = streamer_login
    
    # Get the emotes for each streamer
    for streamer_display_name in streamer_dict:
        print(streamer_display_name)
        print(streamer_dict[streamer_display_name])

        emote_params = {
            'broadcaster_id': streamer_dict[streamer_display_name]['id']
        }

        emotes_url = 'https://api.twitch.tv/helix/chat/emotes'
        emotes_response = requests.get(emotes_url, headers=headers, params=emote_params)
        emotes_data = emotes_response.json()
        emotes = []

        for emote in emotes_data['data']:
            emote_dict = {}
            emote_dict['id'] = emote['id']
            emote_dict['name'] = emote['name']
            emote_dict['image'] = emote['images']['url_4x']
            emote_dict['tier'] = emote['tier']
            emotes.append(emote_dict)
        
        # Add the emote dictionary to the streamer dictionary
        streamer_dict[streamer_display_name]['emotes'] = emotes

        # Generate file creation date
        present_day = date.today()
        present_day = present_day.strftime('%Y%m%d')
        # Generate config file containing streamer with list of emotes
        yaml_filename = f"streamer_config_{present_day}.yaml"
        yaml_output = os.path.join(output_path, yaml_filename)
        with open(yaml_output, "w") as file:
            yaml.dump(streamer_dict, file)
        print(f"Config file created: {yaml_output}")


def get_app_access_token(app_id, app_secret):
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': app_id,
        'client_secret': app_secret,
        'grant_type': 'client_credentials'
    }
    auth_response = requests.post(url, params=params)
    auth_response.raise_for_status()
    return auth_response.json()['access_token']


if __name__ == "__main__":
    main()