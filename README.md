# Steam Backlog


## Description
A command-line interface tool to determine the estimated time required to work through a backlog of video games.

Uses data from:
- [How Long to Beat](https://howlongtobeat.com/) // An excellent website that provides user aggregated data to determine how long it takes to beat a video game.
- [Steam](https://store.steampowered.com/) // An incredibly popular PC gaming platform for purchasing and playing games.

## Features
- Bulk estimation of video game playtime through user's Steam library.
  - See how long it will take to work through all those games you bought on sale, but never played!
- Review estimates for video games by name or by ID.
  - Don't need *all* that data? Just see how long it'll take you to play that one game you've been eyeing up!
- Lightweight command-line interface, perfect for working with data.
- Ability to get estimates for different types of completion states.
  - Tailor to your own playstyle. Speedrunner or achievement hunter.
- See data for the game you've most recently played, so you'll know how long it'll take to finish up.

## Project Status
Completed - **v1.0.0**

- Scope changed slightly throughout development of the project, but the most important features have been - implemented.
- In the future I would like to revisit to improve the internals, more specifically:
  - Creating a cached version of the Steam library/backlog data to reduce requests made.
  - Improving the way flags are implemented to be more extensible/maintainable.

## License
[MIT](LICENSE)