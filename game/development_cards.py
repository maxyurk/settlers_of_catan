import enum


class DevelopmentCard(enum.Enum):
    """Development-cards as specified in the game
    """
    Knight = 0          # 15 cards
    VictoryPoint = 1    # 5  cards
    RoadBuilding = 2    # 2  cards
    Monopoly = 3        # 2  cards
    YearOfPlenty = 4    # 2  cards
FirstDevCardIndex = DevelopmentCard.Knight.value
LastDevCardIndex = DevelopmentCard.YearOfPlenty.value
