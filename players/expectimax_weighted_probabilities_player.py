from game.catan_state import CatanState
from game.development_cards import DevelopmentCard
from game.pieces import Road, Colony
from players.expectimax_baseline_player import ExpectimaxBaselinePlayer


class ExpectimaxWeightedProbabilitiesPlayer(ExpectimaxBaselinePlayer):
    default_weights = {Colony.City: 2, Colony.Settlement: 1, Road.Paved: 0.4,
                       DevelopmentCard.VictoryPoint: 1, DevelopmentCard.Knight: 2.0 / 3.0}

    def __init__(self, seed=None, timeout_seconds=5, weights=default_weights, filter_moves=lambda x, y: x):
        super().__init__(seed, timeout_seconds, self.weighted_probabilities_heuristic, filter_moves)
        self.weights = weights
        self._players_and_factors = None

    def weighted_probabilities_heuristic(self, s: CatanState):
        if self._players_and_factors is None:
            self._players_and_factors = [(self, len(s.players) - 1)] + [(p, -1) for p in s.players if p is not self]

        score = 0
        # noinspection PyTypeChecker
        for player, factor in self._players_and_factors:
            for location in s.board.get_locations_colonised_by_player(player):
                weight = self.weights[s.board.get_colony_type_at_location(location)]
                for dice_value in s.board.get_surrounding_dice_values(location):
                    score += s.probabilities_by_dice_values[dice_value] * weight * factor

            for road in s.board.get_roads_paved_by_player(player):
                weight = self.weights[Road.Paved]
                for dice_value in s.board.get_adjacent_to_path_dice_values(road):
                    score += s.probabilities_by_dice_values[dice_value] * weight * factor

            for development_card in {DevelopmentCard.VictoryPoint, DevelopmentCard.Knight}:
                weight = self.weights[development_card]
                score += self.get_unexposed_development_cards()[development_card] * weight * factor
        return score
