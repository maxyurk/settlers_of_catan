from typing import Dict
from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from game.board import Resource
from math import ceil


class RandomPlayer(AbstractPlayer):

    def __init__(self, seed=None):
        super().__init__(seed)

    def choose_move(self, state: AbstractState):
        return self._random_choice(state.get_next_moves())

    def choose_resources_to_drop(self, state: AbstractState) -> Dict[Resource, int]:
        resources = [resource for resource, resource_count in self.resources.items() for _ in range(resource_count)]
        drop_count = ceil(len(resources) / 2)
        return self._random_choice(resources, drop_count, replace=False)
