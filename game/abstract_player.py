import abc
from typing import Dict
from algorithms.abstract_state import AbstractState, AbstractMove
from game.board import Resource
from game.development_cards import DevelopmentCard
from game.pieces import *
from train_and_test import logger
import numpy as np


class AbstractPlayer(abc.ABC):
    c = 0

    def __init__(self, seed=None):
        if seed is not None and not (0 <= seed < 1):
            logger.error('{parameter_name} should be in the range [0,1). treated as if no {parameter_name}'
                         ' was sent'.format(parameter_name=AbstractPlayer.__init__.__code__.co_varnames[1]))
            seed = None
        AbstractPlayer.c += 1
        numpy_seed = None if seed is None else int(seed * AbstractPlayer.c)
        self._random_choice = np.random.RandomState(seed=numpy_seed).choice

        self.resources = {r: 0 for r in Resource}
        self.pieces = {
            Colony.Settlement: 5,
            Colony.City: 4,
            Road.Paved: 15
        }
        self.unexposed_development_cards = {card: 0 for card in DevelopmentCard}
        self.exposed_development_cards = {card: 0 for card in DevelopmentCard}

    @abc.abstractmethod
    def choose_move(self, state: AbstractState) -> AbstractMove:
        """
        Implement decision mechanism here
        :param state: Game state to help decide on a move
        :return: Selected AbstractMove to be made
        """
        pass

    @abc.abstractmethod
    def choose_resources_to_drop(self) -> Dict[Resource, int]:
        """
        Implement here decision which resources to drop when the dice roll 7
        :param: state: Game state to help decide on a move
        :return: Dict[Resource, int] from resources to the number of resources to drop
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

    def update_resources(self, resources_amount: Dict[Resource, int], update_method):
        """
        update resources according to given histogram, with given method
        :param resources_amount: dictionary of the amounts of resources
        :param update_method: add/remove/anything you may imagine.
        i.e AbstractPlayer.add_resource/AbstractPlayer.add_resource
        :return: None
        """
        for resource, amount in resources_amount.items():
            update_method(self, resource, amount)

    def get_resource_count(self, resource_type: Resource):
        """
        As the name implies
        :param resource_type: Brick, Lumber, Wool, Grain, Ore, Desert
        :return: the number of resource units the player has
        """
        return self.resources[resource_type]

    def add_unexposed_development_card(self, card: DevelopmentCard):
        """
        increase by 1 the count of the development card 'card'
        :param card: the (probably) purchased development card
        :return: None
        """
        self.unexposed_development_cards[card] += 1

    def remove_unexposed_development_card(self, card: DevelopmentCard):
        """
        revert the side effects of 'add_unexposed_development_card' method
        :param card: the (probably) purchased development card to be "un-purchased"
        :return: None
        """
        self.unexposed_development_cards[card] -= 1

    def expose_development_card(self, card: DevelopmentCard):
        """
        only counts the number of exposed/unexposed cards!
        card effect not applied!
        :param card: the exposed development card
        :return: None
        """
        assert self.unexposed_development_cards[card] >= 1
        self.unexposed_development_cards[card] -= 1
        self.exposed_development_cards[card] += 1

    def un_expose_development_card(self, card: DevelopmentCard):
        """
        only counts the number of exposed/unexposed cards!
        card effect not reverted!
        :param card: the exposed development card to be un-exposed
        :return: None
        """
        assert self.exposed_development_cards[card] >= 1
        self.unexposed_development_cards[card] += 1
        self.exposed_development_cards[card] -= 1

    def get_unexposed_development_cards(self):
        for card_type, amount in self.unexposed_development_cards.items():
            for _ in range(amount):
                if card_type != DevelopmentCard.VictoryPoint:
                    yield card_type

    def get_exposed_knights_count(self) -> int:
        """
        get the number of times this player used a "knight" development-card
        :return: int, the number of times "knight" card was used by the player
        """
        return self.exposed_development_cards[DevelopmentCard.Knight]

    def get_victory_point_development_cards_count(self) -> int:
        """
        get the number of "victory points" development-card the player has
        :return: int, the number of times "victory points" development-card the player has
        """
        return self.unexposed_development_cards[DevelopmentCard.VictoryPoint]

    def has_unexposed_development_card(self):
        """
        indicate whether there is an unexposed development card
        victory point cards are not checked - they are never exposed
        :return: True if there is an unexposed development card, False otherwise
        """
        for c in DevelopmentCard:
            if c != DevelopmentCard.VictoryPoint and self.unexposed_development_cards[c] != 0:
                return True
        return False

    def can_pave_road(self):
        """
        indicate whether there are enough resources to pave a road
        :return: True if enough resources to pave a road, False otherwise
        """
        return (self.resources[Resource.Brick] >= 1 and
                self.resources[Resource.Lumber] >= 1 and
                self.pieces[Road.Paved] > 0)

    def can_settle_settlement(self):
        """
        indicate whether there are enough resources to build a settlement
        :return: True if enough resources to build a settlement, False otherwise
        """
        return (self.resources[Resource.Brick] >= 1 and
                self.resources[Resource.Lumber] >= 1 and
                self.resources[Resource.Wool] >= 1 and
                self.resources[Resource.Grain] >= 1 and
                self.pieces[Colony.Settlement] > 0)

    def can_settle_city(self):
        """
        indicate whether there are enough resources to build a city
        :return: True if enough resources to build a city, False otherwise
        """
        return (self.resources[Resource.Ore] >= 3 and
                self.resources[Resource.Grain] >= 2 and
                self.pieces[Colony.City] > 0)

    def has_resources_for_development_card(self):
        """
        indicate whether there are enough resources to buy a development card
        NOTE: unlike can_* methods, this method doesn't check there are needed
        pieces (in this case develpoment-cards in the deck)
        :return: True if enough resources to buy a development card, False otherwise
        """
        return (self.resources[Resource.Ore] >= 1 and
                self.resources[Resource.Wool] >= 1 and
                self.resources[Resource.Grain] >= 1)

    def remove_resources_for_road(self):
        assert self.can_pave_road()
        self.remove_resource(Resource.Brick)
        self.remove_resource(Resource.Lumber)

    def remove_resources_for_settlement(self):
        assert self.can_settle_settlement()
        self.remove_resource(Resource.Brick)
        self.remove_resource(Resource.Lumber)
        self.remove_resource(Resource.Wool)
        self.remove_resource(Resource.Grain)

    def remove_resources_for_city(self):
        assert self.can_settle_city()
        self.remove_resource(Resource.Ore, 3)
        self.remove_resource(Resource.Grain, 2)

    def remove_resources_for_development_card(self):
        assert self.has_resources_for_development_card()
        self.remove_resource(Resource.Ore)
        self.remove_resource(Resource.Wool)
        self.remove_resource(Resource.Grain)

    def add_resources_for_road(self):
        self.add_resource(Resource.Brick)
        self.add_resource(Resource.Lumber)

    def add_resources_for_settlement(self):
        self.add_resource(Resource.Brick)
        self.add_resource(Resource.Lumber)
        self.add_resource(Resource.Wool)
        self.add_resource(Resource.Grain)

    def add_resources_for_city(self):
        self.add_resource(Resource.Ore, 3)
        self.add_resource(Resource.Grain, 2)

    def add_resources_for_development_card(self):
        self.add_resource(Resource.Ore)
        self.add_resource(Resource.Wool)
        self.add_resource(Resource.Grain)
