import os
from kicad_utils import KiCadUtils

if __name__ == "__main__":

    # Define the path to the DXF file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dxf_filename = os.path.join(script_dir, '..', 'human-arm_dual-grid_v5_STENCIL.DXF')  # Replace with the path to your DXF file
    pcb_filename = os.path.join(script_dir, '..', '128ch-hdemg-sleeve.kicad_pcb') # Adjust to your pcb
    updated_pcb_filename = os.path.join(script_dir, '..', '128ch-hdemg-sleeve_updated.kicad_pcb') # Adjust to your pcb
    remapping_file = os.path.join(script_dir, 'electrode_remapping.txt')  # Optional, if you need to remap indices

    # Define the footprint names to be updated in the pcb file. This needs to be looked up in the PCB editor or acquired
    # from the KiCad footprint library.
    electrode_footprint_name = 'CustomComponents:1625-5-57-15_D3.18mm_disk'
    mounting_hole_footprint_name = 'MountingHole:MountingHole_3.2mm_M3_Pad_TopOnly'

    # Define the radius dictionary for the shapes in the DXF file. This is used to determine the approximate center of the shapes.
    radius_dict = {
        'electrode': 1.5,  # Diameter is 3mm, so radius is 1.5
        'grommet': 3.0    # Example radius for grommets (mounting holes), adjust accordingly
    }

    # Define offsets and flip coordinates to match the inverted-y layout in the PCB editor (need to look at internal coordinates to get this)
    x_offset = 163.5
    y_offset = 108
    flip_y = True      # Might not need if using another PCB editor, but KiCad needs this for now
    results = KiCadUtils.get_coordinates_from_dxf(dxf_filename, radius_dict, flip_y=flip_y, visualize=True, export=False)

    # The electrodes are currently not in the mapping order we need, since the cable routing is influenced by the electrode placement to the chips
    print("=== Electrode coordinates before remapping ===")
    for i, row in results.iterrows():
        if i < 10:
            print(f"Electrode {row['channel']}: {row['x'] + x_offset}, {row['y'] + y_offset}")

    # Parse the remapping file and apply to the labeled coordinates
    #remapping = KiCadUtils.parse_remapping_file(remapping_file)

    # Instead of hard-coding the remapping, we will define the electrode arrangement
    remapped_df = KiCadUtils.apply_remapping_v2(results, '8-by-8_swap', 'electrode')

    # Double-check the remapping results
    KiCadUtils.visualize_footprints(remapped_df)

    # Extract coordinates for electrodes
    electrode_df = remapped_df[remapped_df['label'] == 'electrode']

    # Quick check of the electrode coordinate positions, including offset
    print("=== Electrode coordinates after remapping ===")
    for i, row in electrode_df.iterrows():
        if i < 10:
            print(f"Electrode {row['channel']}: {row['x'] + x_offset}, {row['y'] + y_offset}")

    # Update the PCB file with the new electrode coordinates
    KiCadUtils.update_footprint_locations(pcb_filename,
                                          electrode_df,
                                          electrode_footprint_name,
                                          updated_name_tag='',
                                          x_offset=x_offset, y_offset=y_offset,
                                          verbose=True)

    # Update the PCB file with the mounting hole coordinates (don't really need remapped coordinates for these)
    mounting_hole_df = remapped_df[remapped_df['label'] == 'grommet']
    print( "Updating PCB file with grommet coordinates...")
    KiCadUtils.update_footprint_locations(pcb_filename,
                                          mounting_hole_df,
                                          mounting_hole_footprint_name,
                                          updated_name_tag='_updated',
                                          x_offset=x_offset, y_offset=y_offset,
                                          verbose=True)

    print("Done updating PCB file.")


