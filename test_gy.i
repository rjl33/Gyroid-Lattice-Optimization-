[Mesh]
    [file]
        type = FileMeshGenerator
        file = gyroid_50mm_test.msh
    []
    [bottom_nodes]
        type = BoundingBoxNodeSetGenerator
        input = file
        new_boundary = 'bottom'
        bottom_left = '-1 -1 -0.5'
        top_right = '26 26 0.5'
    []

    [top_nodes]
        type = BoundingBoxNodeSetGenerator
        input = bottom_nodes
        new_boundary = 'top'
        bottom_left = '-1 -1 24.5'
        top_right = '26 26 0.5'
    []
[]

# [Functions]
#     [hardening]
#         type = PiecewiseLinear
#         x = '0.0 0.01 0.02 0.05 0.1 0.2 0.5'
#         y = '0.0 50 70 110 158 223 353'
#     []
# []


[GlobalParams]
    displacements = 'disp_x disp_y disp_z'
    volumetric_locking_correction = true
[]

[Physics]
    [SolidMechanics]
        [QuasiStatic]
            [all]
                strain = SMALL
                add_variables = true
                generate_output = 'vonmises_stress strain_xx strain_yy strain_zz'
                save_in = 'react_x react_y react_z'
                use_automatic_differentiation = true
            []
        []
    []
[]

[AuxVariables]
    [react_x]
    []
    [react_y]
    []
    [react_z]
    []
[]


[Materials]
    [elasticity_tensor]
        type = ADComputeIsotropicElasticityTensor
        youngs_modulus = 3000
        poissons_ratio = 0.36
    []


    # [plasticity]
    #     type = ADIsotropicPlasticityStressUpdate
    #     yield_stress = 50.0
    #     hardening_constant = 0
    # []

    [stress]
        type = ADComputeLinearElasticStress
        # inelastic_models = 'plasticity'
        # perform_finite_strain_rotations = true
    []

    [density]
        type = ADGenericConstantMaterial
        prop_names = 'density'
        prop_values = '1.25e-9'
    []
[]

[BCs]
    [bottom_x]
        type = DirichletBC
        variable = disp_x
        boundary = 'bottom'
        value = 0.0
    []
    [bottom_y]
        type = DirichletBC
        variable = 'disp_y'
        boundary = 'bottom'
        value = 0.0
    []
    [bottom_z]
        type = DirichletBC
        variable = 'disp_z'
        boundary = 'bottom'
        value = 0.0
    []

    [top_displacement]
        type = FunctionDirichletBC
        variable = disp_z
        boundary = 'top'
        function = '-0.5 * t'
    []
[]


[Preconditioning]
    [SMP]
        type = SMP
        full = true

        petsc_options_iname = '-pc_type -pc_hypre_type -pc_hypre_boomeramg_strong_threshold'
        petsc_options_value = 'hypre boomeramg 0.7'
    []
[]

[Executioner]
    type = Transient
    solve_type = NEWTON
    petsc_options_iname = '-ksp_type -pc_type -pc_hypre_type'
    petsc_options_value = 'gmres hypre boomeramg'

    nl_rel_tol = 1e-10
    nl_abs_tol = 1e-8
    nl_max_its = 50

    l_tol = 1e-5
    l_max_its = 100

    start_time = 0.0
    end_time = 1.0

    [TimeStepper]
        type = IterationAdaptiveDT
        dt = 0.05
        optimal_iterations = 8
        iteration_window = 2
        growth_factor = 1.2
        cutback_factor = 0.5
    []

    automatic_scaling = true
    line_search = 'basic'
[]

[Postprocessors]


    [max_vonmises]
        type = ElementExtremeValue
        variable = vonmises_stress
        value_type = max
        execute_on = 'INITIAL TIMESTEP_END'
    []

    [avg_vonmises]
        type = ElementAverageValue
        variable = vonmises_stress
        execute_on = 'INITIAL TIMESTEP_END'
    []

    [max_disp_z]
        type = NodalExtremeValue
        variable = disp_z
        value_type = min
        execute_on = 'INITIAL TIMESTEP_END'
    []

    [volume]
        type = VolumePostprocessor
        execute_on = 'INITIAL'
    []

    [reaction_force_z]
        type = NodalSum
        variable = 'react_z'
        boundary = 'bottom'
        execute_on = 'INITIAL TIMESTEP_END'
    []
    

    [num_elems]
        type = NumElements
        execute_on = 'INITIAL'
    []

    [num_nodes]
        type = NumNodes
        execute_on = 'INITIAL'
    []

    [num_dofs]
        type = NumDOFs
        execute_on = 'INITIAL'
    []

    [num_nl_its]
        type = NumNonlinearIterations
        execute_on = 'TIMESTEP_END'
    []

    [num_linear_its]
        type = NumLinearIterations
        execute_on = 'TIMESTEP_END'
    []
[]

[Outputs]
    csv = true
    print_linear_residuals = false

    
  [nemesis]
    type = Exodus
    hide = 'vonmises_stress strain_xx strain_yy strain_zz'
    # 'vel_x accel_x disp_x'
    additional_execute_on = FINAL
  []
    
    [console]
        type = Console
        max_rows = 15
        fit_mode = 80
    []

    [checkpoint]
        type = Checkpoint
        num_files = 2
        interval = 5
    []
[]

[Debug]
    show_var_residual_norms = true
[]








