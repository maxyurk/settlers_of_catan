from players.expectimax_baseline_player import ExpectimaxPlayer
from players.filters import create_bad_robber_placement_filter


class ExpectimaxBadMovesFilteringPlayer(ExpectimaxPlayer):
    def __init__(self, seed=None, timeout_seconds=5, heuristic=None):
        super().__init__(seed, timeout_seconds, heuristic, create_bad_robber_placement_filter(self))
