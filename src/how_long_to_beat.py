#!/usr/bin/env python3
import sys
import requests

BASE_URL = 'https://howlongtobeat.com/'
ID_URL = BASE_URL + 'game?id='
SEARCH_URL = BASE_URL + 'api/search'

def main():
    CMD_SEARCH = 'SEARCH'
    CMD_ID = 'ID'
    CMD_QUIT = 'QUIT'

    # TODO: Add support for Steam library & CSV commands
    cmd_list = [
        CMD_SEARCH,
        CMD_ID,
        CMD_QUIT,
    ]

    input_str = 'Please enter your desired command/number:\n'

    for i, cmd in enumerate(cmd_list, start=1):
        input_str += '{index}: {command}\n'.format(index=i, command=cmd.capitalize())

    user_cmd = input(input_str).strip().upper()

    # Perform user's
    if user_cmd == CMD_SEARCH or user_cmd == str(cmd_list.index(CMD_SEARCH) + 1):
        search_name()
    elif user_cmd == CMD_ID or user_cmd == str(cmd_list.index(CMD_ID) + 1):
        get_by_id()
    elif user_cmd == CMD_QUIT or user_cmd == str(cmd_list.index(CMD_QUIT) + 1):
        user_quit()
    else:
        print("Sorry, I don't recognise that command.")

def search_name():
    search_str = input('Enter game name, ID or search phrase...\n').strip()
    print('You searched for: ' + search_str)

    # TODO: Make request to correct URL and add required arguments
    response = requests.get(BASE_URL)
    try:
        response.raise_for_status()
        # TODO: Use response.json
        print(response.text)
    except:
        print('An error occured making your request. Please try again.\n')
        print('Status code: ' + response.status_code)

def get_by_id():
    # TODO: Finish implementation
    print("TODO")

def user_quit():
    sys.exit()

if __name__ == "__main__":
    main()