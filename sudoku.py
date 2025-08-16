#!/usr/bin/env python3

import eel
import random
import solver as solver
from test import check_sudoku

eel.init('.')

@eel.expose
def victory_check(payload):
    try:
        board = payload['board']
        empty_board = [[0] * len(board) for _ in board]
        assert board
        check_sudoku(empty_board, board)
        return {'victory': True}
    except AssertionError:
        return {'victory': False}
    except Exception as e:
        return {'error': str(e)}

@eel.expose
def solve(board):
    try:
        formula = solver.sudoku_board_to_sat_formula(board)
        assignments = solver.satisfying_assignment(formula)
        sol = solver.assignments_to_sudoku_board(assignments, len(board))
        return sol
    except Exception as e:
        return {'error': str(e)}

@eel.expose
def generate_puzzle(payload):
    try:
        size = payload.get('size', 9)
        
        # solve empty board
        empty_board = [[0 for _ in range(size)] for _ in range(size)]
        formula = solver.sudoku_board_to_sat_formula(empty_board)
        assignments = solver.satisfying_assignment(formula)
        sol = solver.assignments_to_sudoku_board(assignments, size)
        
        if sol is None:
            return empty_board
        
        # remove most numbers
        if size == 4:
            keep_count = random.randint(6, 10)
        else: # size == 9
            keep_count = random.randint(17, 25)
        
        # pick random positions to keep
        positions = [(i, j) for i in range(size) for j in range(size)]
        random.shuffle(positions)
        keep_positions = set(positions[:keep_count])
        
        # create puzzle with only kept positions
        puzzle = [[sol[i][j] if (i,j) in keep_positions else 0 
                   for j in range(size)] for i in range(size)]
        
        return puzzle
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    # Start the desktop app
    eel.start('desktop.html', size=(800, 900), port=0)