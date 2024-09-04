# Battleship Server

This repository contains a server for a single-player Battleship game, where the goal is to sink all ships on a board with the fewest shots possible. The game is designed to allow developers to create automated players that optimize their strategies to find and sink the ships.

## Game Description

In this game, the player takes shots at a hidden board, where the server returns one of the following results for each shot:

- **0 (Miss):** The shot did not hit any ship.
- **1 (Hit):** The shot hit a ship but did not sink it.
- **2 (Hit and sunk):** The shot hit and sunk a complete ship.

### Board Characteristics

- **Dynamic size:** The board size is configurable, allowing different levels of difficulty.
- **Ships of any shape:** Ships can take any shape, as long as all cells of a ship are connected through an edge with another cell of the same ship.
- **Ship positioning:** Ships cannot share edges with other ships but can share corners.

## Objective

The goal is to allow developers to create bots that take shots and defeat all the ships on the board with the least number of attempts. Bots should consider the distribution and shape of the ships to optimize their attack strategies.

## API

The server exposes a JSON-based API that allows interaction with the game. The following are the main endpoints:

### GET `/api/games/`

This endpoint returns a list of active games. Each game includes the following information:

- **id:** The game identifier.
- **start:** The start time of the game.
- **end:** The end time of the game.
- **board_rows:** Number of rows in the board.
- **board_cols:** Number of columns in the board.
- **ships:** A string representing the structure of the ships. Ships are described as a string where each ship is separated by a comma. Each ship is enclosed by its circumscribing rectangle, using `X` for ship parts and `-` for water, with rows separated by `|`.  
  Example:  
  - `XXX` is a ship of 3 cells in a line.  
  - `X-|XX` is a ship with one cell in the first row and two cells in the second row.  
  The ships can be rotated in any of the 4 possible directions on the board.

### POST `/api/play/`

This endpoint sends a shot to the game.

- **Request Body:**
  ```json
  {
    "game": "game_id",
    "key": "player_key",
    "shot_row": 3,
    "shot_col": 5
  }
  ```

- **Response:**
  ```json
  {
    "result": 1  // 0: Miss, 1: Hit, 2: Hit and sunk
  }
  ```

### POST `/api/reset/`

This endpoint resets a player's shots for a given game.

- **Request Body:**
  ```json
  {
    "game": "game_id",
    "key": "player_key"
  }
  ```

- **Description:** Removes all the player's shots for the specified game. Some games may be created without the reset feature enabled.

## Administration

The server includes an administration panel powered by Django’s standard admin interface with additional features:

- **Create a game:** You can set the board size and the ships, which are then randomly positioned according to the game rules.
- **Create tournaments:** Manage multiple games and provide a view that tracks total attempts per player across the games in a tournament.

## Developing Automated Players

The server is designed to allow automated players to connect and shoot automatically on the board. Bots are expected to use intelligent strategies to minimize the number of shots required to sink all the ships.

## License

This project is licensed under the MIT License.
