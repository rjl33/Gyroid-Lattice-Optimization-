

#!/usr/bin/env python3
"""
Create 3D volume mesh from STL using Gmsh Python API
Simple and effective approach for watertight STL files
"""

import gmsh
import sys

def mesh_stl_to_volume(stl_file, output_file, element_size=3.0):
    """
    Convert STL to volumetric mesh with tetrahedra.
    """
    
    print(f"="*70)
    print(f"Creating volume mesh from: {stl_file}")
    print(f"="*70)
    
    # Initialize Gmsh
    gmsh.initialize()
    gmsh.model.add("gyroid")
    
    # Import STL
    print("Importing STL...")
    gmsh.merge(stl_file)
    
    # Create surface loop from all surfaces
    # This assumes the STL is a closed surface
    print("Creating surface loop...")
    surface_tags = [s[1] for s in gmsh.model.getEntities(2)]
    print(f"  Found {len(surface_tags)} surfaces")
    
    # Create surface loop
    surface_loop = gmsh.model.geo.addSurfaceLoop(surface_tags)
    
    # Create volume from surface loop
    print("Creating volume...")
    volume = gmsh.model.geo.addVolume([surface_loop])
    
    # Synchronize CAD representation
    gmsh.model.geo.synchronize()
    
    # Set mesh size
    print(f"Setting mesh size: {element_size} mm")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", element_size * 0.5)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", element_size * 1.5)
    
    # Mesh algorithm
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay
    
    # Generate 3D mesh
    print("Generating 3D mesh...")
    gmsh.model.mesh.generate(3)
    
    # Optimize
    print("Optimizing mesh...")
    gmsh.model.mesh.optimize("Netgen")
    
    # Physical groups for MOOSE
    print("Creating physical groups...")
    gmsh.model.addPhysicalGroup(3, [volume], name="gyroid")
    
    # Get mesh statistics
    nodes = gmsh.model.mesh.getNodes()
    elements = gmsh.model.mesh.getElements(3)  # 3D elements (fixed - was commented out)
    
    print(f"\nMesh statistics:")
    print(f"  Nodes: {len(nodes[0])}")
    print(f"  Volume elements: {len(elements[2][0]) if len(elements[2]) > 0 else 0}")
    
    # Optional GUI
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()

    # Save mesh
    print(f"\nSaving to: {output_file}")
    gmsh.write(output_file)
    
    # Finalize
    gmsh.finalize()
    
    print("="*70)
    print("✓ Volume mesh created successfully!")
    print("="*70)
    
    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mesh_stl_to_volume.py input.stl [element_size]")
        sys.exit(1)
    
    stl_file = sys.argv[1]
    element_size = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
    
    output_file = stl_file.replace('.stl', '.msh')
    
    try:
        mesh_stl_to_volume(stl_file, output_file, element_size)
        print(f"\n✓ Ready for MOOSE: {output_file}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
