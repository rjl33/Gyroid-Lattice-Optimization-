
#!/usr/bin/env python3
"""
Watertight Gyroid STL Generator - With Thickness Control
Creates properly closed gyroid lattice structures with porosity OR thickness control

Usage:
    # Option 1: Specify porosity (thickness calculated automatically)
    python gyroid_generator_with_thickness.py --porosity 70 --periods 3 --output gyroid.stl
    
    # Option 2: Specify thickness directly (porosity reported)
    python gyroid_generator_with_thickness.py --thickness 0.45 --periods 3 --output gyroid.stl
"""

import numpy as np
from skimage import measure
from stl import mesh as mesh_stl
from scipy import ndimage
import argparse


def calculate_thickness_for_porosity(size, periods, resolution, target_porosity, 
                                     tolerance=0.02, max_iterations=20):
    """
    Calculate the thickness parameter needed to achieve target porosity.
    Uses binary search to find the right thickness value.
    
    Args:
        size: Cube size in mm
        periods: Number of unit cells
        resolution: Voxel resolution
        target_porosity: Desired porosity (0-1, e.g., 0.7 = 70%)
        tolerance: Acceptable error in porosity
        max_iterations: Maximum search iterations
    
    Returns:
        thickness: The thickness parameter to use
    """
    print(f"Calculating thickness for {target_porosity*100:.1f}% porosity...")
    
    # Create grid
    x = np.linspace(0, size, resolution)
    y = np.linspace(0, size, resolution)
    z = np.linspace(0, size, resolution)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Compute gyroid
    k = 2 * np.pi * periods / size
    gyroid = (np.sin(k * X) * np.cos(k * Y) + 
              np.sin(k * Y) * np.cos(k * Z) + 
              np.sin(k * Z) * np.cos(k * X))
    
    # Binary search for thickness
    thickness_min = 0.0
    thickness_max = 1.5
    
    for iteration in range(max_iterations):
        thickness = (thickness_min + thickness_max) / 2
        
        # Create solid structure
        solid = (gyroid >= -thickness) & (gyroid <= thickness)
        volume_fraction = solid.sum() / solid.size
        current_porosity = 1 - volume_fraction
        
        error = abs(current_porosity - target_porosity)
        
        if iteration % 5 == 0:
            print(f"  Iteration {iteration+1}: thickness={thickness:.3f}, "
                  f"porosity={current_porosity*100:.1f}%, error={error*100:.2f}%")
        
        if error < tolerance:
            print(f"  ✓ Converged: thickness={thickness:.3f}, porosity={current_porosity*100:.1f}%")
            return thickness
        
        # Adjust search range
        if current_porosity < target_porosity:
            # Need less material (lower thickness)
            thickness_max = thickness
        else:
            # Need more material (higher thickness)
            thickness_min = thickness
    
    print(f"  → Using thickness={thickness:.3f} (porosity={current_porosity*100:.1f}%)")
    return thickness


def calculate_porosity_for_thickness(size, periods, resolution, thickness):
    """
    Calculate the resulting porosity for a given thickness parameter.
    
    Args:
        size: Cube size in mm
        periods: Number of unit cells
        resolution: Voxel resolution
        thickness: Wall thickness parameter
    
    Returns:
        porosity: Resulting porosity (0-1)
    """
    print(f"Calculating porosity for thickness={thickness:.3f}...")
    
    # Create grid
    x = np.linspace(0, size, resolution)
    y = np.linspace(0, size, resolution)
    z = np.linspace(0, size, resolution)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Compute gyroid
    k = 2 * np.pi * periods / size
    gyroid = (np.sin(k * X) * np.cos(k * Y) + 
              np.sin(k * Y) * np.cos(k * Z) + 
              np.sin(k * Z) * np.cos(k * X))
    
    # Create solid structure
    solid = (gyroid >= -thickness) & (gyroid <= thickness)
    volume_fraction = solid.sum() / solid.size
    porosity = 1 - volume_fraction
    
    print(f"  ✓ Resulting porosity: {porosity*100:.1f}%")
    
    return porosity


