#!/usr/bin/env python3
import sys
import json
from types import SimpleNamespace
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

# Global HLTB URL constants
HLTB_BASE_URL = 'https://howlongtobeat.com/'
HLTB_ID_URL = HLTB_BASE_URL + 'game/'
HLTB_SEARCH_URL = HLTB_BASE_URL + 'api/search'

# Global Steam URL constants
STEAM_BASE_URL = 'https://api.steampowered.com/'
STEAM_LIB_URL = STEAM_BASE_URL + 'IPlayerService/GetOwnedGames/v0001/'

STEAM_STORE_BASE_URL = 'https://store.steampowered.com/'
STEAM_APP_LOOKUP_URL = STEAM_STORE_BASE_URL + 'api/appdetails'

# Global custom error constants
ERR_HLTB_NO_DATA = 'ERR_HLTB_NO_DATA'
ERR_STEAM_GAME_REMOVED = 'ERR_STEAM_GAME_REMOVED'
ERR_STEAM_TYPE_APP = 'ERR_STEAM_TYPE_APP'

# Global Steam data variables
global steam_api_key
steam_api_key = ''
global steam_user_id
steam_user_id = ''

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

    # Define allowed command terms
    CMD_BACKLOG = ['STEAM', 'BACKLOG', 'LIBRARY', 'LIB', 'GAMES']
    CMD_SEARCH = ['SEARCH', 'TERM', 'NAME']
    CMD_ID = ['ID', 'DETAIL']
    CMD_QUIT = ['QUIT', 'Q']

    # TODO: Add support for Steam library & CSV commands
    cmd_list = [
        CMD_BACKLOG[0],
        CMD_SEARCH[0],
        CMD_ID[0],
        CMD_QUIT[0],
    ]

    # Output list of possible commands/IDs
    input_str = 'Please enter your desired command/number:'

    for i, cmd in enumerate(cmd_list, start=1):
        input_str += '\n{index}: {command}'.format(index = i, command = cmd.capitalize())

    user_cmd = input(colourise(input_str)).strip().upper()

    # Perform user's desired command
    if user_cmd in CMD_BACKLOG or user_cmd == str(cmd_list.index(CMD_BACKLOG[0]) + 1):
        steam_library()
    elif user_cmd in CMD_SEARCH or user_cmd == str(cmd_list.index(CMD_SEARCH[0]) + 1):
        search_name()
    elif user_cmd in CMD_ID or user_cmd == str(cmd_list.index(CMD_ID[0]) + 1):
        get_by_id()
    elif user_cmd in CMD_QUIT or user_cmd == str(cmd_list.index(CMD_QUIT[0]) + 1):
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
        'origin': HLTB_BASE_URL,
        'referer': HLTB_BASE_URL,
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

# Remove trademark symbols from string, for game names from Steam
def strip_trademark_symbols(string: str) -> str:
    tm_symbols = ['\u2122', '\u00A9', '\u00AE', '\u2117']

    for symbol in tm_symbols:
        string = string.replace(symbol, '')

    return string

# Remove 'Edition' from string if final word, improves compatibility with HLTB
def strip_trailing_edition(string: str) -> str:
    words = string.split(' ')
    # 🔫🤠💠
    the_last_word = words[-1]

    if not the_last_word.upper() == 'EDITION':
        return string

    # Return string excluding last word of 'Edition'
    return string.rsplit(' ', 1)[0]

# Remove apostrophes from string, improves compatibility with HLTB
def strip_apostrophes(string: str) -> str:
    apostrophe_symbols = ['\'', '’']

    for apostrophe in apostrophe_symbols:
        string = string.replace(apostrophe, '')

    return string

