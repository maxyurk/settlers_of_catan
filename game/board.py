import networkx
import enum
import random
from logging import warning
from itertools import chain
from typing import List, Tuple, Set, Dict

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
This map (W2 means wool  with the number 5 on it, L2 is lumber with 2 on it):

    O     O
 /    \ /    \
O      O      O
| (W5) | (L2) |
O      O      O
 \    / \    /
    O     O

In the DS, will be represented as follows:
The array:
 ---- ----
| W5 | L2 |
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


class Resource(enum.Enum):
    Brick = 1
    Lumber = 2
    Wool = 3
    Grain = 4
    Ore = 5
    Desert = 6


class Colony(enum.Enum):
    """the enumeration is also used to specify the points colony type is worth"""
    Uncolonised = 0
    Settlement = 1
    City = 2


class Road(enum.Enum):
    Paved = 1
    Unpaved = 2


Location = int
"""Location is a vertex in the graph
A place that can be colonised (with a settlement, and later with a city)
"""

Path = Tuple[int, int]
"""Path is an edge in the graph
A place that a road can be paved in
"""

Land = Tuple[Resource, int, int, List[Location]]
"""Land is an element in the lands array
A hexagon in the catan map, that has (in this order):
 -a resource type
 -a number between [2,12]
 -an id
 -Locations list (the locations around it)
"""