def remove_floating_components(solid):
    """
    Remove disconnected floating regions, keeping only the largest connected component.
    This eliminates corner artifacts and ensures a single solid piece.
    
    Args:
        solid: Boolean 3D array
    
    Returns:
        cleaned: Boolean 3D array with only largest component
    """
    print("Removing floating components...")
    
    # Label connected components
    labeled, num_features = ndimage.label(solid)
    
    if num_features == 1:
        print("  ✓ No floating regions detected")
        return solid
    
    print(f"  Found {num_features} components")
    
    # Find largest component
    component_sizes = [(i, (labeled == i).sum()) for i in range(1, num_features + 1)]
    component_sizes.sort(key=lambda x: x[1], reverse=True)
    
    largest_label = component_sizes[0][0]
    largest_size = component_sizes[0][1]
    total_voxels = solid.sum()
    
    print(f"  Largest component: {largest_size:,} voxels ({largest_size/total_voxels*100:.1f}% of total)")
    
    if num_features > 1:
        removed_voxels = sum(size for _, size in component_sizes[1:])
        print(f"  Removing {num_features-1} floating region(s): {removed_voxels:,} voxels")
    
    # Keep only largest component
    cleaned = (labeled == largest_label)
    
    return cleaned


def create_watertight_gyroid(size=25, porosity=None, thickness=None, periods=3, 
                            resolution=100, remove_floaters=True, grading_ratio=1.0):
    """
    Generate a watertight gyroid lattice STL with specified porosity OR thickness.
    
    Args:
        size: Cube size in mm (default 25)
        porosity: Target porosity 0-1 (e.g., 0.7 = 70% porous, 30% solid)
                  If None, thickness must be specified
        thickness: Wall thickness parameter (typically 0.2-1.0)
                   If None, porosity must be specified
        periods: Number of unit cells (2-5)
        resolution: Voxel resolution (higher = better quality, slower)
        remove_floaters: Remove disconnected floating regions
        grading_ratio: thickness_bottom / thickness_top (default 1.0 = uniform)
                       1.0 = no grading (uniform thickness)
                       2.0 = bottom 2x thicker than top
                       Only used if porosity is specified
    
    Returns:
        numpy-stl Mesh object
    """
    
    print(f"="*70)
    print(f"GENERATING WATERTIGHT GYROID")
    print(f"="*70)
    print(f"Parameters:")
    print(f"  Size:       {size} mm")
    print(f"  Periods:    {periods}")
    print(f"  Resolution: {resolution}")
    if grading_ratio != 1.0:
        print(f"  Grading:    {grading_ratio:.2f} (bottom/top thickness ratio)")
    
    # Determine thickness (either calculate from porosity or use directly)
    if thickness is not None:
        # Thickness specified directly (no grading support with direct thickness)
        if grading_ratio != 1.0:
            print("  Warning: Grading ratio ignored when thickness specified directly")
        print(f"  Thickness:  {thickness:.3f} (user-specified)")
        print()
        # Calculate resulting porosity
        calculated_porosity = calculate_porosity_for_thickness(
            size, periods, resolution, thickness
        )
        print()
        thickness_bottom = thickness
        thickness_top = thickness
        use_grading = False
    elif porosity is not None:
        # Porosity specified, calculate thickness
        print(f"  Porosity:   {porosity*100:.1f}% (target)")
        print()
        thickness_avg = calculate_thickness_for_porosity(
            size, periods, resolution, porosity, tolerance=0.02
        )
        
        # Apply grading if ratio != 1.0
        if grading_ratio != 1.0:
            # Calculate bottom and top thickness from average and ratio
            thickness_top = 2 * thickness_avg / (grading_ratio + 1)
            thickness_bottom = grading_ratio * thickness_top
            print(f"  Thickness (avg):    {thickness_avg:.3f}")
            print(f"  Thickness (bottom): {thickness_bottom:.3f}")
            print(f"  Thickness (top):    {thickness_top:.3f}")
            print(f"  Gradient:           {(thickness_bottom-thickness_top)/size:.4f} per mm")
            use_grading = True
        else:
            # Uniform thickness
            thickness_bottom = thickness_avg
            thickness_top = thickness_avg
            print(f"  Thickness:  {thickness_avg:.3f}")
            use_grading = False
        print()
    else:
        raise ValueError("Either porosity or thickness must be specified")
    
    # Add padding to ensure clean boundaries
    padding = 3
    res_padded = resolution + 2 * padding
    pad_size = padding * size / resolution
    
    # Create grid (0 to size, with padding)
    x = np.linspace(-pad_size, size + pad_size, res_padded)
    y = np.linspace(-pad_size, size + pad_size, res_padded)
    z = np.linspace(-pad_size, size + pad_size, res_padded)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    print("Computing gyroid surface...")
    
    # Gyroid equation: sin(x)cos(y) + sin(y)cos(z) + sin(z)cos(x) = t
    k = 2 * np.pi * periods / size
    gyroid = (np.sin(k * X) * np.cos(k * Y) + 
              np.sin(k * Y) * np.cos(k * Z) + 
              np.sin(k * Z) * np.cos(k * X))
    
    # Create solid structure
    if use_grading:
        # Spatially-varying thickness (linear grading in Z-direction)
        z_normalized = np.clip((Z - 0) / size, 0, 1)
        thickness_field = thickness_bottom + (thickness_top - thickness_bottom) * z_normalized
        solid = (gyroid >= -thickness_field) & (gyroid <= thickness_field)
    else:
        # Uniform thickness
        solid = (gyroid >= -thickness_bottom) & (gyroid <= thickness_bottom)
    
    # Mask to bounding box [0, size]³
    mask = ((X >= 0) & (X <= size) & 
            (Y >= 0) & (Y <= size) & 
            (Z >= 0) & (Z <= size))
    solid = solid & mask
    
    # Calculate actual volume fraction
    volume_fraction = solid.sum() / mask.sum()
    actual_porosity = 1 - volume_fraction
    print(f"  Volume fraction: {volume_fraction:.1%}")
    print(f"  Actual porosity: {actual_porosity:.1%}")
    print()
    
    # Remove floating components (disconnected regions in corners, etc.)
    if remove_floaters:
        solid = remove_floating_components(solid)
        
        # Recalculate porosity after removing floaters
        volume_fraction_clean = solid.sum() / mask.sum()
        actual_porosity_clean = 1 - volume_fraction_clean
        print(f"  Final volume fraction: {volume_fraction_clean:.1%}")
        print(f"  Final porosity:        {actual_porosity_clean:.1%}")
        print()
    
    # Close any small holes (makes mesh watertight)
    print("Closing holes to ensure watertight mesh...")
    solid_closed = ndimage.binary_closing(solid, iterations=2)
    
    # Recalculate final porosity after closing
    volume_fraction_final = solid_closed.sum() / mask.sum()
    actual_porosity_final = 1 - volume_fraction_final
    print(f"  Post-closing volume fraction: {volume_fraction_final:.1%}")
    print(f"  Post-closing porosity:        {actual_porosity_final:.1%}")
    print()
    
    # Generate surface mesh using marching cubes
    print("Generating surface mesh with marching cubes...")
    # Use spacing that accounts for the actual grid including padding
    spacing = (size + 2 * pad_size) / res_padded
    verts, faces, normals, values = measure.marching_cubes(
        solid_closed.astype(float),
        level=0.5,
        spacing=(spacing, spacing, spacing)
    )
    
    # Shift vertices to account for padding (move origin to 0,0,0)
    verts = verts - pad_size
    
    # Clip vertices to ensure they're exactly in [0, size] range
    # This is critical for Gmsh to properly create volume mesh
    verts = np.clip(verts, 0, size)
    
    print(f"  Vertices:  {len(verts):,}")
    print(f"  Triangles: {len(faces):,}")
    
    # Create STL mesh
    print("Creating STL mesh...")
    stl_mesh = mesh_stl.Mesh(np.zeros(faces.shape[0], dtype=mesh_stl.Mesh.dtype))
    for i, face in enumerate(faces):
        for j in range(3):
            stl_mesh.vectors[i][j] = verts[face[j]]
    
    # Update normals
    stl_mesh.update_normals()
    
    # Check mesh properties
    print("Checking mesh quality...")
    volume, cog, inertia = stl_mesh.get_mass_properties()
    
    print(f"  Volume:  {abs(volume):.2f} mm³")
    print(f"  Center:  [{cog[0]:.2f}, {cog[1]:.2f}, {cog[2]:.2f}]")
    
    # Fix inverted normals if needed
    if volume < 0:
        print("  Fixing inverted normals...")
        stl_mesh.vectors = stl_mesh.vectors[:, ::-1, :]
        volume = -volume
    
    # Check if watertight
    edges = {}
    for triangle in stl_mesh.vectors:
        for i in range(3):
            p1 = tuple(np.round(triangle[i], 6))
            p2 = tuple(np.round(triangle[(i+1)%3], 6))
            edge = tuple(sorted([p1, p2]))
            edges[edge] = edges.get(edge, 0) + 1
    
    boundary_edges = sum(1 for count in edges.values() if count != 2)
    
    if boundary_edges == 0:
        print("  ✓ Mesh is WATERTIGHT!")
    else:
        print(f"  ⚠ Warning: {boundary_edges} boundary edges detected")
        if boundary_edges < 100:
            print("    (Small number, should be okay for meshing)")
        else:
            print("    (Try increasing resolution)")
    
    print(f"="*70)
    
    return stl_mesh


