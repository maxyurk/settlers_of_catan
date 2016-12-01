import math

from game.catan_state import CatanState
from players.alpha_beta_monte_carlo_player import AlphaBetaMonteCarloPlayer
from players.alpha_beta_player import AlphaBetaPlayer
from train_and_test.logger import fileLogger

gr = (math.sqrt(5) + 1) / 2  # golden ratio


def golden_section_search(f, a, b, tol=10):
    """
    golden section search
    to find the minimum of f on [a,b]
    f: a strictly unimodal function on [a,b]
    :param f: The function we want to find it's min val
    :param a: left edge x value
    :param b: right edge x value
    :param tol: error tolerance
    :return: x value where f(x) is minimal
    """

    c = b - (b - a) / gr
    d = a + (b - a) / gr
    while abs(c - d) > tol:
        if f(c) < f(d):
            b = d
        else:
            a = c

        # we recompute both c and d here to avoid loss of precision which may lead to incorrect results or infinite loop
        c = b - (b - a) / gr
        d = a + (b - a) / gr

    return (b + a) / 2


def monte_carlo_player_grade_given_branching_factor(branching_factor):
    seed = None
    timeout_seconds = 5
    p0 = AlphaBetaPlayer(seed, timeout_seconds)
    p1 = AlphaBetaMonteCarloPlayer(seed, timeout_seconds, None, int(branching_factor))
    state = CatanState([p0, p1], seed)

    count_moves = 0
    while not state.is_final():
        count_moves += 1
        state.make_move(state.get_current_player().choose_move(state))
        state.make_random_move()

    p0_score = state.get_scores_by_player()[p0]
    p1_score = state.get_scores_by_player()[p1]
    count_moves_weight = 1
    p0_score_weight = 1
    p1_score_weight = 1
    res = (count_moves_weight * count_moves) + (p0_score_weight * p0_score) + (p1_score_weight * (1 / p1_score))
    excel_data_grabber(p0_score, p1_score, count_moves, res, branching_factor)
    return res


A = []
B = []
C = []
D = []
E = []


def excel_data_grabber(a, b, c, d, e):
    global A
    global B
    global C
    global D
    global E
    A.append(a)
    B.append(b)
    C.append(c)
    D.append(d)
    E.append(e)


def train_monte_carlo():
    fileLogger.info("Train Monte Carlo")
    res = golden_section_search(monte_carlo_player_grade_given_branching_factor, 1, 5850)
    fileLogger.info("Optimal branching factor is : {}".format(res))
    import pandas as pd
    df = pd.DataFrame({"p0_score": A, "p1_score": B, "count_moves": C, "res": D, "branching factor": E})
    writer = pd.ExcelWriter('train_monte_carlo.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='monte_carlo')
    writer.save()


if __name__ == '__main__':
    train_monte_carlo()
