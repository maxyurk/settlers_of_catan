import copy
import pickle
from typing import Dict

from algorithms.first_choice_hill_climbing import *
from game.catan_state import CatanState
from players.expectimax_weighted_probabilities_player import AlphaBetaWeightedProbabilitiesPlayer
from train_and_test.logger import logger

learned_weights_file_name = 'learned_weights'


class WeightsSpace(AbstractHillClimbableSpace):
    def __init__(self):
        self._time_seconds = 5
        self._iterations_count = 0
        self._max_iterations = 10
        self._games_per_iteration = 3
        self._seeds = [i for i in range(1, self._games_per_iteration + 1)]
        self.delta_unit = 0.4
        self._epsilon_is_weighting_better = 3

    def evaluate_state(self, weights) -> AbstractHillClimbingStateEvaluation:
        logger.info('| evaluating weights: {}'.format(weights))
        evaluation = 0

        for i in range(self._games_per_iteration):
            seed = self._seeds[i]
            p0 = AlphaBetaWeightedProbabilitiesPlayer(seed, self._time_seconds)
            p1 = AlphaBetaWeightedProbabilitiesPlayer(seed, self._time_seconds, weights)
            state = CatanState([p0, p1], seed)

            while not state.is_final():
                state.make_move(state.get_current_player().choose_move(state))
                state.make_random_move()

            scores = state.get_scores_by_player()
            logger.info('| done iteration {}. scores: {}'
                        .format(i, {'p0 (default weights)': scores[p0], 'p1 (new weights)': scores[p1]}))

            evaluation += scores[p1]
            evaluation -= scores[p0]

        self._iterations_count += 1

        return evaluation

    def get_neighbors(self, weights):
        next_weights = copy.deepcopy(weights)
        unit_fraction = self.delta_unit / len(weights)
        for key in next_weights.keys():
            next_weights[key] -= unit_fraction

        for key in next_weights.keys():
            weight_modification = self.delta_unit
            next_weights[key] += weight_modification
            yield next_weights
            next_weights[key] -= weight_modification

    def is_better(self, first_victories_count: int, second_victories_count: int) -> bool:
        is_better = first_victories_count > second_victories_count + self._epsilon_is_weighting_better
        logger.info('| is weight better: {}'.format(is_better))
        return is_better

    def enough_iterations(self) -> bool:
        return self._iterations_count >= self._max_iterations


def dump_weights(weights):
    f = open(learned_weights_file_name, 'wb+')
    pickle.dump(weights, f)


def load_weights() -> Dict[Any, float]:
    f = open(learned_weights_file_name, 'rb+')
    return pickle.load(f)


def main():
    space = WeightsSpace()
    previous_result, result = None, None
    for _ in range(3):
        result = first_choice_hill_climbing(space, AlphaBetaWeightedProbabilitiesPlayer.default_weights)
        if result == previous_result:
            break
        previous_result = result
        space.delta_unit /= 2
    logger.info('| learned weights: {}'.format(result))
    dump_weights(result)


if __name__ == '__main__':
    main()
