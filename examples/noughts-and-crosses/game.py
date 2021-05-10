"""Nought and Crosses as played by Lambda functions."""

import itertools

import skyhook
import noughts_and_crosses as tictactoe

class Forfeit(Exception):
    """You lose! Good day sir!"""


def print_board(board):
    row = []
    for index, mark in enumerate(board):
        row.append(mark if mark else " ")
        if len(row) == 3:
            print(" | ".join(row))
            if index != len(board) - 1:
                print("----------")
                row.clear()
    print()
    print()


NOUGHT: tictactoe.Nought = "0"
CROSS: tictactoe.Cross = "X"
board: tictactoe.Board = (
    None, None, None,
    None, None, None,
    None, None, None,
)


hook = skyhook.Hook(tictactoe)
hook.define("play", arn="arn:aws:lambda:eu-west-2:000000000000:function:noughts-crosses-play")
for mark in itertools.cycle([NOUGHT, CROSS]):
    with hook.bind():
        cell = tictactoe.play(mark, board)
    try:
        if cell < 0 or cell > len(board) - 1:
            raise Forfeit("out of bounds")
        if board[cell]:
            raise Forfeit("already placed")
    except Forfeit:
        points_cross = 1 if mark != cross else 0
        points_nought = 1 if mark != nought else 0
        break
    else:
        board_mut = list(board)
        board_mut[cell] = mark
        board = tuple(board_mut)
        print_board(board)
        solutions = {
            (0, 1, 2): ...,  # T
            (3, 4, 5): ...,  # M (h)
            (6, 7, 8): ...,  # B
            (0, 4, 8): ...,  # TL to BR
            (2, 4, 6): ...,  # BL to TR
            (0, 3, 6): ...,  # L
            (1, 4, 7): ...,  # M (v)
            (2, 5, 8): ...,  # R
        }
        for x, y, z in solutions:
            solutions[(x, y, z)] = {
                (NOUGHT, NOUGHT, NOUGHT): NOUGHT,
                (CROSS, CROSS, CROSS): CROSS,
            }.get((board[x], board[y], board[z]))
        solved = any(solutions.values())
        full = not board.count(None)
        points_cross = list(solutions.values()).count(CROSS)
        points_nought = list(solutions.values()).count(NOUGHT)
        if solved or full:
            break
print("X", "winner! :>" if points_cross else "loser! :c")
print("0", "winner! :>" if points_nought else "loser! :c")
