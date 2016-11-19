import enum
import random
import matplotlib.pyplot
import networkx
from itertools import chain
from operator import itemgetter
from typing import List, Tuple, Set, Dict
from algorithms.tree_diameter import tree_diameter

from game.pieces import Colony, Road
from train_and_test.logger import logger

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
    --Is there a robber on the hexagon or not
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


@enum.unique
class Resource(enum.Enum):
    Brick = 1
    Lumber = 2
    Wool = 3
    Grain = 4
    Ore = 5


@enum.unique
class Harbor(enum.Enum):
    """
    Harbor types. Harbors are locations one can exchange resources in.
    specific harbors at 1:2 ratio (1 specific harbor per Resource type)
    generic at 1:3 ratio (4 generic harbors)
    note that the enum numbers correspond to the Resource enum, for easy mapping between the two
    """
    HarborGeneric = 0
    HarborBrick = Resource.Brick.value
    HarborLumber = Resource.Lumber.value
    HarborWool = Resource.Wool.value
    HarborGrain = Resource.Grain.value
    HarborOre = Resource.Ore.value


Location = int
"""Location is a vertex in the graph
A place that can be colonised (with a settlement, and later with a city)
"""

Path = Tuple[Location, Location]
"""Path is an edge in the graph
A place that a road can be paved in
"""

RolledDiceNumber = int
ID = int
Land = Tuple[Resource, RolledDiceNumber, ID, List[Location]]
"""Land is an element in the lands array
A hexagon in the catan map, that has (in this order):
 -a resource type
 -a number between [2,12]
 -an id
 -Locations list (the locations around it)
"""


def path_key(edge):
    return min(edge) * 100 + max(edge)


