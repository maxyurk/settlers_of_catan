import enum


class DevelopmentCard(enum.Enum):
    """Development-cards as specified in the game
    the value of each dev-card type is it's number of occurrences
    in the cards stack. i.e. the are 15 Knight cards in the stack
    """
    Knight = 15
    VictoryPoint = 5
    RoadBuilding = 2
    Monopoly = 2
    YearOfPlenty = 2
