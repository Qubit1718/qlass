#TODO: add some tests for the helper functions and hamiltonian functions

from qlass.utils.utils import compute_energy, get_probabilities, qubit_state_marginal, is_qubit_state
import perceval as pcvl

import warnings
warnings.simplefilter('ignore')
warnings.filterwarnings('ignore')

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import TwoLocal
from perceval.algorithm import Sampler

from qlass import compile
from qlass.vqe import VQE, le_ansatz, custom_unitary_ansatz
from qlass.quantum_chemistry import LiH_hamiltonian

def test_compute_energy():
    # test case 1
    pauli_bin = (0, 0, 0)
    res = {(0, 0, 0): 0.5, (0, 0, 1): 0.3, (0, 1, 0): 0.1, (1, 0, 0): 0.1}
    assert compute_energy(pauli_bin, res) == float(1.0)

    # test case 2
    pauli_bin = (0, 0, 1)
    res = {(0, 0, 0): 0.5, (0, 0, 1): 0.3, (0, 1, 0): 0.1, (1, 0, 0): 0.1}
    assert compute_energy(pauli_bin, res) == float(0.4)

    # test case 3
    pauli_bin = (0, 1, 0)
    res = {(0, 0, 0): 0.5, (0, 0, 1): 0.3, (0, 1, 0): 0.1, (1, 0, 0): 0.1}
    assert compute_energy(pauli_bin, res) == float(0.8)

    # test case 4
    pauli_bin = (1, 0, 0)
    res = {(0, 0, 0): 0.45, (0, 0, 1): 0.23, (0, 1, 0): 0.1, (1, 0, 0): 0.32}
    assert compute_energy(pauli_bin, res) == float(0.46)

def test_get_probabilities():
    # test case 1
    samples = [(0, 0, 0), (0, 0, 1), (0, 0, 0), (0, 1, 0), (0, 0, 1)]
    assert get_probabilities(samples) == {(0, 0, 0): 0.4, (0, 0, 1): 0.4, (0, 1, 0): 0.2}

    # test case 2
    samples = [(0, 0, 0), (0, 0, 1), (0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0)]
    assert get_probabilities(samples) == {(0, 0, 0): 0.5, (0, 0, 1): 0.3333333333333333, (0, 1, 0): 0.16666666666666666}

    # test case 3
    samples = [(0, 0, 0), (0, 0, 1), (0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0), (0, 0, 0)]
    assert get_probabilities(samples) == {(0, 0, 0): 0.5714285714285714, (0, 0, 1): 0.2857142857142857, (0, 1, 0): 0.14285714285714285}

def test_qubit_state_marginal():
    # test case 1
    prob_dist = {pcvl.BasicState([0,0,0,0]): 0.4, pcvl.BasicState([0,1,0,1]): 0.3, pcvl.BasicState([1,0,0,1]): 0.3}
    assert qubit_state_marginal(prob_dist) == {(1, 1): 0.5, (0, 1): 0.5}

    # test case 2
    prob_dist = {pcvl.BasicState([0,1,0,1]): 0.4, pcvl.BasicState([0,1,1,0]): 0.3, pcvl.BasicState([1,0,0,1]): 0.3}
    assert qubit_state_marginal(prob_dist) == {(1, 1): 0.4, (1, 0): 0.3, (0, 1): 0.3}

    # test case 3
    prob_dist = {pcvl.BasicState([0,1,0,1,0,0]): 0.5, pcvl.BasicState([0,1,1,0,1,0]): 0.4, pcvl.BasicState([1,0,0,1,0,1]): 0.1}
    assert qubit_state_marginal(prob_dist) == {(1, 0, 0): 0.8, (0, 1, 1): 0.2}

def test_is_qubit_state():
    # test case 1
    state = pcvl.BasicState([0,1,0,1])
    assert is_qubit_state(state) == (1, 1)

    # test case 2
    state = pcvl.BasicState([1,0,0,1])
    assert is_qubit_state(state) == (0, 1)

    # test case 3
    state = pcvl.BasicState([1,0,1,0])
    assert is_qubit_state(state) == (0, 0)

    # test case 4
    state = pcvl.BasicState([0,1,1,0])
    assert is_qubit_state(state) == (1, 0)

    # test case 5
    state = pcvl.BasicState([1,1,0,1])
    assert is_qubit_state(state) == False

    # test case 6
    state = pcvl.BasicState([0,1,1,1])
    assert is_qubit_state(state) == False

    # test case 7
    state = pcvl.BasicState([1,1,1,1])
    assert is_qubit_state(state) == False

    # test case 8
    state = pcvl.BasicState([0,0,0,1])
    assert is_qubit_state(state) == False

def test_vqe_pipeline():

    # Define an executor function that uses the linear entangled ansatz
    def executor(params, pauli_string):
        processor = le_ansatz(params, pauli_string)
        sampler = Sampler(processor)
        samples = sampler.samples(10_000)
        return samples
    
    # Number of qubits
    num_qubits = 2
    
    # Generate a 2-qubit Hamiltonian
    hamiltonian = LiH_hamiltonian(num_electrons=2, num_orbitals=1)

    # Initialize the VQE solver with the custom executor
    vqe = VQE(
        hamiltonian=hamiltonian,
        executor=executor,
        num_params=2*num_qubits, # Number of parameters in the linear entangled ansatz
    )
    
    # Run the VQE optimization
    vqe_energy = vqe.run(
        max_iterations=10,
        verbose=True
    )

    if not isinstance(vqe_energy, float):
        raise ValueError("Optimization result is not a valid float")

def test_custom_unitary_ansatz():
    """
    Test that custom_unitary_ansatz correctly implements the Hadamard gate
    by checking the output probability distribution from the Perceval processor.
    """

    # Define 1-qubit Hadamard gate
    H = 1 / np.sqrt(2) * np.array([[1, 1],
                                   [1, -1]])
    lp_dummy = np.array([0.0])
    pauli_string = "Z"

    # Create processor
    processor = custom_unitary_ansatz(lp_dummy, pauli_string, H)

    # Sample from the processor using Perceval's Sampler
    sampler = pcvl.algorithm.Sampler(processor)
    samples = sampler.samples(10000)
    sample_count = sampler.sample_count(10000)
    prob_dist = sampler.probs()

    # Extract probabilities from BSDistribution
    prob_dict = {state: float(prob) for state, prob in prob_dist['results'].items()}

    # Assert both logical outcomes are present and roughly balanced
    assert len(prob_dict) == 2, f"Unexpected number of outcomes: {prob_dict}"
    keys = list(prob_dict.keys())
    assert all(state in prob_dict for state in [pcvl.BasicState('|1,0>'), pcvl.BasicState('|0,1>')]), \
        f"Expected states |1,0> and |0,1> not found in results: {prob_dict}"

    prob_0 = prob_dict[pcvl.BasicState('|1,0>')]
    prob_1 = prob_dict[pcvl.BasicState('|0,1>')]

    assert 0.45 <= prob_0 <= 0.55, f"Unexpected probability for |0⟩: {prob_0}"
    assert 0.45 <= prob_1 <= 0.55, f"Unexpected probability for |1⟩: {prob_1}"

    
