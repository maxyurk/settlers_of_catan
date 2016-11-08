import abc
from algorithms import AbstractState
from game.Board import Resource


class AbstractPlayer(abc.ABC):
    def __init__(self):
        self.resources = {r: 0 for r in Resource}

    @abc.abstractmethod
    def choose_move(self, state: AbstractState):
        """Implement decision mechanism here. the state is mutable and
        it's NOT a copy so make sure you 'UNMAKE' every move you make!
        :param state: Game state to help decide on a move
        :return: Selected AbstractMove to be made
        """
        pass

    def add_resource(self, resource_type: Resource, how_many=1):
        """
        As the name implies
        :param resource_type: Brick, Lumber, Wool, Grain, Ore, Desert
        :param how_many: number of resource units to add
        :return: None
        """
        self.resources[resource_type] += how_many

    def remove_resource(self, resource_type: Resource, how_many=1):
        """
        As the name implies
        :param resource_type: Brick, Lumber, Wool, Grain, Ore, Desert
        :param how_many:  number of resource units to remove
        :return: None
        """
        self.add_resource(resource_type, -how_many)

    def get_resource_count(self, resource_type: Resource):
        """
        As the name implies
        :param resource_type: Brick, Lumber, Wool, Grain, Ore, Desert
        :return: the number of resource units the player has
        """
        return self.resources[resource_type]
