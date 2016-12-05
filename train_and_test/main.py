import os
import time

from game.catan_state import CatanState
from players.expectimax_baseline_player import ExpectimaxBaselinePlayer
# noinspection PyUnresolvedReferences
from players.expectimax_weighted_probabilities_player import ExpectimaxWeightedProbabilitiesPlayer
# noinspection PyUnresolvedReferences
from players.filters import create_bad_robber_placement_filter
# noinspection PyUnresolvedReferences
from players.monte_carlo_with_filter_player import MonteCarloWithFilterPlayer
from players.random_player import RandomPlayer
from train_and_test.logger import logger, fileLogger

A, B, C, D, E, F, G = [], [], [], [], [], [], []
excel_file_name = 'NAME_NOT_SET_{}.xlsx'.format(time.time())


def excel_data_grabber(a, b, c, d, e, f, g):
    global A, B, C, D, E, F, G
    A.append(a)
    B.append(b)
    C.append(c)
    D.append(d)
    E.append(e)
    F.append(f)
    G.append(g)


def scores_changed(state, previous_scores, scores):
    for player in state.players:
        if previous_scores[player] != scores[player]:
            return True
    return False


def clean_previous_images():
    for file_name in os.listdir(path='.'):
        if file_name.split(sep='_')[0] == 'turn':
            os.remove(file_name)


def execute_game(seed):
    timeout_seconds = 5
    p0 = RandomPlayer(seed)
    p1 = ExpectimaxBaselinePlayer(seed, timeout_seconds)
    p2 = ExpectimaxBaselinePlayer(seed, timeout_seconds)
    p3 = ExpectimaxBaselinePlayer(seed, timeout_seconds)
    players = [p0, p1, p2, p3]

    state = CatanState(players, seed)

    turn_count = 0
    score_by_player = state.get_scores_by_player()
    # state.board.plot_map('turn_{}_scores_{}.png'
    #                      .format(turn_count, ''.join('{}_'.format(v) for v in score_by_player.values())))

    while not state.is_final():
        # noinspection PyProtectedMember
        logger.info('----------------------p{}\'s turn----------------------'.format(state._current_player_index))

        turn_count += 1
        robber_placement = state.board.get_robber_land()

        move = state.get_current_player().choose_move(state)
        assert not scores_changed(state, score_by_player, state.get_scores_by_player())
        state.make_move(move)
        state.make_random_move()

        previous_score_by_player = score_by_player
        score_by_player = state.get_scores_by_player()

        if scores_changed(state, previous_score_by_player, score_by_player):
            scores = ''.join('{} '.format(v) for v in score_by_player.values())
            move_data = {k: v for k, v in move.__dict__.items() if (
                v and k != 'resources_updates' and not
                (k == 'robber_placement_land' and v == robber_placement) and not
                (isinstance(v, dict) and sum(v.values()) == 0))}
            logger.info('| {}| turn: {:3} | move:{} |'.format(scores, turn_count, move_data))

            # image_name = 'turn_{}_scores_{}.png'.format(
            #     turn_count, ''.join('{}_'.format(v) for v in score_by_player.values()))
            # state.board.plot_map(image_name, state.current_dice_number)

    players_scores_by_names = {(k, v.__class__, v.expectimax_alpha_beta.evaluate_heuristic_value.__name__ if (
        isinstance(v, ExpectimaxBaselinePlayer)) else None): score_by_player[v]
        for k, v in locals().items() if v in players
        }
    fileLogger.info('\n' + '\n'.join(' {:150} : {} '.format(str(name), score)
                                     for name, score in players_scores_by_names.items()) +
                    '\n turns it took: {}\n'.format(turn_count) + ('-' * 156))

    p0_type = type(p0).__name__
    p1_2_3_type = type(p1).__name__
    global excel_file_name
    excel_file_name = '{}_vs_{}_timeout_{}_seed_{}.xlsx'.format(p0_type, p1_2_3_type, timeout_seconds, seed,
                                                                int(time.time()))
    p0_score = state.get_scores_by_player()[p0]
    p1_score = state.get_scores_by_player()[p1]
    p2_score = 0  # state.get_scores_by_player()[p2]
    p3_score = 0  # state.get_scores_by_player()[p3]
    excel_data_grabber(p0_score, p1_score, p2_score, p3_score, turn_count, p0_type, p1_2_3_type)


def flush_to_excel():
    global A, B, C, D, E, F, G, excel_file_name
    import pandas as pd
    df = pd.DataFrame({"p0_score": A, "p1_score": B, "p2_score": C,
                       "p3_score": D, "turn_count": E, "p0_type": F, "p1_2_3_type": G})
    writer = pd.ExcelWriter(excel_file_name, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='results')


def main():
    global A, B, C, D, E, F, G
    import multiprocessing

    try:
        cpus = multiprocessing.cpu_count()
    except NotImplementedError:
        cpus = 2  # arbitrary default

    pool = multiprocessing.Pool(processes=cpus)
    pool.map(execute_game, [None] * 10)

    # for _ in range(10):
    #     clean_previous_images()
    #     execute_game(None)
    flush_to_excel()


if __name__ == '__main__':
    main()
