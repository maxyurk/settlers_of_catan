import numpy
import networkx
import enum
from typing import List


"""
Structure
---------
The board is represented as follows:
It consists of two parts:
a graph that represents the items around the hexagon, and an array of the hexagons.
The graph will hold the "shape":
 -each vertex will be a place a house can be built in
 -each edge will be a place a road can be paved at
THe array will hold the "data":
 -each item will be a hexagon, that consists of:
    --the element (Wheat, Metal, Clay or Wood)
    --the number (2-12)
    --Is there a burglar on the hexagon or not
each edge & vertex in the graph will be bi-directionally linked to it's hexagons, for easy traversal

Example
-------
This map (W2 means wheat with the number 5 on it, M2 is metal with 2 on it):

    O     O
 /    \ /    \
O      O      O
| (W5) | (M2) |
O      O      O
 \    / \    /
    O     O

In the DS, will be represented as follows:
The array:
 ---- ----
| W5 | M2 |
 ---- ----
The graph will have the shape of the map, where the edges are \,/,|
and the vertices are O.
    O     O
 /    \ /    \
O      O      O
|      |      |
O      O      O
 \    / \    /
    O     O

"""
number_of_hexagons = 19


class Resource(enum.Enum):
    Wood = 1
    Steel = 2
    Clay = 3
    Sheep = 4


class Settlement:
    def __init__(self):
        pass

    def get_surrounding_resources(self) -> List[Resource]:
        """get resources surrounding this settlement"""
        pass


class Road:
    def __init__(self):
        pass


class Board:
    def __init__(self):
        self.roads_and_villages = networkx.Graph()
        self.resources = numpy.array([i for i in range(number_of_hexagons)])

    def get_all_settleable_locations(self) -> List[Settlement]:
        """get non-colonised (empty vertices) locations on map"""
        pass

    def get_settleable_locations_by_player(self, player) -> List[Settlement]:
        """get non-colonised (empty vertices) locations on map that this player can settle"""
        pass

    def get_roads_near_player(self, player) -> List[Road]:
        """get unpaved (empty edges) roads on map that this player can pave"""
        pass
