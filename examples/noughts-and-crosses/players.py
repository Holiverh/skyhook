"""Play Noughts and Crosses ... poorly."""

import random
import typing

import skyhook
import noughts_and_crosses as tictactoe


@tictactoe.play.lambda_
def play_first(
    mark: typing.Union[tictactoe.Nought, tictactoe.Cross],
    board: tictactoe.Board
) -> int:
    """Place marker in first free cell."""
    for index, cell in enumerate(board):
        if cell is None:
            return index


@tictactoe.play.lambda_
def play_random(
    mark: typing.Union[tictactoe.Nought, tictactoe.Cross],
    board: tictactoe.Board,
) -> int:
    """Place marker randomly on the board."""
    placement = random.choice([
        index for index, cell in enumerate(board) if cell is None])
    return placement