# Search API for game by term and return entire game data JSON
def api_search(search_str: str) -> dict:
    search_terms = search_str.split(' ')

    # Build search JSON payload
    search_payload = {
        'searchType': 'games',
        'searchTerms': search_terms,
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

    # Set required request headers
    search_headers = get_http_headers(True)

    response = requests.post(
        url = HLTB_SEARCH_URL,
        data = json.dumps(search_payload),
        headers = search_headers,
    )

    try:
        # Parse request response
        response.raise_for_status()
        data = json.loads(response.text)['data']

        if not data:
            return ERR_HLTB_NO_DATA

        return data[0]
    except HTTPError as e:
        handle_http_error(e)

# Lookup game name from Steam app ID
def app_id_lookup(app_id: int) -> str:

    lookup_url = '{url}?appids={id}&filters=basic'.format(
        url = STEAM_APP_LOOKUP_URL,
        id = app_id,
    )
    lookup_headers = get_http_headers(True)

    response = requests.get(
        url = lookup_url,
        headers = lookup_headers,
    )

    try:
        # Parse request response
        response.raise_for_status()
        data = json.loads(response.text)

        if not data or not data[str(app_id)]['success']:
            return ERR_STEAM_GAME_REMOVED

        if not data[str(app_id)]['data']['type'] == 'game':
            return ERR_STEAM_TYPE_APP

        name = data[str(app_id)]['data']['name']
        name = strip_trademark_symbols(name)

        return name
    except HTTPError as e:
        handle_http_error(e)

# Output game completion data from Steam library
def steam_library():
    global colour_prefix
    colour_prefix = colours.CYAN

    global steam_api_key
    if not steam_api_key:
        steam_api_key = input(colourise('Please enter your Steam API key...'))

    global steam_user_id
    if not steam_user_id:
        steam_user_id = input(colourise('Please enter your Steam account ID...'))

    user_library_url = '{base}?key={key}&steamid={id}'.format(
        base = STEAM_LIB_URL,
        key = steam_api_key,
        id = steam_user_id,
    )
    library_headers = get_http_headers(True)

    response = requests.get(
        url = user_library_url,
        headers = library_headers,
    )

    try:
        # Parse request response
        response.raise_for_status()
        data = json.loads(response.text)['response']

        if not data:
            print(colourise('No data returned from Steam. Please check the visibility of your user profile.'))
            steam_api_key = ''
            steam_user_id = ''
            steam_library()

        total_games = str(data['game_count'])

        if not total_games:
            print(colourise('You have no games in your library... :('))

        print(colourise('Your have {num} games in your library!'.format(num = total_games)))

        games_list = data['games']
        story_dur_total = 0
        sides_dur_total = 0
        compl_dur_total = 0
        style_dur_total = 0
        error_count = 0
        app_count = 0

        for game in games_list:
            game_id = game['appid']
            game_name = app_id_lookup(game_id)

            # Error getting game name from Steam lookup
            if game_name == ERR_STEAM_GAME_REMOVED:
                error_count += 1
                continue

            # Game is a different type of application (e.g. art program like Aesprite or Blender)
            if game_name == ERR_STEAM_TYPE_APP:
                app_count += 1
                continue

            # Get completion data from HLTB API using compatibile name
            name_searchable = strip_trailing_edition(game_name)
            name_searchable = strip_apostrophes(name_searchable)
            data = api_search(name_searchable)

            if data == ERR_HLTB_NO_DATA:
                error_count += 1
                continue

            story_duration = format_half_hours(data['comp_main'])
            sides_duration = format_half_hours(data['comp_plus'])
            compl_duration = format_half_hours(data['comp_100'])
            style_duration = format_half_hours(data['comp_all'])

            if type(story_duration) == float:
                story_dur_total += story_duration
            if type(sides_duration) == float:
                sides_dur_total += sides_duration
            if type(compl_duration) == float:
                compl_dur_total += compl_duration
            if type(style_duration) == float:
                style_dur_total += style_duration

            output = '''{0}:
                Main Story - {1} hours
                Main + Sides - {2} hours
                Completionist - {3} hours
                All Styles - {4} hours
            '''.format(
                game_name,
                story_duration,
                sides_duration,
                compl_duration,
                style_duration,
            )

            print(colourise(output))

        # TODO: In a future iteration will add the ability to subtract current playtime, using the flags mentioned in other document
        total_output = '''Total time to get through Steam library backlog:
            Main Story - {0} hours
            Main + Sides - {1} hours
            Completionist - {2} hours
            All Styles - {3} hours
        '''.format(
            story_dur_total,
            sides_dur_total,
            compl_dur_total,
            style_dur_total,
        )
        print(colourise(total_output))

        if error_count:
            print(
                colourise(
                    '''An error occured when looking up {errors} of your games and have been ommitted from the list.
                    This is likely because it has been removed from the Steam store.
                    Or it could not be found by HowLongToBeat's search.'''.format(errors = error_count)
                )
            )

        if app_count:
            print(
                colourise(
                    '''{apps} games in your library are other types of applications and have been ommitted from the list.
                    These are likely utility, productivity or art apps like Wallpaper Engine, Aesprite or Blender.'''.format(apps = app_count)
                )
            )

    except HTTPError as e:
        handle_http_error(e)

# Output game completion data from search term
def search_name():
    global colour_prefix
    colour_prefix = colours.BLUE

    search_term = input(colourise('Enter game name or search phrase...')).strip().lower()

    data = api_search(search_term)

    if data == ERR_HLTB_NO_DATA:
        print(colourise('No matches returned for this query. Try to match the game name.'))
        search_name()

    game_name = data['game_name']
    story_duration = format_half_hours(data['comp_main'])
    sides_duration = format_half_hours(data['comp_plus'])
    compl_duration = format_half_hours(data['comp_100'])
    style_duration = format_half_hours(data['comp_all'])

    output = '''Most relevant result for {0}:
        Main Story - {1} hours
        Main + Sides - {2} hours
        Completionist - {3} hours
        All Styles - {4} hours
    '''.format(
        game_name,
        story_duration,
        sides_duration,
        compl_duration,
        style_duration,
    )

    print(colourise(output))

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
        url = '{path}{id}'.format(path = HLTB_ID_URL, id = game_id),
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

    print(colourise('Goodbye! 🤙'))
    sys.exit()

if __name__ == '__main__':
    main()