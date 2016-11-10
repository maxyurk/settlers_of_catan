import abc
import enum
from algorithms import abstract_state
from algorithms.abstract_state import AbstractState
from game.board import Resource


class DevelopmentCard(enum.Enum):
    Knight = 1
    # TODO write the rest


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

    def add_development_card(self, card: DevelopmentCard):
        """
        add a development-card to this player's development-cards
        :param card: the development card to add
        :return: None
        """
        pass

    def remove_development_card(self, card: DevelopmentCard):
        """
        remove a development-card from this player's development-cards
        :param card: the development card to remove
        :return: None
        """
        pass

    def get_exposed_knights_count(self) -> int:
        """
        get the number of times this player used a "knight" development-card
        :return: int, the number of times "knight" card was used by the player
        """
        pass

    def has_resources_for_road(self):
        """
        indicate whether there are enough resources to pave a road
        :return: True if enough resources to pave a road, False otherwise
        """
        return (self.resources[Resource.Brick] >= 1 and
                self.resources[Resource.Lumber] >= 1)

    def has_resources_for_settlement(self):
        """
        indicate whether there are enough resources to build a settlement
        :return: True if enough resources to build a settlement, False otherwise
        """
        return (self.resources[Resource.Brick] >= 1 and
                self.resources[Resource.Lumber] >= 1 and
                self.resources[Resource.Wool] >= 1 and
                self.resources[Resource.Grain] >= 1)

    def has_resources_for_city(self):
        """
        indicate whether there are enough resources to build a city
        :return: True if enough resources to build a city, False otherwise
        """
        return (self.resources[Resource.Ore] >= 3 and
                self.resources[Resource.Grain] >= 2)

    def has_resources_for_development_card(self):
        """
        indicate whether there are enough resources to buy a development card
        :return: True if enough resources to buy a development card, False otherwise
        """
        return (self.resources[Resource.Ore] >= 1 and
                self.resources[Resource.Wool] >= 1 and
                self.resources[Resource.Grain] >= 1)
