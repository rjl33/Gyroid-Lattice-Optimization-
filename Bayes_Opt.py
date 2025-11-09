from ax import Client, RangeParameterConfig
import os 
import numpy as np
import pandas as pd
import torch 
from botorch.models.transforms.input import Normalize
from botorch.utils.transforms import standardize
from botorch.models import SingleTaskGP, ModelListGP
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
from botorch.acquisition.objective import GenericMCObjective
from gpytorch.mlls import ExactMarginalLogLikelihood
from botorch.fit import fit_gpytorch_mll
from typing import Optional
from botorch.optim import optimize_acqf
import time
import warnings
import csv
from botorch import fit_gpytorch_mll
from botorch.acquisition import (
    qLogExpectedImprovement,
    qLogNoisyExpectedImprovement,
)
from botorch.exceptions import BadInitialCandidatesWarning
from botorch.sampling.normal import SobolQMCNormalSampler
from Sample_Gen_Pipeline import run_sim, append_result_row


# Load initial LHS data
df = pd.read_csv("global_results.csv")
df_converged = df[df['converged'] == 1]  # Only use converged initial samples

porosity_np = df_converged['porosity'].values
grading_np = df_converged['grading'].values
periods_np = df_converged['periods'].values
converged_np = df_converged['converged'].values
objective_np = df_converged['specific_stiffness'].values




device =  torch.device("cuda" if torch.cuda.is_available() else "cpu")
dtype = torch.double
SMOKE_TEST = os.environ.get("SMOKE_TEST")



#TEST
# pretend we got 3 MC samples, q=1, m=2: [objective, converged]
# Y = torch.tensor([
#     [[3.0, 1.0]],   # feasible
#     [[5.0, 0.0]],   # infeasible
#     [[2.5, 1.0]],   # feasible
# ], dtype=torch.double)

#Problem Setup
def outcome_constraint(Y):
    "Second objective = converged or not; 0 for not converged, 1 for converged"
    """Constraint; feasible if less than or equal to zero"""
    conv = Y[..., 1]
    return 1.0 - conv #Feaisble if <= 0

def weighted_obj(Y): 
    """Returns zero if not feasible"""
    obj = Y[..., 0]
    feas = (outcome_constraint(Y) <= 0).to(obj.dtype)  
    return obj * feas


constraints = [outcome_constraint]

# print("constraint c(Y):", outcome_constraint(Y).squeeze(-1))  # should be [0, 1, 0]
# print("weighted obj:", weighted_obj(Y).squeeze(-1))           # should be [3.0, 0.0, 2.5]

#Model Initialization
#Move existing array to pytroch tensors 
porosity = torch.tensor(porosity_np, device=device, dtype=dtype)
grading = torch.tensor(grading_np, device=device, dtype=dtype)
periods = torch.tensor(periods_np, device=device, dtype=dtype)
converged = torch.tensor(converged_np, device=device, dtype=dtype)
objective = torch.tensor(objective_np, device=device, dtype=dtype)

#Construct X and Y: 
X_init = torch.stack([porosity, grading, periods], dim=1)
Y_obj = objective.unsqueeze(-1)
Y_con = converged.unsqueeze(-1)

#Scale 
Y_obj_std = standardize(Y_obj)

#Fit Surrogate Models 
def initialize_model(X_init, Y_obj_std, Y_con, state_dict=None):
    obj_model = SingleTaskGP(X_init, Y_obj_std)
    con_model = SingleTaskGP(X_init, Y_con)
    model = ModelListGP(obj_model, con_model)
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)

    if state_dict is not None:
        model.load_state_dict(state_dict, strict=False)
    return model, mll

def obj_callable(Y: torch.Tensor, X=None):
    return Y[..., 0]


objective = GenericMCObjective(objective=obj_callable)

porosity_low, porosity_high = 20, 85
grading_low, grading_high = 1.0, 4.0
periods_low, periods_high = 1, 8

bounds = torch.tensor([[porosity_low, grading_low, periods_low],
                      [porosity_high, grading_high, periods_high],
                      ], device=device, dtype=dtype)


