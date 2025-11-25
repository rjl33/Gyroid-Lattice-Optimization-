Gyroid Lattice Optimization!

Bayesian Optimization model to find the most efficient gyroid lattice design (determined by specififc stiffness = E_eff / rho_relative)
To use:
1. Generate dataset: Decide number of samples you want to generate (200 by default). Inputs (porosity, grading, periods) will be automatically determiend using Latin Hypercube Sampling
2. Train Bayesian model: Decide number of BO iterations to run
3. Once Trained using the traine model to instantly get stiffnesses of any gyroid lattice using Determine_Gyroid.py
4. If desired, automatically validate results via Finite Element Simulations (This will take up to 30 minutes)

Details:
Finite Element Simulations are done in MOOSE, input file is provided and can be altered. It is set to a samll strain finite linear elastic solve and the material parameters are set to model PLA.
The workflow to generate a sample: Get inputs -> create stl -> create Gmsh fron stl -> run simulatio in MOOSE -> store results 
The BO model uses the logEI imporovement function and is set to generate a random sample every 5 iterations to encourage exploration of the design space. 
