'''
Created on Aug 12, 2020

@author: Sascha Kuhnke
'''
from _collections import defaultdict


class Graph(object):
    """Data structure for an undirected graph."""

    def __init__(self, edges):
        
        self.graph_dict = defaultdict(set)
        self.num_selected_neighbours = {}
        self.add_edges(edges)


    def add_edges(self, edges):
        """Add edges to graph."""

        for node1, node2 in edges:
            self.add(node1, node2)
            self.num_selected_neighbours[node1] = 0
            self.num_selected_neighbours[node2] = 0


    def add(self, node1, node2):
        """Add edge between node1 and node2."""

        self.graph_dict[node1].add(node2)
        self.graph_dict[node2].add(node1)


    def remove(self, node):
        """Removes all references to node."""

        for __, edges in self.graph_dict.items():
            try:
                edges.remove(node)
            except KeyError:
                pass
        try:
            del self.graph_dict[node]
        except KeyError:
            pass


    def get_neighbors(self, node):
        """Returns all neighbors of node."""
        
        return self.graph_dict[node]
    
    
    def get_degree(self, node):
        """Returns the number of neighbors of node."""
        
        if node in self.graph_dict:
            degree = len(self.get_neighbors(node))
        else:
            degree = 0
        
        return degree
    
    
    def is_empty(self):
        """Returns true if the graph is empty."""
        
        return len(self.graph_dict) == 0
        

    def get_nodes(self):
        """Returns a list with all nodes of the graph."""
        
        return list(self.graph_dict)
    
    
    def get_random_node(self):
        """Returns a random node of the graph."""
        
        return list(self.graph_dict)[0]


    def __str__(self):
        """String representation of the graph."""
        
        return '{}({})'.format(self.__class__.__name__, dict(self.graph_dict))
    
    
    