import sys
import doctest

sys.setrecursionlimit(10_000)

def update_formula(formula, assignment):
    """
    given a formula, returns an updated formula, incorporating
    the given assignment and its consequences
    formula = [[clause], [(var, bool), (var, bool)]]
    assignment = (var, bool)

    >>> update_formula([[('a', True), ('c', False)]], ('a', False))
    [[('c', False)]]

    >>> update_formula([[('a', True), ('c', False)], [('b', True), ('d', True)]], ('c', False))
    [[('b', True), ('d', True)]]
    """
    new_formula = []
    for clause in formula:
        new_clause = []
        next_clause = True
        for tup in clause:
            if assignment[0] == tup[0]: # this tup has the assigned variable
                if assignment[1] == tup[1]: # assigned bool == tuple's bool
                    # exclude the whole clause from formula bc it's been satisfied
                    next_clause = False
                    break # break out of current new_clause
                else:
                    # do not include tuple in formula
                    continue # continue out of current tup
            # add this random tuple to new clause
            else:
                new_clause.append(tup)
        if next_clause:
            new_formula.append(new_clause)
    return new_formula

def make_unitless_formula(formula):
    unitless = formula
    assignments = {}
    # check for clauses with 1 tuple
    for clause in formula:
        if len(clause) == 1:
            unitless = update_formula(unitless, clause[0]) # just assign it first
            assignments[clause[0][0]] = clause[0][1]
            empties = [clause for clause in unitless if clause == []]
            if len(empties) > 0:
                return None
    return unitless, assignments


def satisfying_assignment(formula):
    """
    returns satisfying assignment for CNF formula if one exists, else returns None.

    where a satisfying assignment is a dictionary mapping variables to Bools
    that satisfies the given formula {'a': False, 'b': True, ...}

    >>> x = satisfying_assignment([[('a', True), ('b', False), ('c', True)]])
    >>> x.get('a', None) is True or x.get('b', None) is False or x.get('c', None) is True
    True
    >>> satisfying_assignment([[('a', True)], [('a', False)]])
    """
    # successful bc:
    if len(formula) == 0: # formula = []
        return {}

    x = make_unitless_formula(formula)
    if x is None:
        return None
    unitless, assignments = x

    if unitless is None:
        return None
    
    elif len(unitless) == 0:
        return assignments
    
    clause = unitless[0]
    if clause: # if clause can be reduced further:
        empties = [clause for clause in unitless if clause == []]
        if len(empties) > 0:
            return None

        tup = clause[0]
        # subprob = formula - clause + conseq of setting clause
        new_formula = update_formula(unitless, tup)
        result = satisfying_assignment(new_formula)
        # successful subprob:
        if result is not None:
            result[tup[0]] = tup[1]
            return result | assignments
        # unsuccessful subprob
        else:
            # try switched T/F of that tup
            switched_tup = (tup[0], not tup[1])
            switched_formula = update_formula(unitless, switched_tup)
            # successful with switched T/F
            switched_result = satisfying_assignment(switched_formula)
            if switched_result is not None:
                switched_result[switched_tup[0]] = switched_tup[1]
                return switched_result | assignments
            # unsuccessful with switched T/F
            else:
                return None
    return None


def sudoku_board_to_sat_formula(sudoku_board):
    """
    generate a SAT formula that, when solved, represents a solution to the
    given sudoku board that can be passed as the formula into satisfying_assignment(formula).
    formula = [[clause], [((val, row, col), True), ( (val, row, col), False ) ], [ ]]
    """
    n = len(sudoku_board)
    sn = round((len(sudoku_board))**.5) # gets len of each subgrid

    def exactly_1():
        """
        for each spot on the grid, at least 1 val must be True
        ie. each spot on the grid must have >=1 number in it
        """
        rules = []
        for row in range(n):
            for col in range(n):
                clause = []
                for val in range(1, n+1):
                    clause.append(((val, row, col), True))
                    for val2 in range(val+1, n+1): # ensures only 1 val per cell
                        pair_clause = [((val, row, col), False),\
                                        ((val2, row, col), False)]
                        rules.append(pair_clause)
                rules.append(clause)

        return rules


    def at_most_1_row():
        """
        for each row, given a list of clauses of literal pairs,
        at least 1 var amongst the pair must be False
        """
        rules = []
        for row in range(n):
            for val in range(1, n+1):
                clause = [] # ensures each row has 1 of each val
                for col in range(n):
                    for col2 in range(col+1, n):
                        rules.append([((val, row, col), False),\
                                      ((val, row, col2), False)])
                    clause.append(((val, row, col), True))
                rules.append(clause)
        return rules


    def at_most_1_col():
        """
        for each col, given a list of clauses of literal pairs,
        at least 1 var amongst the pair must be False
        """
        rules = []
        for col in range(n):
            for val in range(1, n+1):
                clause = []
                for row in range(n):
                    for row2 in range(row+1, n):
                        rules.append([((val, row, col), False),\
                                      ((val, row2, col), False)])
                    clause.append(((val, row, col), True))
                rules.append(clause)
        return rules


    def get_topleft_coords():
        """
        gets board's all top left corner's coordinates
        """
        output = []
        for row in range(0, n, sn):
            for col in range(0, n, sn):
                output.append((row, col))
        return output
        

    def get_subgrid_coords(coords):
        """
        enumerates all coordinates in a given subgrid, 
        denoted by coordinates of the top left of a subgrid
        """
        output = []
        for row in range(coords[0], coords[0] + sn):
            for col in range(coords[1], coords[1]+sn):
                output.append((row, col))
        return output


    def exactly_1_subgrids():
        """
        for each subgrid, given a list of clauses of literal pairs,
        at least 1 var amongst the pair must be False
        """
        rules = []
        topleft_coords = get_topleft_coords()
        for c in topleft_coords:
            subgrid_coords = get_subgrid_coords(c)
            for i, coord in enumerate(subgrid_coords):
                for coord2 in subgrid_coords[i+1:]:
                    for val in range(1, n+1):
                        rules.append([((val, *coord), False),\
                                      ((val, *coord2), False)])
            for val in range(1, n+1):
                clause = []
                for cd in subgrid_coords:     
                    clause.append(((val, *cd), True))
                rules.append(clause)
        return rules

    def keep_starting_vals():
        rules = []
        for row in range(n):
            for col in range(n):
                if sudoku_board[row][col] != 0:
                    rules.append([((sudoku_board[row][col], row, col), True)])
        return rules
    
    rules1 = exactly_1()
    rules2 = at_most_1_row()
    rules3 = at_most_1_col()
    rules4 = exactly_1_subgrids()
    rules5 = keep_starting_vals()

    formula = rules1 + rules2 + rules3 + rules4 + rules5
    return formula


def assignments_to_sudoku_board(assignments, n):
    """
    given a variable assignment as given by satisfying_assignment, and a
    size n, creates n-by-n 2-d array (list-of-lists) representing the
    solution given by the provided assignment of variables.

    if assignments are of an unsolvable board, return None
    """

    board = [[0 for col in range(n)] for row in range(n)]

    if assignments:
        for k in assignments:
            if assignments[k] is True:
                board[k[1]][k[2]] = k[0] # puts val in that row, col
        return board
    
    return None

if __name__ == "__main__":
    _doctest_flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    doctest.testmod(optionflags=_doctest_flags)
