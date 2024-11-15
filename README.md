<div>
<a id="readme-top"></a>

<br />
<h3 align="center">Chess app</h3>
<p align="center">
    <img src="https://github.com/arozx/a-level_project/blob/main/media/black/Bishop.svg?raw=true" alt="Bishop">
</p>

  <p align="center">
    A Python bot that plays chess against you
    <br />
    <a href="https://github.com/arozx/a-level_project/issues">Report Bug</a>
    ·
    <a href="https://github.com/arozx/a-level_project/issues">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#testing">Testing</a></li>
    <li>
      <a href="#license">Licence</a>
      <ul>
        <li><a href="#images">Images</a></li>
      </ul>
    </li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

A full stack chess app using PyQt5 for the front end and an engine using Monte-Carlo Algorithms. This project is designed to meet the AQA Computer Science A Level specification.

- `chess_board_1.py`: Contains the `ChessBoard` class which initializes the chessboard and sets up the pieces.
- `db_connector.py`: Handles database connections.
- `eval_board.py`: Evaluates the board state.
- `gui.py`: Manages the graphical user interface.
- `hsm.py`: Hierarchical state machine implementation.
- `mcts.py`: Monte Carlo Tree Search implementation.
- `pgn_to_db.py`: Converts PGN files to database entries.
- `pieces.py`: Defines the chess pieces (Bishop, King, Knight, Pawn, Queen, Rook).
- `promotion_window.py`: Manages the promotion window for pawns.
- `split_file.py`: Utility to split files.
- `train.py`: Training script for AI.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

Python versions 3.9 - 3.12 are supported. You can download the latest version of python from [here](https://www.python.org/downloads/)


### Installation

Clone the github repo by running

```sh
git clone https://github.com/arozx/a_level_project.git
```

Install the required packages by running

```sh
pip install -r requirements.txt
```

Download a lichess shard you can use any but I recomend the 2014-09 shard as it is roughly 1,000,000 games and about 0.2GB in size. You can download the shard by running

```sh
mkdir lichess
cd lichess
wget https://database.lichess.org/standard/lichess_db_standard_rated_2014-09.pgn.zst
```

Next you will need to extract the shard by running

```sh
zstd -d lichess_db_standard_rated_2014-09.pgn.zst
```

Note, if you are using a different shard you will need to change the file name in the above commands. And you will need to change the file name in the pgn_to_db.py file **line 154**.

Finally you will need to run a script to convert the pgn to a database file. You can do this by running

```sh
python3 pgn_to_db.py
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE -->
## Usage

To run the program use the following comand

```sh
python chess_board.py
```

### Testing

To run the tests, first install pytest by running

```sh
pip install pytest
```

Then run the tests by running

```sh
pytest
```

<!-- LICENSE -->
## License

### Images

Images used in this project are from [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:SVG_chess_pieces). The images are under the Creative Commons license. Please see the individual image pages for more information on the copyright holder and the specific license conditions.

<!-- CONTACT -->
## Contact

Mastodon - [@arozx](https://infosec.exchange/@arozx)

Project Link: [https://github.com/arozx/a-level_project](https://github.com/arozx/a-level_project)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
