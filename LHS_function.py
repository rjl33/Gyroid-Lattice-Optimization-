import numpy as np
from scipy.stats import qmc

#Define Materials bounds 
POROSITY_MIN = 20
POROSITY_MAX = 0.85

PERIODS_MIN = 1
PERIODS_MAX = 8

GRADING_MIN = 1.0
GRADING_MAX = 4.0

def generate_lhs_designs(
        num_samples,
        porosity_range,
        periods_range,
        grading_range
):
    por_min, por_max = porosity_range
    per_min, per_max = periods_range
    grad_min, grad_max = grading_range

    #Make LHS Sampler for 3 dimensions
    sampler = qmc.LatinHypercube(d=3)

    #draw samples in [0,1)
    unit_samples = sampler.random(n=num_samples)

    #scale each column
    l_bounds = [por_min, per_min, grad_min]
    u_bounds = [por_max, per_max, grad_max]

    scaled = qmc.scale(unit_samples, l_bounds, u_bounds)

    #Round periods to intergers
    periods_int = np.round(scaled[:,1]).astype(int)

    #Make input arrays
    designs = []
    for i in range(num_samples):
        d = {
        "porosity": float(scaled[i,0]),
        "periods": int(periods_int[i]),
        "grading": float(scaled[i,2])
        }
        designs.append(d)

        return designs
    
    
