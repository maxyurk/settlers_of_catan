import enum


class DevelopmentCard(enum.Enum):
    """Development-cards as specified in the game
    """
    Knight = 0         # 15 cards
    VictoryPoint = 1    # 5  cards
    RoadBuilding = 2    # 2  cards
    Monopoly = 3        # 2  cards
    YearOfPlenty = 4    # 2  cards

    @staticmethod
    def get_occurrences_in_deck_count(development_card):
        assert isinstance(development_card, DevelopmentCard)
        if development_card is DevelopmentCard.Knight:
            return 15
        elif development_card is DevelopmentCard.VictoryPoint:
            return 5
        return 2

    @staticmethod
    @property
    def deck_size():
        return 26

FirstDevCardIndex = DevelopmentCard.Knight.value
LastDevCardIndex = DevelopmentCard.YearOfPlenty.value
