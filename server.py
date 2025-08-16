#!/usr/bin/env python3

import os
import html
import json
import mimetypes
import traceback
import random

from wsgiref.handlers import read_environ
from wsgiref.simple_server import make_server

import solver as solver
from test import check_sudoku

LOCATION = os.path.realpath(os.path.dirname(__file__))


def parse_post(environ):
    try:
        body_size = int(environ.get("CONTENT_LENGTH", 0))
    except:
        body_size = 0

    body = environ["wsgi.input"].read(body_size)
    try:
        return json.loads(body)
    except:
        return {}

def victory_check(payload):
    board = payload['board']
    empty_board = [[0] * len(board) for _ in board]
    try:
        assert board
        check_sudoku(empty_board, board)
        return {'victory': True}
    except AssertionError:
        return {'victory': False}

def solve(payload):
    board = payload
    formula = solver.sudoku_board_to_sat_formula(board)
    assignments = solver.satisfying_assignment(formula)
    sol = solver.assignments_to_sudoku_board(assignments, len(board))
    return sol

def generate_puzzle(payload):
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


funcs = {
    'victory_check': victory_check,
    'solve': solve,
    'generate': generate_puzzle,
}

def application(environ, start_response):
    path = (environ.get("PATH_INFO", "") or "").lstrip("/")
    if path in funcs:
        try:
            out = funcs[path](parse_post(environ))
            body = json.dumps(out).encode("utf-8")
            status = "200 OK"
            type_ = "application/json"
        except Exception as e:
            tb = traceback.format_exc()
            print(
                "--- Python error (likely in your solver code) during the next operation:\n"
                + tb,
                end="",
            )
            body = html.escape(tb).encode("utf-8")
            status = "500 INTERNAL SERVER ERROR"
            type_ = "text/plain"
    else:
        if path == "":
            static_file = "index.html"
        else:
            static_file = path

        test_fname = os.path.join(LOCATION, static_file)
        try:
            status = "200 OK"
            with open(test_fname, "rb") as f:
                body = f.read()
            type_ = mimetypes.guess_type(test_fname)[0] or "text/plain"
        except FileNotFoundError:
            status = "404 FILE NOT FOUND"
            body = test_fname.encode("utf-8")
            type_ = "text/plain"

    len_ = str(len(body))
    headers = [("Content-type", type_), ("Content-length", len_)]
    start_response(status, headers)
    return [body]


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3001))
    with make_server("", PORT, application) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down.")
            httpd.server_close()
