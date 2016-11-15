import logging
from logging import info

from game.catan_state import CatanState
from game.pieces import Colony, Road
from players.alpha_beta_player import *
from players.random_player import *
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def scores_changed(state, previous_scores, scores):
    for player in state._players:
        if previous_scores[player] != scores[player]:
            return True
    return False


def build_game(p1, p2):
    state = CatanState([p1, p2])
    state.board.set_location(p1, 0, Colony.Settlement)
    state.board.set_location(p1, 1, Colony.Settlement)
    state.board.set_location(p1, 14, Colony.Settlement)
    state.board.set_location(p1, 23, Colony.Settlement)
    state.board.set_path(p1, (0, 4), Road.Paved)
    state.board.set_path(p1, (4, 1), Road.Paved)
    state.board.set_path(p1, (14, 9), Road.Paved)
    state.board.set_path(p1, (23, 17), Road.Paved)
    state.board.set_location(p2, 52, Colony.Settlement)
    state.board.set_location(p2, 53, Colony.Settlement)
    state.board.set_location(p2, 22, Colony.Settlement)
    state.board.set_location(p2, 36, Colony.Settlement)
    state.board.set_path(p2, (52, 49), Road.Paved)
    state.board.set_path(p2, (49, 53), Road.Paved)
    state.board.set_path(p2, (22, 28), Road.Paved)
    state.board.set_path(p2, (36, 31), Road.Paved)
    return state


def clean_previous_images():
    for file_name in os.listdir(None):
        if file_name.split(sep='_')[0] == 'turn':
            os.remove(file_name)


def main():
    p1 = AlphaBetaPlayer(1)
    p2 = RandomPlayer()
    state = build_game(p1, p2)
    clean_previous_images()

    c = 0
    previous_scores = state.get_scores_by_player()
    logger.info('\n{}:{} | turn: {} | game start'.format(previous_scores[p1], previous_scores[p2], c))
    state.board.plot_map('turn_{}_{}_to_{}.jpg'.format(c, previous_scores[p1], previous_scores[p2]))
    while not state.is_final():
        c += 1

        state.throw_dice()
        # --------------------------------------
        if scores_changed(state, previous_scores, state.get_scores_by_player()):
            logger.info('\n~throw dice~')
        # --------------------------------------
        move = state.get_current_player().choose_move(state)
        # --------------------------------------
        if scores_changed(state, previous_scores, state.get_scores_by_player()):
            logger.info('\n~choose move~')
        # --------------------------------------
        state.make_move(move)
        # --------------------------------------
        if scores_changed(state, previous_scores, state.get_scores_by_player()):
            logger.info('\n~make move~')
        # --------------------------------------

        current_scores = state.get_scores_by_player()
        score_changed = scores_changed(state, previous_scores, current_scores)
        if score_changed:
            previous_scores = current_scores

        if move.is_doing_anything():
            logger.info('\n{}:{} | turn: {} | move:{}'
                 .format(current_scores[p1], current_scores[p2], c, {k: v for k, v in move.__dict__.items() if v}))
            state.board.plot_map('turn_{}_{}_to_{}.jpg'.format(c, current_scores[p1], current_scores[p2]))
        elif score_changed:
            logger.info('\n{}:{} | turn: {} | BUG. score changed, without movement.'
                 .format(current_scores[p1], current_scores[p2], c))
        else:
            logger.info('.')

if __name__ == '__main__':
    main()

