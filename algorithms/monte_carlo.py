import operator
import numpy as np
from typing import List
from algorithms.abstract_state import AbstractState, AbstractMove
from algorithms.timeoutable_algorithm import TimeoutableAlgorithm
from train_and_test.logger import logger


class MonteCarlo(TimeoutableAlgorithm):
    def __init__(self, seed=None, timeout_seconds=5):
        assert seed is None or (isinstance(seed, int) and seed > 0)
        assert timeout_seconds > 0

        super().__init__(timeout_seconds)
        self._player = None
        self._random_choice = np.random.RandomState(seed).choice

    def get_best_move(self, state: AbstractState):
        max_depth = 50
        self._player = state.get_current_player()
        moves = state.get_next_moves()
        victories_histogram = [0 for _ in range(len(moves))]
        while not self.ran_out_of_time:
            for move, i in zip(moves, range(len(victories_histogram))):
                state.pretend_to_make_a_move(move)
                result = self._roll_out(state, max_depth, True)
                state.unpretend_to_make_a_move(move)
                if self.ran_out_of_time:
                    break
        # TODO decide whether the fact that the non-complete iteration affects the result is okay or not
        most_victories_index = victories_histogram.index(max(victories_histogram))
        return moves[most_victories_index]

    def _roll_out(self, state: AbstractState, depth, is_random_event):
        """
        the roll-out of the game-tree. choosing recursively random moves, and returning who won
        :param state: the state of the game
        :param depth: the maximun depth of the roll-out. this is necessary because this game has 'no move' move,
        which may result in stack over-flow
        :param is_random_event: boolean indicating whether a random move is made or not
        :return:
        """
        if self.ran_out_of_time:
            return 0
        if depth == 0:
            return 0
        if state.is_final():
            winner = max(state.get_scores_by_player().items(), key=operator.itemgetter(1))[0]
            return 1 if self._player is winner else 0
        if is_random_event:
            move = state.throw_dice()
            result = self._roll_out(state, depth - 1, False)
            state.unthrow_dice(move)
        else:
            moves = state.get_next_moves()
            next_moves = list(filter(lambda m: m.is_doing_anything(), moves))
            if len(next_moves) == 0:
                next_moves = moves
            move = self._random_choice(next_moves)
            state.pretend_to_make_a_move(move)
            result = self._roll_out(state, depth - 1, True)
            state.unpretend_to_make_a_move(move)
        return result