NUM_RESTARTS = 10 if not SMOKE_TEST else 2
RAW_SAMPLES = 200 if not SMOKE_TEST else 2

def optimize_acqf_and_get_observation(acq_func):
    """Optimizes the acquisition function, and returns a new candidate and a noisy observation
        evaluate and return (new_x, y_obj, y_con)"""
    candidates, _ = optimize_acqf(
        acq_function=acq_func,
        bounds=bounds,
        num_restarts=NUM_RESTARTS,
        raw_samples=RAW_SAMPLES,
        options={"maxiter": 200},
    )

    #observe new values
    new_x = candidates.detach()
    

    #evaluate simulater at new X:
    #Unpack and call function:
    porosity = float(new_x[0, 0])
    grading = float(new_x[0, 1])
    period = float(new_x[0, 2])

    obj_val, converged_flag = run_sim(porosity, grading, period)

    if converged_flag == 0:
        obj_val = -1000.0
    
    return new_x, obj_val, converged_flag

#Generate a Random Sample (to compare to our guided search to prove it is better)
def update_random_observation(best_random):
    """Simulated a random policy by taking the current list of best values oberseved randomly
        and  randomly drawing a  new point to sample"""
    
    rand_x = torch.rand(1, 3, device=device, dtype=dtype) 
    #scale to bounds 
    rand_x = bounds[0] + (bounds[1] - bounds[0]) * rand_x
    
    #run_simulation
    porosity = float(rand_x[0, 0])
    grading = float(rand_x[0, 1])
    period = float(rand_x[0, 2])

    obj_val, converged_flag = run_sim(porosity, grading, period)
    
    # Only count if converged (fair comparison)
    if converged_flag == 1:
        next_random_best = obj_val
    else:
        next_random_best = -float('inf')  # Don't update best if infeasible
    
    best_random.append(max(best_random[-1], next_random_best))
    return best_random

#compare best random to best BO
best_random = [Y_obj[Y_con.squeeze() == 1].max().item()]  # Best feasible from initial data
best_bo = [Y_obj[Y_con.squeeze() == 1].max().item()]

warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

N_ITERATIONS = 20
#RUN BO OPTIMIZATION LOOP
for iteration in range(N_ITERATIONS):
    t0 = time.monotonic()
    #fit model on current data 
    model, mll = initialize_model(X_init, Y_obj_std, Y_con)

    #Create acquisition function
    qNEI = qLogNoisyExpectedImprovement(
        model=model,
        X_baseline=X_init,
        prune_baseline=True,
        outcome_constraints=(outcome_constraint, torch.tensor([0.0]))
    )

    #get new observation
    new_x, obj_val, converged_flag = optimize_acqf_and_get_observation(qNEI)
    best_random = update_random_observation(best_random)

    # Log to CSV
    design = {
        "porosity": float(new_x[0, 0]),
        "periods": int(round(new_x[0, 1])),
        "grading": float(new_x[0, 2])
    }
    append_result_row(
        "bo_results.csv",
        design,
        rho_star=None,  # Could extract if needed
        rho_slice_min=None,
        rho_slice_max=None,
        converged=(converged_flag == 1),
        E_eff=None,
        specific_stiffness=obj_val if converged_flag else None,
        note=f"BO_iter_{iteration+1}"
    )

    #update datasets 
    X_init = torch.cat([X_init, new_x])
    Y_obj = torch.cat([Y_obj, torch.tensor([[obj_val]], device=device, dtype=dtype)])
    Y_con = torch.cat([Y_con, torch.tensor([[converged_flag]], device=device, dtype=dtype)])

    # Track best feasible BO result
    feasible_obj = Y_obj[Y_con.squeeze() == 1]
    if len(feasible_obj) > 0:
        best_bo.append(feasible_obj.max().item())
    else:
        best_bo.append(best_bo[-1])

    #Restandardize after adding data
    Y_obj_std = standardize(Y_obj)

    print(f"Iteration {iteration+1}: obj={obj_val:.f}, converged={converged_flag}")
    print(f"Iter {iteration+1}: BO_best={best_bo[-1]:.3f}, Random_best={best_random[-1]:.3f}")










    

