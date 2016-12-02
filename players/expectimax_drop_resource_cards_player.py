from players.expectimax_baseline_player import AlphaBetaPlayer


class AlphaBetaDropResourceCardsPlayer(AlphaBetaPlayer):
    def __init__(self, seed=None, timeout_seconds=5):
        super().__init__(seed, timeout_seconds, self.drop_resource_cards_heuristic)

    def drop_resource_cards_heuristic(self, s):
        return -sum(self.resources.values())
