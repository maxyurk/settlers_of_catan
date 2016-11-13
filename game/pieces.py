import enum


class Colony(enum.Enum):
    """the enumeration is also used to specify the points colony type is worth"""
    Uncolonised = 0
    Settlement = 1
    City = 2


class Road(enum.Enum):
    Paved = 1
    Unpaved = 2
