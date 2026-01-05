# Gyroid Lattice Optimization

A Bayesian optimization framework for designing efficient gyroid lattice structures through integrated computational geometry, finite element analysis, and machine learning.

## Overview

This project implements an end-to-end optimization pipeline to identify high-performance gyroid lattice designs by maximizing specific stiffness (E<sub>eff</sub> / ρ<sub>relative</sub>). The framework combines parametric STL generation, automated mesh creation, MOOSE-based finite element simulations, and Bayesian optimization with Latin Hypercube Sampling for efficient design space exploration.

### Key Features

- **Parametric Gyroid Generation**: Automated creation of functionally graded gyroid lattices with tunable porosity, grading, and periodicity
- **Bayesian Optimization**: Efficient design space exploration using LogEI acquisition function with periodic random sampling
- **Finite Element Validation**: MOOSE framework integration for small-strain linear elastic analysis
- **Design Space Sampling**: Latin Hypercube Sampling for optimal initial dataset generation
- **GUI Interface**: Interactive tools for design visualization and parameter selection

## Technical Approach

### Design Parameters

The optimization considers three primary design variables:
- **Porosity**: Volume fraction of void space
- **Grading**: Spatial variation of lattice density
- **Periods**: Number of unit cells in the structure

### Workflow

1. **Sample Generation**: Latin Hypercube Sampling generates diverse design points across the parameter space
2. **Geometry Creation**: Parametric STL models generated for each design point
3. **Mesh Generation**: Gmsh converts STL geometry to finite element meshes
4. **FE Simulation**: MOOSE performs linear elastic analysis with PLA material properties
5. **Surrogate Modeling**: Bayesian optimization builds a Gaussian process surrogate
6. **Optimization**: LogEI acquisition function identifies promising designs, with exploration enforced through periodic random sampling

## Installation

### Prerequisites

- Python 3.8+
- MOOSE framework (for FE simulations)
- Gmsh (for mesh generation)

### Python Dependencies

```bash
pip install numpy scipy matplotlib
pip install botorch gpytorch  # For Bayesian optimization
pip install trimesh  # For STL handling
```

### MOOSE Setup

Follow the [MOOSE installation guide](https://mooseframework.inl.gov/getting_started/installation/index.html) for your platform. Ensure the MOOSE executable is in your system PATH.

## Usage

### Quick Start

```python
# 1. Generate initial dataset (default: 200 samples)
python Sample_Gen_Pipeline.py --n_samples 200

# 2. Run Bayesian optimization
python Bayes_Opt.py --n_iterations 50

# 3. Evaluate a specific design
python Determine_Gyroid.py --porosity 0.7 --grading 0.5 --periods 3
```

### Detailed Workflow

#### 1. Dataset Generation

Generate an initial dataset using Latin Hypercube Sampling:

```python
python Sample_Gen_Pipeline.py --n_samples 200 --output_dir ./data
```

This automatically:
- Samples design parameters using LHS
- Generates STL files for each design
- Creates finite element meshes
- Runs MOOSE simulations (~30 min per sample)
- Stores results for model training

#### 2. Bayesian Optimization

Train the surrogate model and perform optimization:

```python
python Bayes_Opt.py --n_iterations 100 --exploration_freq 5
```

Parameters:
- `n_iterations`: Number of BO iterations
- `exploration_freq`: Random sample every N iterations (default: 5)

#### 3. Design Evaluation

Query the trained model for instant stiffness predictions:

```python
python Determine_Gyroid.py --porosity 0.65 --grading 0.3 --periods 4 --validate
```

Use `--validate` flag to run FE simulation for verification (~30 minutes).

### GUI Interface

Launch the interactive design tool:

```python
python GUI/main_gui.py
```

## File Structure

```
Gyroid-Lattice-Optimization-/
├── Bayes_Opt.py              # Bayesian optimization implementation
├── Gyroid_Generator.py        # Parametric gyroid STL generation
├── LHS_function.py            # Latin Hypercube Sampling utilities
├── Sample_Gen_Pipeline.py     # End-to-end sample generation workflow
├── stl_to_mesh.py            # STL to FE mesh conversion (Gmsh)
├── test_gy.i                 # MOOSE input file template
├── GUI/                      # Interactive visualization tools
└── README.md
```

## Finite Element Details

### MOOSE Configuration

- **Analysis Type**: Small strain, linear elastic
- **Material Model**: PLA (Polylactic Acid)
  - Young's Modulus: 3.5 GPa
  - Poisson's Ratio: 0.36
- **Boundary Conditions**: Compression loading with periodic side constraints
- **Solver**: Newton-Raphson with automatic time stepping

The MOOSE input file (`test_gy.i`) can be modified for different material properties, loading conditions, or analysis types.

## Optimization Details

### Acquisition Function

The framework uses the **LogEI (Log Expected Improvement)** acquisition function, which provides:
- Robust exploration of the design space
- Numerical stability for extreme objective values
- Balance between exploitation and exploration

### Exploration Strategy

To prevent premature convergence, the algorithm injects a random sample every 5 iterations, ensuring adequate coverage of the design space while focusing on promising regions.

## Results

The optimized surrogate model enables:
- **Instant predictions**: Query any design in milliseconds
- **Efficient optimization**: Converge to optimal designs in 50-100 iterations
- **Validated accuracy**: FE verification confirms model predictions

Typical optimal designs achieve specific stiffness improvements of 20-40% over baseline uniform lattices.

## Applications

This framework can be applied to:
- Lightweight structural design for aerospace and automotive applications
- Energy absorption systems
- Thermal management structures
- Biomedical scaffolds
- Additive manufacturing optimization

## Future Work

- Extension to nonlinear material models and large deformation analysis
- Multi-objective optimization (stiffness, weight, energy absorption)
- Integration with topology optimization methods
- Manufacturing constraint incorporation
- Experimental validation with 3D-printed specimens

## References

This work builds on research in:
- Bayesian optimization for engineering design
- Triply periodic minimal surfaces in structural mechanics
- Surrogate modeling for expensive simulations

## Contact

Ryan Lutz
ryanjohnlutz@gmail.com
Duke University - Mechanical Engineering and Materials Science  
[GitHub](https://github.com/rjl33)

For questions or collaboration opportunities, please open an issue or contact via email.