class Board:
    _player = 'player'
    _lands = 'lands'

    def __init__(self):
        self._create_and_shuffle_lands()
        self._create_graph()
        self._set_attributes()
        self._player_colonies_points = {}

    def get_all_settleable_locations(self) -> List[Location]:
        """
        get non-colonised (empty vertices) locations on map
        :return: list of locations on map that aren't colonised
        """
        return [v for v in self._roads_and_colonies.nodes()
                if not self.is_colonised(v)]

    def get_settleable_locations_by_player(self, player) -> List[Location]:
        """
        get non-colonised (empty vertices) locations on map that this player can settle
        :param player: the player to get settleable location by
        :return: list of locations on map that the player can settle locations on
        """
        non_colonised = [v for v in self._roads_and_colonies.nodes_iter()
                         if not self.is_colonised(v)]
        coloniseable = []
        for u in non_colonised:
            is_coloniseable = True
            one_hop_from_non_colonised = []
            for v in self._roads_and_colonies.neighbors(u):
                if self.is_colonised(v):
                    is_coloniseable = False
                    break
                if self.has_road_been_paved_by(player, (u, v)):
                    one_hop_from_non_colonised.append(v)
            if not is_coloniseable:
                continue

            is_coloniseable = False
            for v in one_hop_from_non_colonised:
                for w in self._roads_and_colonies.neighbors(v):
                    if w != u and self.has_road_been_paved_by(player, (v, w)):
                        is_coloniseable = True
                        break
            if is_coloniseable:
                coloniseable.append(u)
        return coloniseable

    def get_settlements_by_player(self, player) -> List[Location]:
        """
        get player's settlements on map that this player can settle with a city
        :param player: the player to get settlements
        :return: list of locations on map that the player can settle a city on
        """
        return [v for v in self._roads_and_colonies.nodes()
                if self._roads_and_colonies.node[v]['player'] == (player, Colony.Settlement)]

    def get_unpaved_paths_near_player(self, player) -> List[Path]:
        """
        get unpaved (empty edges) paths on map that this player can pave
        :param player: the player to get paths on map that he can pave
        :return: list of paths the player can pave a road in
        """

        roads = [e for e in self._roads_and_colonies.edges_iter()
                 if self.has_road_been_paved_by(player, e)]
        locations_non_colonised_by_other_players = [
            v for v in set(chain(*roads))
            if self._roads_and_colonies.node[v]['player'][0] in [player, None]]
        return [(u, v) for u in locations_non_colonised_by_other_players
                for v in self._roads_and_colonies.neighbors(u)
                if self._roads_and_colonies[u][v]['player'][0] is None]

    def get_settled_locations_by_player(self, player) -> List[Location]:
        """
        get the colonies owned by given player
        :param player: the player to get the colonies of
        :return: list of locations that have colonies of the given player
        """
        return [v for v in self._roads_and_colonies.nodes()
                if self._roads_and_colonies.node[v]['player'][0] == player]

    def get_surrounding_resources(self, location: Location) -> List[Land]:
        """
        get resources surrounding the settlement in this location
        :param location: the location to get the resources around
        :return: list of lands, which are a tuple of (Resource, number, id)
                    where Resource is the hexagon resource,
                    number is the number on the specified hexagon,
                    and the id is the number of the resource in the _lands array
        """

        return self._roads_and_colonies.node[location]['lands']

    def get_colonies_score(self, player) -> int:
        """
        get the colonies score-count of a single player
        that is the sum of points the player got for his colonies
        :param player: a player to get the colonies-score of
        :return: int, the score of the specified player
        """
        if player in self._player_colonies_points:
            return self._player_colonies_points[player]
        return 0

    def get_longest_road_length_of_player(self, player) -> int:
        """
        get the longest road length of specified player.
        NOTE: if player has less than 5 roads in total, it returns 0
        that's because it means he can't have the "longest-road" card anyways,
        so computing the longest road is unnecessary
        :param player: the player fir whom the longest road is calculated
        :return: the length of the longest road of specified player
        """
        roads_paved_by_player = [
            e for e in self._roads_and_colonies.edges_iter()
            if self.has_road_been_paved_by(player, e)]

        if len(roads_paved_by_player) < 5:
            return 0

        sub_graph_of_player = networkx.Graph(roads_paved_by_player)
        max_road_length = 0
        # TODO think if perhaps only some of the nodes can be checked
        # (perhaps those with degree 1 + those that are in a cycle, or something like that)
        for w in sub_graph_of_player.nodes():
            max_road_length = max(
                max_road_length,
                Board._compute_longest_road_length(sub_graph_of_player, w, set()))
        return max_road_length

    def get_players_to_resources_by_number(self, number: int) -> Dict:
        """
        get the resources that players get when the dice roll specified number
        :param number: the number the dice rolled
        :return: Dict[player, Dict[Resource, int]], a dictionary of plaers to
        the resources they should receive
        """
        lands_with_this_number = [land for land in self._lands if land[1] == number]

        players_to_resources = {player: {resource: 0 for resource in Resource}
                                for player in self._player_colonies_points.keys()}
        for land in lands_with_this_number:
            resource = land[0]
            for location in land[3]:
                if self.is_colonised(location):
                    player = self._roads_and_colonies.node[location]['player'][0]
                    colony = self._roads_and_colonies.node[location]['player'][1]
                    players_to_resources[player][resource] += colony.value
        return players_to_resources

    def set_location(self, player, location: Location, colony: Colony):
        """
        settle/unsettle given colony type in given location by given player
        NOTE that if the colony type is Colony.Uncolonised, then the player is irrelevant
        if player is None or colony is Colony.Uncolonised,
        the updated (player, colony) will be: (None ,Colony.Uncolonised)
        :param player: the player to settle/unsettle a settlement of
        :param location: the location to put the settlement on
        :param colony: the colony type to put (settlement/city)
        :return: None
        """
        if ((colony == Colony.Uncolonised and player is not None) or
                (player is None and colony != Colony.Uncolonised)):
            warning(' {} bad arguments: ({}, {}) is not a logical combination.'
                    ' Treated as (None, Colony.Uncolonised)'
                    .format(Board.set_location.__name__, player, colony))
            player = None
            colony = Colony.Uncolonised

        if player not in self._player_colonies_points:
            self._player_colonies_points[player] = 0
        previous_colony = self._roads_and_colonies.node[location]['player'][1]
        self._player_colonies_points[player] -= previous_colony.value
        self._player_colonies_points[player] += colony.value

        self._roads_and_colonies.node[location]['player'] = (player, colony)

    def set_path(self, player, path: Path, road: Road):
        """
        pave/un-pave road in given location by given player
        NOTE that if the road type is Road.Unpaved, then the player is irrelevant
        :param player: the player that paves/un-paves the road
        :param path: the path on the map to pave/un-pave the road at
        :param road: road type. Road.Paved to pave, Road.Unpaved to un-pave
        :return: None
        """
        if ((road == Road.Unpaved and player is not None) or
                (player is None and road != Road.Unpaved)):
            warning(' {} bad arguments: ({}, {}) is not a logical combination.'
                    ' Treated as (None, Road.Unpaved)'
                    .format(Board.set_path.__name__, player, road))
            player = None
            road = Road.Unpaved
        self._roads_and_colonies[path[0]][path[1]]['player'] = (player, road)

    def is_colonised(self, location: Location):
        """
        indicate whether the specified location is colonised
        :param location: the location to check
        :return: True if specified location is colonised, false otherwise
        """
        return self._roads_and_colonies.node[location]['player'][0] is not None

    def has_road_been_paved_by(self, player, path: Path):
        """
        indicate whether a road has been paved in specified location by specified player
        :param player: the player to check if he paved a road in that path
        :param path: the path to check if the player paved a road at
        :return: True if road on that path has been paved by given player, False otherwise
        """
        return self._roads_and_colonies[path[0]][path[1]]['player'][0] == player

    _vertices_rows = [
        [i for i in range(0, 3)],
        [i for i in range(3, 7)],
        [i for i in range(7, 11)],
        [i for i in range(11, 16)],
        [i for i in range(16, 21)],
        [i for i in range(21, 27)],
        [i for i in range(27, 33)],
        [i for i in range(33, 38)],
        [i for i in range(38, 43)],
        [i for i in range(43, 47)],
        [i for i in range(47, 51)],
        [i for i in range(51, 54)]
    ]
    _vertices = [v for vertices_row in _vertices_rows for v in vertices_row]

    @staticmethod
    def _compute_longest_road_length(g: networkx.Graph, u: Location, visited: Set[Path]):
        max_road_length = 0
        for v in g.neighbors(u):
            if (u, v) in visited or (v, u) in visited:
                continue
            visited.add((u, v))
            max_road_length = max(
                max_road_length,
                1 + Board._compute_longest_road_length(g, v, visited))
            visited.remove((u, v))
        return max_road_length

    def _create_and_shuffle_lands(self):
        land_numbers = [2, 12] + [i for i in range(3, 12) if i != 7] * 2
        land_resources = [Resource.Lumber, Resource.Wool, Resource.Grain] * 4 + \
                         [Resource.Brick, Resource.Ore] * 3

        random.shuffle(land_numbers)
        random.shuffle(land_resources)

        land_resources.append(Resource.Desert)
        land_numbers.append(0)

        ids = range(len(land_resources))

        locations = [[] for _ in range(len(land_resources))]

        lands = zip(land_resources, land_numbers, ids, locations)
        self._lands = [land for land in lands]

    def _create_graph(self):
        self._roads_and_colonies = networkx.Graph()
        self._roads_and_colonies.add_nodes_from(Board._vertices)
        self._roads_and_colonies.add_edges_from(Board._create_edges())

    @staticmethod
    def _create_edges():
        edges = []
        for i in range(5):
            Board._create_row_edges(edges, i, i + 1, Board._vertices_rows, i % 2 == 0)
            Board._create_row_edges(edges, -i - 1, -i - 2, Board._vertices_rows, i % 2 == 0)
        Board._create_odd_rows_edges(edges, Board._vertices_rows[5], Board._vertices_rows[6])
        return edges

    @staticmethod
    def _create_row_edges(edges, i, j, vertices_rows, is_even_row):
        if is_even_row:
            Board._create_even_rows_edges(edges, vertices_rows[j], vertices_rows[i])
        else:
            Board._create_odd_rows_edges(edges, vertices_rows[j], vertices_rows[i])

    @staticmethod
    def _create_odd_rows_edges(edges, first_row, second_row):
        for edge in zip(second_row, first_row):
            edges.append(edge)

    @staticmethod
    def _create_even_rows_edges(edges, larger_row, smaller_row):
        for i in range(len(smaller_row)):
            edges.append((smaller_row[i], larger_row[i]))
            edges.append((smaller_row[i], larger_row[i + 1]))

    def _set_attributes(self):
        vertices_to_lands = self._create_vertices_to_lands_mapping()
        self._set_vertices_attributes(vertices_to_lands)
        self._set_edges_attributes(vertices_to_lands)
        self._set_lands_attributes(vertices_to_lands)

    def _create_vertices_to_lands_mapping(self):
        land_rows = [
            self._lands[0:3],
            self._lands[3:7],
            self._lands[7:12],
            self._lands[12:16],
            self._lands[16:19]
        ]
        vertices_rows_per_land_row = [
            Board._vertices_rows[0:3] + [Board._vertices_rows[3][1:-1]],
            Board._vertices_rows[2:5] + [Board._vertices_rows[5][1:-1]],
            Board._vertices_rows[4:8],
            [Board._vertices_rows[6][1:-1]] + Board._vertices_rows[7:10],
            [Board._vertices_rows[8][1:-1]] + Board._vertices_rows[9:12]
        ]
        vertices_map = {vertex: [] for vertex in Board._vertices}
        for vertices_rows, land_row in zip(vertices_rows_per_land_row, land_rows):
            Board._create_top_vertex_mapping(vertices_map, vertices_rows[0], land_row)
            Board._create_middle_vertex_mapping(vertices_map, vertices_rows[1], land_row)
            Board._create_middle_vertex_mapping(vertices_map, vertices_rows[2], land_row)
            Board._create_top_vertex_mapping(vertices_map, vertices_rows[3], land_row)
        return vertices_map

    def _set_vertices_attributes(self, vertices_to_lands):
        networkx.set_node_attributes(self._roads_and_colonies, 'lands', vertices_to_lands)
        vertices_to_players = {v: (None, Colony.Uncolonised) for v in Board._vertices}
        networkx.set_node_attributes(self._roads_and_colonies, 'player', vertices_to_players)

    def _set_edges_attributes(self, vertices_to_lands):
        for edge in self._roads_and_colonies.edges_iter():
            lands_intersection = [land for land in vertices_to_lands[edge[0]]
                                  if land in vertices_to_lands[edge[1]]]
            edge_attributes = self._roads_and_colonies[edge[0]][edge[1]]
            edge_attributes['lands'] = lands_intersection
            edge_attributes['player'] = (None, Road.Unpaved)

    @staticmethod
    def _set_lands_attributes(vertices_to_lands):
        for location, lands in vertices_to_lands.items():
            for land in lands:
                land[3].append(location)

    @staticmethod
    def _create_top_vertex_mapping(vertices_map, vertices, lands):
        for vertex, land in zip(vertices, lands):
            vertices_map[vertex].append(land)

    @staticmethod
    def _create_middle_vertex_mapping(vertices_map, vertices, lands):
        vertices_map[vertices[0]].append(lands[0])
        vertices_map[vertices[-1]].append(lands[-1])

        for i in range(1, len(vertices[1:-1]) + 1):
            vertices_map[vertices[i]].append(lands[i - 1])
            vertices_map[vertices[i]].append(lands[i])