class Board:
    player = 'p'
    lands = 'l'
    harbor = 'h'

    def __init__(self, seed: int = None):
        """
        Board of the game settlers of catan
        :param seed: optional parameter. send the same number in the range [0,1) to get the same map
        """
        if seed is not None and not (0 <= seed < 1):
            logger.error('{parameter_name} should be in the range [0,1). treated as if no {parameter_name}'
                         ' was sent'.format(parameter_name=Board.__init__.__code__.co_varnames[1]))
            seed = None

        self._seed = seed
        self._player_colonies_points = {}
        self._players_by_roads = {}

        self._create_and_shuffle_lands()
        self._create_graph()
        self._set_attributes()
        self._create_harbors()

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
        non_colonised = [v for v in self._roads_and_colonies.nodes()
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
        unlike get_settled_locations_by_player, this method returns only the
        settlements' locations. It doesn't return cities locations
        :param player: the player to get settlements
        :return: list of locations on map that the player can settle a city on
        """
        return [v for v in self._roads_and_colonies.nodes()
                if self._roads_and_colonies.node[v][Board.player] == (player, Colony.Settlement)]

    def get_settled_locations_by_player(self, player) -> List[Location]:
        """
        get the colonies owned by given player
        unlike get_settlements_by_player, this method returns both the
        settlements' and the cities' locations
        :param player: the player to get the colonies of
        :return: list of locations that have colonies of the given player
        """
        return [v for v in self._roads_and_colonies.nodes() if self.is_colonised_by(player, v)]

    def get_unpaved_paths_near_player(self, player) -> List[Path]:
        """
        get unpaved (empty edges) paths on map that this player can pave
        :param player: the player to get paths on map that he can pave
        :return: list of paths the player can pave a road in
        """
        roads = [e for e in self._roads_and_colonies.edges()
                 if self.has_road_been_paved_by(player, e)]
        uncolonised_by_other_players = [v for v in set(chain(*roads))
                                        if self.is_colonised_by(player, v) or not self.is_colonised(v)]
        return [(u, v) for u in uncolonised_by_other_players
                for v in self._roads_and_colonies.neighbors(u)
                if self.has_road_been_paved_by(None, (u, v))]

    def get_surrounding_resources(self, location: Location) -> List[Land]:
        """
        get resources surrounding the settlement in this location
        :param location: the location to get the resources around
        :return: list of lands, which are a tuple of (Resource, number, id)
                    where Resource is the hexagon resource,
                    number is the number on the specified hexagon,
                    and the id is the number of the resource in the _lands array
        """

        return self._roads_and_colonies.node[location][Board.lands]

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
        NOTE: if player has less than 5 roads in total, it returns 4
        that's because it means he can't have the "longest-road" card anyways,
        so computing the longest road is unnecessary
        :param player: the player fir whom the longest road is calculated
        :return: max(4, the length of the longest road of specified player)
        """
        roads_paved_by_player = [e for e in self._roads_and_colonies.edges()
                                 if self.has_road_been_paved_by(player, e)]

        roads_threshold = 4
        if len(roads_paved_by_player) <= roads_threshold:
            return roads_threshold
        sub_graph_of_player = networkx.Graph(roads_paved_by_player)
        max_road_length = roads_threshold

        # TODO think if perhaps only some of the nodes can be checked
        # ------
        # IDEA 1
        # ------
        # perhaps check only those with degree 1 + those that are in a cycle
        # ------
        # IDEA 2 - implemented
        # ------
        # something like:
        # longest_in_graph = 0
        # connect_components = sorted(graph.connect_components, by_number_of_edges_in_component)
        # for each component in connected_component:
        #     if len(component.get_edges()) <= longest_in_graph:
        #         break
        #     longest = 0
        #     for each edge in component:
        #         if longest == len(component.get_edges()):
        #             break  # that's the best in this component
        #         longest = max(longest, compute_longest(edge))
        #     longest_in_graph = max(longest, longest_in_graph)
        # ------
        # IDEA 3
        # ------
        # maintain subgraphs to avoid the copy overhead
        # (not possible because the sub-graph in networkx is induced from nodes, not edges
        # could be implemented by removing edges and then putting them back.
        # not sure it's better though)
        # ------
        # IDEA 4
        # ------
        # maintain roads paved by player lists to avoid repeated graph traversals
        # (this may be useful in other places in the code where edges are iterated)
        # ------
        # IDEA 5
        # ------
        # for each component, check if DAG. if DAG, finds longest road
        # ------
        # IDEA 6
        # ------
        # use graph-tool library, that claims to have better performance
        connected_components_and_edge_count_sorted_by_edge_count = sorted(
            ((g, g.size()) for g in networkx.connected_component_subgraphs(sub_graph_of_player, copy=False)),
            key=itemgetter(1), reverse=True)

        for g, edges_count in connected_components_and_edge_count_sorted_by_edge_count:
            if edges_count <= max_road_length:
                return max_road_length
            if networkx.is_tree(g):
                max_road_length = max(max_road_length, tree_diameter(g) - 1)
            else:
                for w in g.nodes():
                    if networkx.degree(g, w) == 2:
                        continue
                    max_road_length = max(max_road_length, Board._compute_longest_road_length(g, w, set()))
                    if max_road_length == edges_count:
                        return max_road_length
        return max_road_length

    def get_players_to_resources_by_number(self, number: RolledDiceNumber) -> Dict:
        """
        get the resources that players get when the dice roll specified number
        :param number: the number the dice rolled
        :return: Dict[player, Dict[Resource, int]], a dictionary of plaers to
        the resources they should receive
        """
        assert 2 <= number <= 12 and number != 7
        lands_with_this_number = [land for land in self._lands
                                  if land[1] == number and self._robber_land != land]
        players_to_resources = {player: {resource: 0 for resource in Resource}
                                for player in self._player_colonies_points.keys()}
        for land in lands_with_this_number:
            resource = land[0]
            for location in land[3]:
                if self.is_colonised(location):
                    player = self._roads_and_colonies.node[location][Board.player][0]
                    colony = self.get_colony_type_at_location(location)
                    players_to_resources[player][resource] += colony.value
        return players_to_resources

    def get_colony_type_at_location(self, location: Location) -> Colony:
        return self._roads_and_colonies.node[location][Board.player][1]

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
        assert not (player is None and colony != Colony.Uncolonised)

        if player not in self._player_colonies_points:
            self._player_colonies_points[player] = 0
        previous_colony = self.get_colony_type_at_location(location)
        self._player_colonies_points[player] -= previous_colony.value
        self._player_colonies_points[player] += colony.value

        if colony == Colony.Uncolonised:
            player = None
        self._roads_and_colonies.node[location][Board.player] = (player, colony)

        if __debug__:
            sum_of_settlements_and_cities_points = 0
            for v in self._roads_and_colonies.nodes():
                sum_of_settlements_and_cities_points += self.get_colony_type_at_location(v).value

            sum_of_points = 0
            for points in self._player_colonies_points.values():
                sum_of_points += points

            assert sum_of_points == sum_of_settlements_and_cities_points

    def set_path(self, player, path: Path, road: Road):
        """
        pave/un-pave road in given location by given player
        NOTE that if the road type is Road.Unpaved, then the player is irrelevant
        :param player: the player that paves/un-paves the road
        :param path: the path on the map to pave/un-pave the road at
        :param road: road type. Road.Paved to pave, Road.Unpaved to un-pave
        :return: None
        """
        assert not (player is None and road != Road.Unpaved)
        if road == Road.Unpaved:
            player = None
        self._roads_and_colonies[path[0]][path[1]][Board.player] = (player, road)
        self._players_by_roads[path_key(path)] = player

    def get_robber_land(self) -> Land:
        """
        get the land where the robber currently lays
        :return: Land, where the robber is located
        """
        return self._robber_land

    def set_robber_land(self, land: Land):
        """
        set the land where the robber lays
        :param land: the land where the robber will be located
        :return: None
        """
        self._robber_land = land

    def is_colonised(self, location: Location) -> bool:
        """
        indicate whether the specified location is colonised
        :param location: the location to check
        :return: True if specified location is colonised, false otherwise
        """
        return not self.is_colonised_by(None, location)

    def is_colonised_by(self, player, location: Location) -> bool:
        """
        indicate whether the specified location is colonised by specified player
        :param location: the location to check
        :param player: the player to check
        :return: True if specified location is colonised by player, false otherwise
        """
        return self._roads_and_colonies.node[location][Board.player][0] is player

    def has_road_been_paved_by(self, player, path: Path):
        """
        indicate whether a road has been paved in specified location by specified player
        :param player: the player to check if he paved a road in that path
        :param path: the path to check if the player paved a road at
        :return: True if road on that path has been paved by given player, False otherwise
        """
        return self._players_by_roads[path_key(path)] is player

    def plot_map(self, file_name='tmp.jpg'):
        vertices_by_players = self.get_locations_by_players()
        edges_by_players = self.get_paths_by_players()

        # NOTE: this implementation works, but for some reason
        # the plotted graph is sometimes scattered
        #
        # colors = ['m', 'g', 'b', 'r']
        # for player in vertices_by_players.keys():
        #     color = 'grey'
        #     if player is not None:
        #         color = colors.pop()
        #     networkx.draw_spectral(self._roads_and_colonies,
        #                            with_labels=True,
        #                            nodelist=vertices_by_players[player],
        #                            node_color=color,
        #                            edgelist=edges_by_players[player],
        #                            edge_color=color)
        #     print('{} is {}'.format(player, color))
        # matplotlib.pyplot.show()

        g = networkx.nx_agraph.to_agraph(self._roads_and_colonies)

        colors = ['orange', 'brown', 'blue', 'red']
        for player in vertices_by_players.keys():
            color = 'grey'
            if player is not None:
                color = colors.pop()
            for vertex in vertices_by_players[player]:
                g.get_node(vertex).attr['color'] = color
                g.get_node(vertex).attr['fillcolor'] = color
                g.get_node(vertex).attr['style'] = 'filled'
                g.get_node(vertex).attr['fontsize'] = 25
                g.get_node(vertex).attr['fontname'] = 'times-bold'
                if self.get_colony_type_at_location(vertex) == Colony.City:
                    g.get_node(vertex).attr['shape'] = 'box'
                else:
                    g.get_node(vertex).attr['shape'] = 'circle'
                g.get_node(vertex).attr['penwidth'] = 2
            for u, v in edges_by_players[player]:
                g.get_edge(u, v).attr['color'] = color
                g.get_edge(u, v).attr['penwidth'] = 2
        g.layout()
        g.draw(file_name)

    def get_paths_by_players(self):
        """
        get players to paths dictionary
        my_board.get_paths_by_players()[None] == all the unpaved paths
        :return: Dict[Player, List[Location]]
        """
        edges_by_players = {
            player: [e for e in self._roads_and_colonies.edges() if self.has_road_been_paved_by(player, e)]
            for player in self._player_colonies_points.keys()
            }
        edges_by_players[None] = [e for e in self._roads_and_colonies.edges()
                                  if self.has_road_been_paved_by(None, e)]
        return edges_by_players

    def get_locations_by_players(self):
        """
        get players to locations dictionary
        my_board.get_locations_by_players()[None] == all the non-colonised locations
        :return: Dict[Player, List[Location]]
        """
        vertices_by_players = {
            player: [v for v in self._roads_and_colonies.nodes() if self.is_colonised_by(player, v)]
            for player in self._player_colonies_points.keys()
            }
        vertices_by_players[None] = [v for v in self._roads_and_colonies.nodes() if not self.is_colonised(v)]
        return vertices_by_players

    def is_player_on_harbor(self, player, harbor: Harbor):
        """
        indicate whether specified player is settled on a location with specified harbor_type
        :param player: the player to check if he's settled on a location with given harbor-type
        :param harbor: harbor-type to check if given player is settled nearby
        :return: True if player settled near the harbor-type, false otherwise
        """
        for location in self._locations_by_harbors[harbor]:
            if self.is_colonised_by(player, location):
                return True
        return False

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
        self._shuffle(land_numbers)
        self._shuffle(land_resources)

        land_resources.append(None)
        land_numbers.append(0)

        ids = range(len(land_resources))

        locations = [[] for _ in range(len(land_resources))]

        lands = zip(land_resources, land_numbers, ids, locations)
        self._lands = [land for land in lands]
        self._robber_land = self._lands[-1]
        # Note how the robber location relies on the fact that the last
        # land in the list is the desert

    def _create_graph(self):
        self._roads_and_colonies = networkx.Graph()
        self._roads_and_colonies.add_nodes_from(Board._vertices)
        self._roads_and_colonies.add_edges_from(Board._create_edges())

    def _create_harbors(self):
        harbors = [Harbor.HarborBrick, Harbor.HarborLumber, Harbor.HarborWool, Harbor.HarborGrain, Harbor.HarborOre]
        self._shuffle(harbors)
        edges = self._get_harbors_edges()

        self._locations_by_harbors = {harbor: list(edge) for harbor, edge in zip(harbors, edges[0:len(harbors)])}
        self._locations_by_harbors[Harbor.HarborGeneric] = list(chain(*edges[len(harbors):len(edges)]))

    def _get_harbors_edges(self):
        wrapping_edges = self._get_wrapping_edges()
        offsets = [4] * 3 + [3] * 6
        self._shuffle(offsets)
        indices = [offsets[0] - 2]
        for i in range(1, len(offsets)):
            indices.append(offsets[i] + indices[i - 1])
        return [wrapping_edges[i] for i in indices]

    def _get_wrapping_edges(self):
        u, v = (3, 0)
        wrapping_edges = [(u, v)]
        while (u, v) != (7, 3):
            assert len([w for w in self._roads_and_colonies.neighbors(v)
                        if w != u and self._is_wrapping_edge(v, w)]) == 1
            w = next(w for w in self._roads_and_colonies.neighbors(v) if w != u and self._is_wrapping_edge(v, w))
            wrapping_edges.append((v, w))
            u, v = v, w
        return wrapping_edges

    def _is_wrapping_edge(self, u, v):
        return len(self._roads_and_colonies[u][v][Board.lands]) == 1

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
        networkx.set_node_attributes(self._roads_and_colonies, Board.lands, vertices_to_lands)
        vertices_to_players = {v: (None, Colony.Uncolonised) for v in Board._vertices}
        networkx.set_node_attributes(self._roads_and_colonies, Board.player, vertices_to_players)

    def _set_edges_attributes(self, vertices_to_lands):
        for edge in self._roads_and_colonies.edges():
            lands_intersection = [land for land in vertices_to_lands[edge[0]]
                                  if land in vertices_to_lands[edge[1]]]
            edge_attributes = self._roads_and_colonies[edge[0]][edge[1]]
            edge_attributes[Board.lands] = lands_intersection
            edge_attributes[Board.player] = (None, Road.Unpaved)
            self._players_by_roads[path_key(edge)] = None

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

    def _shuffle(self, sequence):
        assert self._seed is None or 0 <= self._seed < 1
        random.shuffle(sequence, None if self._seed is None else lambda: self._seed)
