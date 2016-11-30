from collections import Counter
from math import ceil
from typing import Dict

from algorithms.abstract_state import AbstractState
from game.resource import Resource
from players.abstract_player import AbstractPlayer


class RandomPlayer(AbstractPlayer):
    def __init__(self, seed=None):
        assert seed is None or (isinstance(seed, int) and seed > 0)
        super().__init__(seed)

    def choose_move(self, state: AbstractState):
        return self._random_choice(state.get_next_moves())

    def choose_resources_to_drop(self) -> Dict[Resource, int]:
        if sum(self.resources.values()) < 8:
            return {}

        resources = [resource for resource, resource_count in self.resources.items() for _ in range(resource_count)]
        drop_count = ceil(len(resources) / 2)
        return Counter(self._random_choice(resources, drop_count, replace=False))
