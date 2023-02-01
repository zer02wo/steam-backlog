#!/usr/bin/env python3
import sys
import json
from types import SimpleNamespace
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

# Global URL constants
BASE_URL = 'https://howlongtobeat.com/'
ID_URL = BASE_URL + 'game/'
SEARCH_URL = BASE_URL + 'api/search'

# Define simple namespace for ANSI colour prefixes
colours = SimpleNamespace()
colours.GREY = '\033[1;30m'
colours.RED = '\033[1;31m'
colours.GREEN = '\033[1;32m'
colours.YELLOW = '\033[1;33m'
colours.BLUE = '\033[1;34m'
colours.MAGENTA = '\033[1;35m'
colours.CYAN = '\033[1;36m'
colours.RESET = '\u001b[0m'

# Global colour variables
COLOUR_SUFFIX = colours.RESET
global colour_prefix

# Main command branching/user input
def main():
    global colour_prefix
    colour_prefix = colours.GREEN

    CMD_SEARCH = 'SEARCH'
    CMD_ID = 'ID'
    CMD_QUIT = 'QUIT'

    # TODO: Add support for Steam library & CSV commands
    cmd_list = [
        CMD_SEARCH,
        CMD_ID,
        CMD_QUIT,
    ]

    # Output list of possible commands/IDs
    input_str = 'Please enter your desired command/number:'

    for i, cmd in enumerate(cmd_list, start=1):
        input_str += '\n{index}: {command}'.format(index = i, command = cmd.capitalize())

    user_cmd = input(colourise(input_str)).strip().upper()

    # Perform user's desired command
    if user_cmd == CMD_SEARCH or user_cmd == str(cmd_list.index(CMD_SEARCH) + 1):
        search_name()
    elif user_cmd == CMD_ID or user_cmd == str(cmd_list.index(CMD_ID) + 1):
        get_by_id()
    elif user_cmd == CMD_QUIT or user_cmd == str(cmd_list.index(CMD_QUIT) + 1):
        user_quit()
    else:
        print(colourise('Sorry, I don\'t recognise that command.'))
        main()

# Prefix string with ANSI colour code and suffix with reset code
def colourise(string: str) -> str:
    return colour_prefix + string + COLOUR_SUFFIX + '\n'

# Provide HTTP headers to make requests
def get_http_headers(isJson: bool) -> dict:
    base_headers = {
        'origin': BASE_URL,
        'referer': BASE_URL,
        'user-agent': 'steam backlog python script',
    }

    if isJson:
        base_headers['content-type'] = 'application/json'

    return base_headers

# Handle HTTP errors and output to the console
def handle_http_error(e: HTTPError):
    global colour_prefix
    colour_prefix = colours.RED

    err_str = '''An error occured making your request. Please try again.
        Status code: {status}
        Response: {reason}
    '''.format(
        status = str(e.response.status_code),
        reason = e.response.reason
    )

    print(colourise(err_str))

# Format seconds to hours rounded to nearest .5
def format_half_hours(seconds: int) -> float | str:
    if not seconds:
        return 'No Data'

    hours = seconds / 3600

    return round(hours * 2) / 2

# Output game completion data from search term
def search_name():
    global colour_prefix
    colour_prefix = colours.BLUE

    # Build search JSON payload
    search_payload = {
        'searchType': 'games',
        'searchTerms': [],
        'searchPage': 1,
        'size': 1,
        'searchOptions': {
            'games': {
                'userId': 0,
                'platform': '',
                'sortCategory': 'popular',
                'rangeCategory': 'main',
                'rangeTime': {
                    'min': None,
                    'max': None,
                },
                'gameplay': {
                    'perspective': '',
                    'flow': '',
                    'genre': '',
                },
                'rangeYear': {
                    'min': '',
                    'max': ''
                },
                'modifier': '',
            },
            'users': {
                'sortCategory': 'postcount',
            },
            'filter': '',
            'sort': 0,
            'randomizer': 0,
        },
    }

    search_term = input(colourise('Enter game name or search phrase...')).strip().lower().split(' ')
    search_payload['searchTerms'] = search_term

    # Set required request headers
    search_headers = get_http_headers(True)

    response = requests.post(
        url = SEARCH_URL,
        data = json.dumps(search_payload),
        headers = search_headers,
    )

    try:
        # Parse request response
        response.raise_for_status()
        data = json.loads(response.text)['data']

        if not data:
            print(colourise('No matches returned for this query. Try to match the game name.'))
            search_name()

        data = data[0]

        game_name = data['game_name']
        story_duration = format_half_hours(data['comp_main'])
        sides_duration = format_half_hours(data['comp_plus'])
        compl_duration = format_half_hours(data['comp_100'])
        style_duration = format_half_hours(data['comp_all'])

        output = '''Most relevant result for {0}:
            Main Story - {1}
            Main + Sides - {2}
            Completionist - {3}
            All Styles - {4}
        '''.format(
            game_name,
            story_duration,
            sides_duration,
            compl_duration,
            style_duration
        )

        print(colourise(output))
    except HTTPError as e:
        handle_http_error(e)

    main()

# Output game completion data from identifier
def get_by_id():
    global colour_prefix
    colour_prefix = colours.MAGENTA

    # TODO: Add support for Steam ID too
    game_id = input(colourise('Enter HLTB game ID...')).strip()

    if not game_id.isdigit():
        print(colourise('Invalid ID. Must be an integer.'))
        get_by_id()

    # Set required request headers
    id_headers = get_http_headers(False)

    response = requests.get(
        url = '{path}{id}'.format(path = ID_URL, id = game_id),
        headers = id_headers,
    )

    try:
        # Parse request response
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        output = ''

        # Get game name from HTML
        game_name_selector = 'div[class^="GameHeader_profile_header"]'
        game_name = soup.select_one(game_name_selector + '>' + game_name_selector).text.strip()
        output += 'Game completion times for {0}:\n'.format(game_name)

        # Get game completion type and duration
        for time_type in soup.select('li[class^="GameStats"] > h4'):
            time_amount = time_type.find_next_sibling('h5')
            time_amount = time_amount.text.replace('\u00BD', '.5')

            if time_amount == '--':
                time_amount = 'No Data'

            output += '\t{0} - {1}\n'.format(time_type.text, time_amount)

        print(colourise(output))
    except HTTPError as e:
        handle_http_error(e)

    main()

# Quit script from user command
def user_quit():
    global colour_prefix
    colour_prefix = colours.YELLOW

    print(colourise('Goodbye! :)'))
    sys.exit()

if __name__ == '__main__':
    main()