def main():
    parser = argparse.ArgumentParser(
        description='Generate watertight gyroid lattice STL files with porosity or thickness control',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--size',
        type=float,
        default=25.0,
        help='Cube size in mm'
    )
    
    parser.add_argument(
        '--porosity',
        type=float,
        default=None,
        help='Target porosity percentage (0-100), e.g., 70 = 70%% porous. '
             'Mutually exclusive with --thickness.'
    )
    
    parser.add_argument(
        '--thickness',
        type=float,
        default=None,
        help='Wall thickness parameter (typically 0.2-1.0). '
             'Mutually exclusive with --porosity. '
             'Larger values = thicker walls = lower porosity.'
    )
    
    parser.add_argument(
        '--periods',
        type=int,
        default=3,
        help='Number of unit cells (2-5 typical)'
    )
    
    parser.add_argument(
        '--grading-ratio',
        type=float,
        default=1.0,
        help='Thickness ratio: t_bottom/t_top (1.0=uniform, 2.0=bottom 2x thicker). '
             'Only applies when using --porosity.'
    )
    
    parser.add_argument(
        '--resolution',
        type=int,
        default=100,
        help='Voxel resolution (80-120 recommended, higher=better quality)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output STL filename'
    )
    
    parser.add_argument(
        '--keep-floaters',
        action='store_true',
        help='Keep floating disconnected regions (not recommended)'
    )
    
    args = parser.parse_args()
    
    # Validate input: exactly one of porosity or thickness must be specified
    if args.porosity is None and args.thickness is None:
        parser.error("Either --porosity or --thickness must be specified")
    
    if args.porosity is not None and args.thickness is not None:
        parser.error("Cannot specify both --porosity and --thickness. Choose one.")
    
    # Convert porosity from percentage to fraction if specified
    porosity_fraction = None
    if args.porosity is not None:
        porosity_fraction = args.porosity / 100.0
        if not 0 < porosity_fraction < 1:
            print(f"Error: Porosity must be between 0 and 100 (got {args.porosity})")
            return
    
    # Validate thickness if specified
    if args.thickness is not None:
        if args.thickness <= 0 or args.thickness > 2.0:
            print(f"Warning: Thickness {args.thickness} is outside typical range (0.2-1.0)")
            print("Continuing anyway, but results may be unexpected.")
    
    # Validate grading ratio
    if args.grading_ratio < 1.0:
        parser.error(f"Grading ratio must be ≥ 1.0 (got {args.grading_ratio})")
    
    if args.grading_ratio > 1.0 and args.thickness is not None:
        print("Warning: Grading ratio will be ignored when using --thickness")
    
    # Generate gyroid
    gyroid_mesh = create_watertight_gyroid(
        size=args.size,
        porosity=porosity_fraction,
        thickness=args.thickness,
        periods=args.periods,
        resolution=args.resolution,
        remove_floaters=not args.keep_floaters,
        grading_ratio=args.grading_ratio
    )
    
    # Save STL
    print(f"\nSaving to: {args.output}")
    gyroid_mesh.save(args.output)
    
    print(f"✓ Successfully saved: {args.output}")
    print()


if __name__ == "__main__":
    main()
