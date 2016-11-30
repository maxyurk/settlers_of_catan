from players.alpha_beta_player import AlphaBetaPlayer


class AlphaBetaMonteCarloPlayer(AlphaBetaPlayer):
    def default_heuristic(self, state):
        return float(state.get_scores_by_player()[self])

    def __init__(self, seed=None, timeout_seconds=5, heuristic=None, branching_factor=10):
        super().__init__(seed, timeout_seconds, heuristic, self.monte_carlo_filter)
        self.branching_factor = branching_factor

    def monte_carlo_filter(self, all_moves):
        if len(all_moves) <= self.branching_factor:
            return all_moves
        return self._random_choice(all_moves, self.branching_factor, False)
