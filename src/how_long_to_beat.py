#!/usr/bin/env python3
import sys
import json
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

BASE_URL = 'https://howlongtobeat.com/'
ID_URL = BASE_URL + 'game/'
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
        input_str += '{index}: {command}\n'.format(index = i, command = cmd.capitalize())

    user_cmd = input(input_str).strip().upper()

    # Perform user's desired command
    if user_cmd == CMD_SEARCH or user_cmd == str(cmd_list.index(CMD_SEARCH) + 1):
        search_name()
    elif user_cmd == CMD_ID or user_cmd == str(cmd_list.index(CMD_ID) + 1):
        get_by_id()
    elif user_cmd == CMD_QUIT or user_cmd == str(cmd_list.index(CMD_QUIT) + 1):
        user_quit()
    else:
        print('Sorry, I don\'t recognise that command.')

def get_http_headers(isJson: bool) -> dict:
    base_headers = {
        'origin': BASE_URL,
        'referer': BASE_URL,
        'user-agent': 'steam backlog python script',
    }

    if isJson:
        base_headers['content-type'] = 'application/json'

    return base_headers

def handle_http_error(e: HTTPError):
    print('An error occured making your request. Please try again.')
    print('\tStatus code: {status}'.format(status = str(e.response.status_code)))
    print('\tResponse: {reason}'.format(reason = e.response.reason))

def format_half_hours(seconds: int) -> float | str:
    if not seconds:
        return 'No Data'

    hours = seconds / 3600

    return round(hours * 2) / 2

def search_name():
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

    search_term = input('Enter game name or search phrase...\n').strip().lower().split(' ')
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
        data = json.loads(response.text)['data'][0]

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
        '''.format(game_name, story_duration, sides_duration, compl_duration, style_duration)
        print(output)
    except HTTPError as e:
        handle_http_error(e)

    main()

def get_by_id():
    # TODO: Add support for Steam ID too
    game_id = input('Enter HLTB game ID...\n').strip()

    if not game_id.isdigit():
        print('Invalid ID. Must be an integer.')
        return

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

        # Get game name from HTML
        game_name_selector = 'div[class^="GameHeader_profile_header"]'
        game_name = soup.select_one(game_name_selector + '>' + game_name_selector).text.strip()
        print('Game completion times for {0}:'.format(game_name))

        # Get game completion type and duration
        for time_type in soup.select('li[class^="GameStats"] > h4'):
            time_amount = time_type.find_next_sibling('h5')
            time_amount = time_amount.text.replace('\u00BD', '.5')

            if time_amount == '--':
                time_amount = 'No Data'

            print('\t{0} - {1}'.format(time_type.text, time_amount))
    except HTTPError as e:
        handle_http_error(e)

    main()

def user_quit():
    print('Goodbye! :)')
    sys.exit()

if __name__ == '__main__':
    main()