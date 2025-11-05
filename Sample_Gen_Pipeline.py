import subprocess
from pathlib import Path 
import numpy as np
from scipy.stats import qmc
import trimesh
import numpy as np
from scipy.stats import qmc
import os
import csv

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
    
    


def generate_stl(design, run_dir, cube_size=25.0):
    stl_path = Path(run_dir) / "part.stl"

    command = [
        "python",
        "gyroid_generator.py",
        "--porosity", str(design["porosity"]),
        "--grading-ratio", str(design["grading"]),
        "--periods", str(design["periods"]),
        "--output", str(stl_path),
    ]

    subprocess.run(command, check=True)

    return stl_path 

def stl_to_mesh(stl_path, msh_path):
    command = [
        "python",
        "stl_to_mesh.py",
        str(stl_path),
        str(msh_path),
    ]

    subprocess.run(command, check=True)
    return msh_path

def write_moose_input(
        template_path,
        msh_path, 
        out_i_path,
):
    template_text = Path(template_path).read_text()
    text = template_text("PATH_TO_MESH", str(msh_path))
    text = text.replace("FILE_BASE", "out")

    job_i_path = Path(run_dir) / "job.i"
    job_i_path.write(text)
    return job_i_path

def run_moose(input_file, workdir, mpi_ranks=16, moose_exec="../modules/solid_mechanics/solid_mechanics-opt -i test_gy.i"):
    try:
        command = [
            "mpiexec",
            "-n", str(mpi_ranks),
            moose_exec,
        ]
        
        subprocess.run(command, cwd=workdir, check=True)
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"[run_moose] MOOSE solve failed with return code {e.returncode}")
        return False


    


def compute_relative_density(stl_path, cube_size=25.0):
    mesh = trimesh.load_mesh(stl_path, process=False)
    solid_volume = mesh.volume
    bounding_volume = cube_size ** 3
    rho_star = solid_volume / bounding_volume
    return rho_star, mesh 


def geometry_sanity(mesh, max_components=3):
    watertight_ok = mesh.is_watertight
    comps = mesh.split(only_watertight=False)
    connected_ok = (len(comps) <= max_components)
    return watertight_ok and connected_ok

def feasability_filter(stl_path, rho_max = 0.35, cube_size=25):
    rho_star, mesh = compute_relative_density(stl_path, cube_size)

    if rho_star > rho_max:
        return False, rho_star, None, None, "too_dense"
    
    if not geometry_sanity(mesh):
        return False, rho_star, None, None, "geom_bad"
    
    return True, rho_star, None, None, "ok"



def append_result_row(global_csv_path,
                      design,
                      rho_star,
                      rho_slice_min,
                      rho_slice_max,
                      converged,
                      E_eff=None,
                      specific_stiffness=None,
                      note=""):
    """
    Append one row of results to the global_results.csv file.
    If the file doesn't exist yet, write the header first.
    """

    file_exists = os.path.exists(global_csv_path)

    with open(global_csv_path, "a", newline="") as f:
        writer = csv.writer(f)

        # Write header if it's a new file
        if not file_exists:
            writer.writerow([
                "porosity",
                "periods",
                "grading",
                "rho_star",
                "rho_slice_min",
                "rho_slice_max",
                "converged",
                "E_eff",
                "specific_stiffness",
                "note"
            ])

        # Write the actual row
        writer.writerow([
            design["porosity"],
            design["periods"],
            design["grading"],
            rho_star,
            rho_slice_min if rho_slice_min is not None else "",
            rho_slice_max if rho_slice_max is not None else "",
            int(converged),
            E_eff if E_eff is not None else "",
            specific_stiffness if specific_stiffness is not None else "",
            note
        ])

def parse_moose_csv(out_csv_path):
    Fz_top = None
    k_eff = None
    E_eff = None

    with open(out_csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "Fz_top" in row and row["Fz_top"] != "":
                Fz_top = float(row["Fz_top"])
            if "k_eff" in row and row["k_eff"] != "":
                k_eff = float(row["k_eff"])
            if "E_eff" in row and row["E_eff"] != "":
                E_eff = float(row["E_eff"])
    return Fz_top, k_eff, E_eff



def main():
    NUM_SAMPLES = 200
    GLOBAL_CSV = "global_results.csv"

    designs = generate_lhs_designs(num_smaples = NUM_SAMPLES)

    Path("dataset").mkdir(exist_ok=True)

    for i, design in enumerate(designs):
        run_dir = Path("dataset") / f"run_{i:o4d}"
        run_dir.mkdir(parents=True, exist_ok=True)

        #Generate STL:
        stl_path = generate_stl(design, run_dir)

        #Feasability Check
        feasible, rho_star, rho_slice_min, rho_slice_max, note = feasability_filter(
            stl_path, 
            rho_max = 0.35, 
            cube_size=25
        )

        if not feasible:
            append_result_row(
                GLOBAL_CSV,
                design,
                rho_star,
                rho_slice_min,
                rho_slice_max,
                converged=False,
                note=note
            )
            continue

        #Mesh the STL: 
        msh_path = run_dir / "part.msh"
        stl_to_mesh(stl_path, msh_path)

        #Write to MOOSE input file
        job_i_path = write_moose_input(
            template_path="base_template.i",
              msh_path=msh_path,
                run_dir=run_dir
        )

        success = run_moose(str(job_i_path), str(run_dir), mpi_ranks=16)

        if not success:
            append_result_row(
            GLOBAL_CSV,
            design,
            rho_star,
            converged=False,
            note="moose_fail"
        )
        continue

        out_csv_path = run_dir / "out.csv"
        Fz_top, k_eff, E_eff = parse_moose_csv(out_csv_path)

        specific_stifness = None
        if(E_eff is not None) and (rho_star is not None) and rho_star > 0:
            specific_stiffness = E_eff / rho_star

        append_result_row(
        GLOBAL_CSV,
        design,
        rho_star,
        converged=True,
        E_eff=E_eff,
        specific_stiffness=specific_stiffness,
        note="ok"
    )






