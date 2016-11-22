import logging
import os
import time
from game.catan_state import CatanState
from game.pieces import Colony, Road
from players.alpha_beta_player import AlphaBetaPlayer
from players.random_player import RandomPlayer
from train_and_test.logger import logger


def scores_changed(state, previous_scores, scores):
    for player in state.players:
        if previous_scores[player] != scores[player]:
            return True
    return False


def build_game(players, seed):
    p1, p2 = players
    state = CatanState([p1, p2], seed)
    # state.board.set_location(p1, 0, Colony.Settlement)
    # state.board.set_location(p1, 1, Colony.Settlement)
    # state.board.set_location(p1, 14, Colony.Settlement)
    # state.board.set_location(p1, 23, Colony.Settlement)
    # state.board.set_path(p1, (0, 4), Road.Paved)
    # state.board.set_path(p1, (4, 1), Road.Paved)
    # state.board.set_path(p1, (14, 9), Road.Paved)
    # state.board.set_path(p1, (23, 17), Road.Paved)
    # state.board.set_location(p2, 52, Colony.Settlement)
    # state.board.set_location(p2, 53, Colony.Settlement)
    # state.board.set_location(p2, 22, Colony.Settlement)
    # state.board.set_location(p2, 36, Colony.Settlement)
    # state.board.set_path(p2, (52, 49), Road.Paved)
    # state.board.set_path(p2, (49, 53), Road.Paved)
    # state.board.set_path(p2, (22, 28), Road.Paved)
    # state.board.set_path(p2, (36, 31), Road.Paved)
    return state


def clean_previous_images():
    for file_name in os.listdir(None):
        if file_name.split(sep='_')[0] == 'turn':
            os.remove(file_name)


def execute_game():
    seed = None  # 0.35 - this number, when used with alpha-beta players, produces a very slow game
    p1 = AlphaBetaPlayer(3, seed)
    # p2 = AlphaBetaPlayer(1, seed)
    # p1 = RandomPlayer(seed)
    p2 = RandomPlayer(seed)
    state = build_game([p1, p2], seed)

    clean_previous_images()

    start_time = time.time()
    c = 0
    previous_scores = state.get_scores_by_player()
    logger.info('\np1 {}:p2 {} | turn: {} | game start'.format(previous_scores[p1], previous_scores[p2], c))
    if __debug__:
        state.board.plot_map('turn_{}_{}_to_{}.jpg'.format(c, previous_scores[p1], previous_scores[p2]))
    while not state.is_final():
        c += 1

        state.throw_dice()
        # --------------------------------------
        # TODO remove
        if __debug__ and scores_changed(state, previous_scores, state.get_scores_by_player()):
            logger.error('\n~BUG throw dice changed score~')
            exit(1)
        # --------------------------------------
        move = state.get_current_player().choose_move(state)
        # --------------------------------------
        # TODO remove
        if __debug__ and scores_changed(state, previous_scores, state.get_scores_by_player()):
            logger.error('\n~BUG choose move changed score~')
            exit(1)
        # --------------------------------------
        state.make_move(move)

        current_scores = state.get_scores_by_player()
        score_changed = scores_changed(state, previous_scores, current_scores)
        if score_changed:
            previous_scores = current_scores

        if move.is_doing_anything():
            logger.info('\np1 {}:p2 {} | turn: {} | time: {} | move:{}'
                        .format(current_scores[p1],
                                current_scores[p2],
                                c,
                                time.time() - start_time,
                                {k: v for k, v in move.__dict__.items() if v and k != 'resources_updates'}))
            if __debug__:
                state.board.plot_map('turn_{}_{}_to_{}.jpg'.format(c, current_scores[p1], current_scores[p2]))
        elif score_changed:
            # TODO remove
            logger.error('\np1 {}:p2 {} | turn: {} | BUG. score changed, without movement.'
                        .format(current_scores[p1], current_scores[p2], c))
            exit(1)


def main():
    for _ in range(1):
        execute_game()

if __name__ == '__main__':
    main()
