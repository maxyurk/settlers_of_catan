import copy
from collections import Counter
from math import ceil
from typing import Dict, Callable, List

from algorithms.abstract_state import AbstractState, AbstractMove
from algorithms.alpha_beta_pruning_expectimax import AlphaBetaExpectimax
from game.catan_state import CatanState
from game.resource import Resource, ResourceAmounts
from players.abstract_player import AbstractPlayer
from players.random_player import RandomPlayer
from train_and_test.logger import logger


class ExpectimaxBaselinePlayer(AbstractPlayer):

    def default_heuristic(self, state: CatanState):
        if state.is_initialisation_phase():
            return self._random_choice([i for i in range(10)])
        # as discussed with Shaul, this isn't zero-sum heuristic, but a max-gain approach where only own player's
        # value is is taken in account
        return float(state.get_scores_by_player()[self])

    def __init__(self, seed=None, timeout_seconds=5, heuristic=None, filter_moves=lambda x, y: x):
        assert seed is None or (isinstance(seed, int) and seed > 0)

        super().__init__(seed, timeout_seconds)

        if heuristic is None:
            heuristic = self.default_heuristic

        self.expectimax_alpha_beta = AlphaBetaExpectimax(
            is_maximizing_player=lambda p: p is self,
            evaluate_heuristic_value=heuristic,
            timeout_seconds=self._timeout_seconds,
            filter_moves=filter_moves)

    def choose_move(self, state: CatanState):
        self.expectimax_alpha_beta.start_turn_timer()
        best_move, move, depth = None, None, 1
        while not self.expectimax_alpha_beta.ran_out_of_time:
            best_move = move
            logger.info('starting depth {}'.format(depth))
            move = self.expectimax_alpha_beta.get_best_move(state, max_depth=depth)
            depth += 2
        if best_move is not None:
            return best_move
        else:
            logger.warning('did not finish depth 1, returning a random move')
            return RandomPlayer.choose_move(self, state)

    def choose_resources_to_drop(self) -> Dict[Resource, int]:
        if sum(self.resources.values()) < 8:
            return {}
        resources_count = sum(self.resources.values())
        resources_to_drop_count = ceil(resources_count / 2)
        if self.can_settle_city() and resources_count >= sum(ResourceAmounts.city.values()) * 2:
            self.remove_resources_and_piece_for_city()
            resources_to_drop = copy.deepcopy(self.resources)
            self.add_resources_and_piece_for_city()

        elif self.can_settle_settlement() and resources_count >= sum(ResourceAmounts.settlement.values()) * 2:
            self.remove_resources_and_piece_for_settlement()
            resources_to_drop = copy.deepcopy(self.resources)
            self.add_resources_and_piece_for_settlement()

        elif (self.has_resources_for_development_card() and
              resources_count >= sum(ResourceAmounts.development_card.values()) * 2):
            self.remove_resources_for_development_card()
            resources_to_drop = copy.deepcopy(self.resources)
            self.add_resources_for_development_card()

        elif self.can_pave_road() and resources_count >= sum(ResourceAmounts.road.values()) * 2:
            self.remove_resources_and_piece_for_road()
            resources_to_drop = copy.deepcopy(self.resources)
            self.add_resources_and_piece_for_road()

        else:
            return RandomPlayer.choose_resources_to_drop(self)

        resources_to_drop = [resource for resource, count in resources_to_drop.items() for _ in range(count)]
        return Counter(self._random_choice(resources_to_drop, resources_to_drop_count, replace=False))

    def set_heuristic(self, evaluate_heuristic_value: Callable[[AbstractState], float]):
        """
        set heuristic evaluation of a state in a game
        :param evaluate_heuristic_value: a callable that given state returns a float. higher means "better" state
        """
        self.expectimax_alpha_beta.evaluate_heuristic_value = evaluate_heuristic_value

    def set_filter(self, filter_moves: Callable[[List[AbstractMove]], List[AbstractMove]]):
        """
        set the filtering of moves in each step
        :param filter_moves: a callable that given list of moves, returns a list of moves that will be further developed
        """
        self.expectimax_alpha_beta.filter_moves = filter_moves
