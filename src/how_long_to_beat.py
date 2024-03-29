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
STEAM_REC_URL = STEAM_BASE_URL + 'IPlayerService/GetRecentlyPlayedGames/v0001/'

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

    # Define allowed command terms and optional flags
    CMD_BACKLOG = ['STEAM', 'BACKLOG', 'LIBRARY', 'LIB', 'GAMES']
    FLAGS_BACKLOG = ['BACKLOG']
    CMD_RECENT = ['RECENT', 'PAST', 'LATEST', 'LAST']
    FLAGS_RECENT = []
    CMD_SEARCH = ['SEARCH', 'TERM', 'NAME']
    FLAGS_SEARCH = []
    CMD_ID = ['ID', 'DETAIL']
    FLAGS_ID = ['STEAM']
    CMD_QUIT = ['QUIT', 'Q']
    FLAGS_QUIT = []

    # Create command data structure
    CMD_KEY = 'CMD'
    FLAGS_KEY = 'FLAGS'

    cmd_list = [
        {
            CMD_KEY: CMD_BACKLOG[0],
            FLAGS_KEY: FLAGS_BACKLOG,
        },
        {
            CMD_KEY: CMD_RECENT[0],
            FLAGS_KEY: FLAGS_RECENT,
        },
        {
            CMD_KEY: CMD_SEARCH[0],
            FLAGS_KEY: FLAGS_SEARCH,
        },
        {
            CMD_KEY: CMD_ID[0],
            FLAGS_KEY: FLAGS_ID,
        },
        {
            CMD_KEY: CMD_QUIT[0],
            FLAGS_KEY: FLAGS_QUIT,
        },
    ]

    # Output list of possible commands/IDs
    input_str = 'Please enter your desired command/number:'

    for i, cmd in enumerate(cmd_list, start=1):
        input_str += '\n{index}: {command} {flags}'.format(
            index = i,
            command = cmd[CMD_KEY].capitalize(),
            flags = format_cmd_flags(cmd[FLAGS_KEY]),
        )

    # Parse user input for command and flags
    user_input = input(colourise(input_str)).strip().upper().split(' --')
    user_cmd = user_input[0].strip()
    user_flags = user_input[1:]

    # Perform user's desired command
    if user_cmd in CMD_BACKLOG or user_cmd == find_cmd_index(cmd_list, CMD_KEY, CMD_BACKLOG[0]):
        if not user_flags:
            steam_library()

        # TODO: Look into better approach than hardcoding flag strings
        is_backlog = False
        if 'BACKLOG' in user_flags:
            is_backlog = True

        steam_library(is_backlog)
    elif user_cmd in CMD_RECENT or user_cmd == find_cmd_index(cmd_list, CMD_KEY, CMD_RECENT[0]):
        steam_recently_played()
    elif user_cmd in CMD_SEARCH or user_cmd == find_cmd_index(cmd_list, CMD_KEY, CMD_SEARCH[0]):
        search_name()
    elif user_cmd in CMD_ID or user_cmd == find_cmd_index(cmd_list, CMD_KEY, CMD_ID[0]):
        if not user_flags:
            get_by_id()

        is_steam_id = False
        if 'STEAM' in user_flags:
            is_steam_id = True

        get_by_id(is_steam_id)
    elif user_cmd in CMD_QUIT or user_cmd == find_cmd_index(cmd_list, CMD_KEY, CMD_QUIT[0]):
        user_quit()
    else:
        print(colourise('Sorry, I don\'t recognise that command.'))
        main()

# Prefix string with ANSI colour code and suffix with reset code
def colourise(string: str) -> str:
    return colour_prefix + string + COLOUR_SUFFIX + '\n'

# Format list of flags to output string
def format_cmd_flags(flags: list) -> str:
    if not flags:
        return ''

    output = '['

    for flag in flags:
        output += ' --{flag} '.format(flag = flag.lower())

    output += ']'

    return output

# Get index of dictionary containing relevant command data
def find_cmd_index(cmd_list: list, cmd_key: str, cmd_val: str) -> str:
    # For each dictionary in list
    for i, cmd_dict in enumerate(cmd_list):
        # Return string version of index if matches value
        if cmd_dict[cmd_key] == cmd_val:
            return str(i + 1)

    return str(-1)

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

# Format minutes to hours to nearest .1
def format_dec_hours(minutes: int) -> float:
    hours = minutes / 60

    return round(hours, 1)

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

