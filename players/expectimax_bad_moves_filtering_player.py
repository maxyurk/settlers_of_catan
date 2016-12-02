from players.expectimax_baseline_player import AlphaBetaPlayer
from players.filters import create_bad_robber_placement_filter


class AlphaBetaBadMovesFilteringPlayer(AlphaBetaPlayer):
    def __init__(self, seed=None, timeout_seconds=5, heuristic=None):
        super().__init__(seed, timeout_seconds, heuristic, create_bad_robber_placement_filter(self))
