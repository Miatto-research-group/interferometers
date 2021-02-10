from typing import Dict, Tuple
from collections.abc import MutableMapping
import numpy as np

from utils import approx_tree_cost

class State(MutableMapping):
    """
    A dictionary that represents a pure quantum state.
    It stores ket:amplitude pairs and supports a `normalize()` method.
    """

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    # def __hash__(self):
    #     return hash(self.store)

    def __iter__(self):
        return iter(self.store)
    
    def __len__(self):
        return len(self.store)

    def normalize(self):
        norm = sum(abs(s)**2 for s in self.store.values())
        for k in self.store:
            self.store[k] /= np.sqrt(norm)

    def __repr__(self):
        return str(self.store)


class IOSpec:
    """
    Input-output specification.
    Supports generating all Input/Output pairs and their amplitude
    """
    def __init__(self, input_state:State, output_state:State):
        if len(set([sum(ket) for ket in input_state.keys()])) > 1:
            raise ValueError("""The input state spans more than one multiplet.
        Solution: separate the required input-output relations per multiplet and submit them as different requirements.""")
        if len(set([sum(ket) for ket in output_state.keys()])) > 1:
            raise ValueError("""The input state spans more than one multiplet.
        Solution: separate the required input-output relations per multiplet and submit them as different requirements.""")
        if sum(list(input_state.keys())[0]) != sum(list(output_state.keys())[0]):
            raise ValueError("""This spec does not conserve photon number.
        Solution: separate the required input-output relations per multiplet and submit them as different requirements.""")
        if len(set([len(ket) for ket in input_state.keys()])) > 1:
            raise ValueError("not all input states span the same number of modes")
        if len(set([len(ket) for ket in output_state.keys()])) > 1:
            raise ValueError("not all output states span the same number of modes")
        self.input = input_state
        self.output = output_state
        cost_of_building_input  = approx_tree_cost(build_patterns=list(self.input.keys()), scan_patterns=list(self.output.keys()))
        cost_of_building_output = approx_tree_cost(build_patterns=list(self.output.keys()), scan_patterns=list(self.input.keys()))
        if cost_of_building_input < cost_of_building_output:
            self.building_output = False
            self.building_input = True
            self.paths = [(ket_in, ket_out, self.input[ket_in]*self.output[ket_out]) for ket_out in output_state for ket_in in input_state]
        else:
            self.building_output = True
            self.building_input = False
            self.paths = [(ket_out, ket_in, self.input[ket_in]*self.output[ket_out]) for ket_out in output_state for ket_in in input_state]

    @property
    def photons(self):
        return sum(list(self.input.keys())[0])

    @property
    def modes(self):
        return len(list(self.input.keys())[0])



class Requirements:
    """
    Summary of all the IO specifications for a given input state with corresponding probabilities
    """

    def __init__(self, specs:Dict[IOSpec,float]):
        if len(set([io.modes for io in specs.keys()])) > 1:
            raise ValueError('not all input-output relations span the same number of modes')
        self.specs = specs 

    @property
    def modes(self):
        return list(self.specs.keys())[0].modes

    