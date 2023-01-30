#!/usr/bin/env python3
import sys
from types import SimpleNamespace
import requests

BASE_URL = 'https://howlongtobeat.com/'
ID_URL = BASE_URL + 'game?id='
SEARCH_URL = BASE_URL + 'api/search'

def main():
    # SimpleNamespace required because Python match doesn't allow constants, for some reason
    cmds = SimpleNamespace()
    cmds.SEARCH = 'SEARCH'
    cmds.ID = 'ID'
    cmds.QUIT = 'QUIT'

    # TODO: Add support for Steam library & CSV commands
    cmd_list = [
        cmds.SEARCH,
        cmds.ID,
        cmds.QUIT,
    ]

    input_str = 'Please enter your desired command/number:\n'

    for i, cmd in enumerate(cmd_list, start=1):
        input_str += '{index}: {command}\n'.format(index=i, command=cmd.capitalize())

    user_cmd = input(input_str).strip().upper()

    # Perform user's
    match user_cmd:
        case cmds.SEARCH:
            search_name()
        case cmds.ID:
            get_by_id()
        case cmds.QUIT:
            user_quit()
        case _:
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