# Append 'hours' text to end if input is float
def append_hours(prefix: float|str) -> str:
    if type(prefix) == str:
        return prefix

    return '{pre} hours'.format(pre = prefix)

# Reusable function to print game data
def get_printable_game_data(
    story_duration: float|str,
    sides_duration: float|str,
    compl_duration: float|str,
    style_duration: float|str,
    game_prefix: str = '',
    game_name: str = '',
    game_suffix: str = '',
):
    output = '''{prefix}{name}: {suffix}
        Main Story - {story}
        Main + Sides - {sides}
        Completionist - {compl}
        All Styles - {style}
    '''.format(
        prefix = game_prefix,
        name = game_name,
        suffix = game_suffix,
        story = append_hours(story_duration),
        sides = append_hours(sides_duration),
        compl = append_hours(compl_duration),
        style = append_hours(style_duration),
    )

    return output

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

# Get Steam API key/user ID from memory or user
def get_steam_details():
    global steam_api_key
    if not steam_api_key:
        steam_api_key = input(colourise('Please enter your Steam API key...'))

    global steam_user_id
    if not steam_user_id:
        steam_user_id = input(colourise('Please enter your Steam account ID...'))

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
def steam_library(is_backlog: bool =  False):
    global colour_prefix
    colour_prefix = colours.CYAN

    global steam_api_key
    global steam_user_id
    get_steam_details()

    # Create request to API endpoint for all user's games
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

        # TODO: Consider creating a cached version of the necessary data in an object for future use
        if not data:
            print(colourise('No data returned from Steam. Please check the visibility of your user profile.'))
            steam_api_key = ''
            steam_user_id = ''
            main()

        total_games = str(data['game_count'])

        if not total_games:
            print(colourise('You have no games in your library... :('))

        print(colourise('Your have {num} games in your library!'.format(num = total_games)))

        games_list = data['games']
        total_unplayed_games = 0
        total_playtime = 0
        story_dur_total = 0
        sides_dur_total = 0
        compl_dur_total = 0
        style_dur_total = 0
        error_count = 0
        app_count = 0

        for game in games_list:
            game_id = game['appid']
            game_playtime = game['playtime_forever']

            # Only interested in games with no playtime in backlog mode
            if is_backlog and game_playtime:
                continue

            game_name = app_id_lookup(game_id)

            # Error getting game name from Steam lookup
            if game_name == ERR_STEAM_GAME_REMOVED:
                error_count += 1
                continue

            # Game is a different type of application (e.g. art program like Aesprite or Blender)
            if game_name == ERR_STEAM_TYPE_APP:
                app_count += 1
                continue

            total_playtime += game_playtime

            # Keep track of games with 0 time played
            if not game_playtime:
                total_unplayed_games += 1

            # Get completion data from HLTB API using compatible name
            name_searchable = strip_trailing_edition(game_name)
            name_searchable = strip_apostrophes(name_searchable)
            search_data = api_search(name_searchable)

            if search_data == ERR_HLTB_NO_DATA:
                error_count += 1
                continue

            # Output individual game data
            story_duration = format_half_hours(search_data['comp_main'])
            sides_duration = format_half_hours(search_data['comp_plus'])
            compl_duration = format_half_hours(search_data['comp_100'])
            style_duration = format_half_hours(search_data['comp_all'])

            if type(story_duration) == float:
                story_dur_total += story_duration
            if type(sides_duration) == float:
                sides_dur_total += sides_duration
            if type(compl_duration) == float:
                compl_dur_total += compl_duration
            if type(style_duration) == float:
                style_dur_total += style_duration

            output = get_printable_game_data(
                game_name = game_name,
                game_suffix = '(Currently played {0})'.format(append_hours(format_dec_hours(game_playtime))),
                story_duration = story_duration,
                sides_duration = sides_duration,
                compl_duration = compl_duration,
                style_duration = style_duration,
            )

            print(colourise(output))

        # Output aggregated library data

        total_output = get_printable_game_data(
            game_prefix = 'Total time to get through Steam library backlog',
            story_duration = story_dur_total,
            sides_duration = sides_dur_total,
            compl_duration = compl_dur_total,
            style_duration = style_dur_total,
        )

        print(colourise(total_output))

        print(
            colourise(
                '''You have played these games on Steam for a total of {hours}!
                But {unplayed} of these games you have never played before!'''.format(
                    hours = append_hours(format_dec_hours(total_playtime)),
                    unplayed = total_unplayed_games,
                )
            )
        )

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

    main()

