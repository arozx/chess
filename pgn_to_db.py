import argparse
import concurrent.futures
import cProfile
import os
import pstats
import sqlite3
from multiprocessing import cpu_count

import chess.pgn
import pandas as pd
from alive_progress import alive_bar

from db_connector import DBConnector
from split_file import split_file

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--database",
    help="Name of the database to be created",
    type=str,
    default="chess_games",
)

database = parser.parse_args().database

if os.name == "nt":  # check if windows
    database = os.getcwd() + f"\\{database}.db"
else:  # UNIX style path (osx, linux, etc)
    database = os.getcwd() + f"/{database}.db"

# connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(database)
print("opening database at:", database)


# create a new DBConnector instance
db = DBConnector(database)

# create the tables
db.create_games_table()
db.create_moves_table()


def count_games_in_pgn(file_path):
    with open(file_path) as pgn:
        count = 0
        for line in pgn:
            if line[0:6] == "[Event":
                count += 1
    return count


def add_game_to_db(game, file_id):
    headers = game.headers
    white = headers.get("White", "Unknown")
    black = headers.get("Black", "Unknown")
    result = headers.get("Result", "Unknown")
    white_elo = headers.get("WhiteElo", "Unknown")
    black_elo = headers.get("BlackElo", "Unknown")
    event = headers.get("Event", "Unknown")
    site = headers.get("Site", "Unknown")
    date = headers.get("Date", "Unknown")
    _round = headers.get("Round", "Unknown")
    utc_date = headers.get("UTCDate", "Unknown")
    utc_time = headers.get("UTCTime", "Unknown")
    white_rating_diff = headers.get("WhiteRatingDiff", "Unknown")
    black_rating_diff = headers.get("BlackRatingDiff", "Unknown")
    white_title = headers.get("WhiteTitle", "Unknown")
    eco = headers.get("ECO", "Unknown")
    opening = headers.get("Opening", "Unknown")
    time_control = headers.get("TimeControl", "Unknown")
    termination = headers.get("Termination", "Unknown")

    # get moves for a givern game
    try:
        moves = " ".join(str(move) for move in game.mainline_moves())
    except ValueError:
        print("Illegal move encountered. Skipping game...")
        return None

    # format data as a dictionary
    game_data = {
        "file_id": file_id,
        "white": white,
        "black": black,
        "result": result,
        "white_elo": white_elo,
        "black_elo": black_elo,
        "event": event,
        "site": site,
        "date": date,
        "round": _round,
        "utc_date": utc_date,
        "utc_time": utc_time,
        "white_rating_diff": white_rating_diff,
        "black_rating_diff": black_rating_diff,
        "white_title": white_title,
        "eco": eco,
        "opening": opening,
        "time_control": time_control,
        "termination": termination,
        "moves": moves,
    }

    return game_data


def process_game(file):
    file_id = os.path.basename(file)  # file_id is basename
    with open(file) as pgn:
        game = chess.pgn.read_game(pgn)
        if game is None:
            return None  # end of file
        return add_game_to_db(game, file_id)


def process_file(file):
    games_list = []
    max_workers = cpu_count()
    # process games in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_game = {
            executor.submit(process_game, file, game_number): game_number
            for game_number in range(100000)
        }
        # use a progress bar to track the status of the processing
        with alive_bar(len(future_to_game), title="Processing") as bar:
            for future in concurrent.futures.as_completed(future_to_game):
                game_data = future.result()
                if game_data is None:
                    break  # end of file
                games_list.append(game_data)
                if len(games_list) >= 1000:  # batch size
                    df = pd.DataFrame(games_list)
                    df.drop(
                        columns=["file_id"]
                    )  # drop the file_id column before inserting into the database
                    df.to_sql("games", conn, if_exists="append", index=False)
                    games_list = []  # clear the list
                bar()  # update bar status
    print("finished processing file:", file)
    conn.commit()


def process_files():
    for file in files:
        process_file(file)


if __name__ == "__main__":
    files = []
    # returns the number of lines in the file
    file = "./lichess/lichess_db_standard_rated_2014-09.pgn"
    print("Counting games in the file...")
    games = count_games_in_pgn(file)
    print(f"number of games, {games:,}")
    num_games = games

    # split the file into parts if it contains more than 100,000 games
    if games > 100_000:
        games = games // 100_000
        print("The file is too large to be processed splitting it into parts.")
        split_file(file, games)
        for i in range(games):
            try:
                with open(f"{file}{i+1}") as f:
                    f.close()
            except FileNotFoundError:  # check if the file exists
                split_file(file, games)

            files.append(f"{file}_part{i+1}")

    # run the process_files function with profiling
    print("Processing files...")
    profiler = cProfile.Profile()
    profiler.enable()
    process_files()
    profiler.disable()

    # output the profiling results
    stats = pstats.Stats(profiler)
    stats.dump_stats("profiling_results.pstats")

    # close db connection
    conn.close()
