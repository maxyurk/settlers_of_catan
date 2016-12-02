from players.expectimax_weighted_probabilities_player import AlphaBetaWeightedProbabilitiesPlayer
from players.filters import create_monte_carlo_filter


class AlphaBetaMonteCarloPlayer(AlphaBetaWeightedProbabilitiesPlayer):
    def __init__(self, seed=None, timeout_seconds=5, branching_factor=10):
        super().__init__(seed=seed,
                         timeout_seconds=timeout_seconds,
                         filter_moves=create_monte_carlo_filter(seed, branching_factor))
