from players.expectimax_baseline_player import AlphaBetaPlayer
from players.filters import create_bad_robber_placement_and_monte_carlo_filter


class AlphaBetaBothFiltersPlayer(AlphaBetaPlayer):
    def __init__(self, seed=None, timeout_seconds=5, heuristic=None, branching_factor=10):
        super().__init__(seed, timeout_seconds, heuristic,
                         create_bad_robber_placement_and_monte_carlo_filter(seed, self, branching_factor))