# Output remaining time left on most recently played Steam game
def steam_recently_played():
    global colour_prefix
    colour_prefix = colours.GREY

    global steam_api_key
    global steam_user_id
    get_steam_details()

    # Create request to API endpoint for most recently played game
    recent_url = '{base}?key={key}&steamid={id}&count=1'.format(
        base = STEAM_REC_URL,
        key = steam_api_key,
        id = steam_user_id,
    )

    recent_headers = get_http_headers(True)

    response = requests.get(
        url = recent_url,
        headers = recent_headers,
    )

    try:
        # Parse request response
        response.raise_for_status()
        data = json.loads(response.text)['response']

        if not data:
            print(colourise('No data returned from Steam. Please check the visibility of your user profile.'))
            steam_api_key = ''
            steam_user_id = ''
            main()

        if not data['total_count']:
            print(colourise('You have not played any games within the last 2 weeks... :('))
            main()

        game_data = data['games'][0]
        game_name = game_data['name']
        total_playtime = game_data['playtime_forever']
        recent_playtime = game_data['playtime_2weeks']

        # Get completion data from HLTB API using compatible name
        name_searchable = strip_trailing_edition(game_name)
        name_searchable = strip_apostrophes(name_searchable)
        search_data = api_search(name_searchable)

        if search_data == ERR_HLTB_NO_DATA:
            print(colourise('No HLTB data was found for this game.'))
            main()

        # Prepare HLTB completion data for output
        story_duration = format_half_hours(search_data['comp_main'])
        sides_duration = format_half_hours(search_data['comp_plus'])
        compl_duration = format_half_hours(search_data['comp_100'])
        style_duration = format_half_hours(search_data['comp_all'])

        output = get_printable_game_data(
            game_prefix = 'You most recently played - ',
            game_name = game_name,
            story_duration = story_duration,
            sides_duration = sides_duration,
            compl_duration = compl_duration,
            style_duration = style_duration,
        )

        print(colourise(output))

        print(
            colourise(
                'You have played {total} in total ({recent} in the past 2 weeks).'.format(
                    total = append_hours(format_dec_hours(total_playtime)),
                    recent = append_hours(format_dec_hours(recent_playtime)),
                )
            )
        )
    except HTTPError as e:
        handle_http_error(e)

    main()

# Output game completion data from search term
def search_name(game_name: str = ''):
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

    output = get_printable_game_data(
        game_prefix = 'Most relevant result for ',
        game_name = game_name,
        story_duration = story_duration,
        sides_duration = sides_duration,
        compl_duration = compl_duration,
        style_duration = style_duration,
    )

    print(colourise(output))

    main()

# Output game completion data from identifier
def get_by_id(is_steam_id: bool = False):
    global colour_prefix
    colour_prefix = colours.MAGENTA

    id_type = 'Steam' if is_steam_id else 'HLTB'
    game_id = input(colourise('Enter {service} game ID...').format(service = id_type)).strip()

    if not game_id.isdigit():
        print(colourise('Invalid ID. Must be an integer.'))
        get_by_id(is_steam_id)

    # Different lookup service required, HLTB does not natively support Steam app IDs
    if is_steam_id:
        game_name = app_id_lookup(game_id)

        if game_name == ERR_STEAM_GAME_REMOVED or game_name == ERR_STEAM_TYPE_APP:
            print(
                colourise(
                    'Unable to find data for this Steam ID, please ensure it is valid/still present on the Steam storefront.'
                )
            )
            get_by_id(is_steam_id)

        name_searchable = strip_trailing_edition(game_name)
        name_searchable = strip_apostrophes(name_searchable)
        data = api_search(name_searchable)

        if data == ERR_HLTB_NO_DATA:
            print(colourise('Unable to find HLTB data for this Steam ID, please ensure it is valid.'))
            get_by_id(is_steam_id)

        # Output HLTB data from search API response
        story_duration = format_half_hours(data['comp_main'])
        sides_duration = format_half_hours(data['comp_plus'])
        compl_duration = format_half_hours(data['comp_100'])
        style_duration = format_half_hours(data['comp_all'])

        output = get_printable_game_data(
            game_prefix = 'Game completion times for ',
            game_name = game_name,
            story_duration = story_duration,
            sides_duration = sides_duration,
            compl_duration = compl_duration,
            style_duration = style_duration,
        )

        print(colourise(output))

        # Early return to main function
        main()

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