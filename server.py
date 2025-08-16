#!/usr/bin/env python3

import os
import json
import traceback
import random

from flask import Flask, request, jsonify, send_from_directory

import solver as solver
from test import check_sudoku

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/victory_check', methods=['POST'])
def victory_check():
    try:
        payload = request.json
        board = payload['board']
        empty_board = [[0] * len(board) for _ in board]
        assert board
        check_sudoku(empty_board, board)
        return jsonify({'victory': True})
    except AssertionError:
        return jsonify({'victory': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/solve', methods=['POST'])
def solve():
    try:
        board = request.json
        formula = solver.sudoku_board_to_sat_formula(board)
        assignments = solver.satisfying_assignment(formula)
        sol = solver.assignments_to_sudoku_board(assignments, len(board))
        return jsonify(sol)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_puzzle():
    try:
        payload = request.json
        size = payload.get('size', 9)
        
        # solve empty board
        empty_board = [[0 for _ in range(size)] for _ in range(size)]
        formula = solver.sudoku_board_to_sat_formula(empty_board)
        assignments = solver.satisfying_assignment(formula)
        sol = solver.assignments_to_sudoku_board(assignments, size)
        
        if sol is None:
            return jsonify(empty_board)
        
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
        
        return jsonify(puzzle)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
