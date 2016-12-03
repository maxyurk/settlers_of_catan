import math

import time

from game.catan_state import CatanState
from players.monte_carlo_player import ExpectimaxMonteCarloPlayer
from players.expectimax_baseline_player import ExpectimaxPlayer
# noinspection PyUnresolvedReferences
from players.random_player import RandomPlayer
from train_and_test.logger import fileLogger

gr = (math.sqrt(5) + 1) / 2  # golden ratio
tolerance = 50
seed = None
timeout_seconds = 3
games_for_average = 3
A, B, C, D, E, F, G = [], [], [], [], [], [], []


def excel_data_grabber(a, b, c, d, e):
    global A, B, C, D, E
    A.append(a)
    B.append(b)
    C.append(c)
    D.append(d)
    E.append(e)


def excel_data_grabber2(f, g):
    global F, G
    F.append(f)
    G.append(g)


def golden_section_search(f, a, b, tol=tolerance):
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
    fileLogger.info('GSS: entered golden_section_search with a={}, b={}, tol={}'.format(a, b, tol))
    c = b - (b - a) / gr
    fileLogger.info('GSS: c = b - (b - a) / gr = {} - ({} - {}) / {} = {}'.format(b, b, a, gr, c))
    d = a + (b - a) / gr
    fileLogger.info('GSS: d = a + (b - a) / gr = {} - ({} - {}) / {} = {}'.format(a, b, a, gr, d))
    while abs(c - d) > tol:
        f1 = f(c)
        fileLogger.info('GSS: f(c) = f({}) = {}'.format(c, f1))
        f2 = f(d)
        fileLogger.info('GSS: f(d) = f({}) = {}'.format(d, f2))
        if f1 < f2:
            b = d
        else:
            a = c
        fileLogger.info('GSS: after assignment b={}, a={}'.format(b, a))

        # we recompute both c and d here to avoid loss of precision which may lead to incorrect results or infinite loop
        c = b - (b - a) / gr
        d = a + (b - a) / gr
        fileLogger.info('GSS: after recompute c={}, d={}'.format(c, d))

    fileLogger.info(
        'GSS: End of while loop. a={}, b={}, c={}, d={}, return ((b + a) / 2)={}'.format(a, b, c, d, ((b + a) / 2)))
    return (b + a) / 2


def execute_game_given_monte_carlo_branching_factor(branching_factor):
    fileLogger.info('EXEC_GAME: branching_factor={}'.format(branching_factor))
    p0 = ExpectimaxPlayer(seed, timeout_seconds)  # RandomPlayer(seed)
    p1 = ExpectimaxMonteCarloPlayer(seed, timeout_seconds, int(branching_factor))
    state = CatanState([p0, p1], seed)

    count_moves = 0
    while not state.is_final():
        count_moves += 1
        state.make_move(state.get_current_player().choose_move(state))
        state.make_random_move()

    p0_score = state.get_scores_by_player()[p0]
    p1_score = state.get_scores_by_player()[p1]
    count_moves_factor = 1 * count_moves
    p0_factor = 10000 if (p0_score >= 10) else 0
    p1_factor = p1_score * 0.2
    res = - p0_factor + (p1_factor * count_moves_factor)
    fileLogger.info('EXEC_GAME: p0_score={}, p1_score={}, count_moves={}, p0_factor={}, p1_factor={}, '
                    'count_moves_factor={}, res={}'.format(p0_score, p1_score, count_moves, p0_factor, p1_factor,
                                                           count_moves_factor, res))
    excel_data_grabber(p0_score, p1_score, count_moves, res, branching_factor)
    return res


def calc_average_result(branching_factor: int):
    global games_for_average
    import multiprocessing

    try:
        cpus = multiprocessing.cpu_count()
    except NotImplementedError:
        cpus = 2  # arbitrary default

    pool = multiprocessing.Pool(processes=cpus)
    results = pool.map(execute_game_given_monte_carlo_branching_factor, [branching_factor]*games_for_average)

    # results = [execute_game_given_monte_carlo_branching_factor(branching_factor) for _ in range(games_for_average)]
    average = sum(results) / len(results)
    fileLogger.info('AVERAGE: average of {} games is {}'.format(len(results), average))
    excel_data_grabber2(branching_factor, average)
    return average


def train_monte_carlo():
    global tolerance, seed, timeout_seconds, games_for_average
    fileLogger.info('MAIN: Train Monte Carlo: '
                    'tolerance={}, seed={}, timeout_seconds={}, games_for_average={}         [{}]'
                    .format(tolerance, seed, timeout_seconds, games_for_average, int(time.time())))
    res = golden_section_search(calc_average_result, 1, 5850)
    fileLogger.info("MAIN: Optimal branching factor is : {}         [{}]".format(res, int(time.time())))
    import pandas as pd
    df = pd.DataFrame({"p0_score": A, "p1_score": B, "count_moves": C, "res": D, "branching factor": E})
    writer = pd.ExcelWriter('train_monte_carlo_abcde_{:.3f}.xlsx'.format(int(time.time())), engine='xlsxwriter')
    df.to_excel(writer, sheet_name='monte_carlo')

    df2 = pd.DataFrame({"branching factor": F, "average": G})
    writer2 = pd.ExcelWriter('train_monte_carlo_fg____{:.3f}.xlsx'.format(int(time.time())), engine='xlsxwriter')
    df2.to_excel(writer2, sheet_name='monte_carlo')
    writer2.save()


if __name__ == '__main__':
    train_monte_carlo()
