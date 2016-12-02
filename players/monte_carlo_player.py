from players.expectimax_baseline_player import AlphaBetaPlayer
from players.filters import create_monte_carlo_filter


class AlphaBetaMonteCarloPlayer(AlphaBetaPlayer):
    def __init__(self, seed=None, timeout_seconds=5, heuristic=None, branching_factor=10):
        super().__init__(seed, timeout_seconds, heuristic, create_monte_carlo_filter(seed, branching_factor))
