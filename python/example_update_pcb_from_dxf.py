# This script demonstrates how to update a KiCad PCB file with shape data from
# a DXF file. If you have a DXF file from a CAD drawing or Illustrator, you can
# use this script to extract the shape data and update the PCB file with the
# new coordinates. This script is useful for updating the PCB file with new
# electrode locations or mounting holes.
#
# Author: jshulgac@andrew.cmu.edu
# Last updated: 2025-02-25

import os
from kicad_utils import KiCadUtils, kicad_pcb_schematic

if __name__ == "__main__":

    # ================= USER INPUTS ==================
    dxf_filename = 'EMG-sleeve-forearm_128ch_V13.DXF' # DFX file name with shape data
    pcb_filename = '128ch-hdemg-forearm.kicad_pcb' # kicad_pcb file name to update

    # Define some metadata in the PCB file like footprint, radius, and entity type. Make sure every key has different values
    pcb_data = {
        '3mm-electrode': {'footprint': 'CustomComponents:1625-5-57-15_D3.18mm_disk', 'radius': 1.5, 'entity': 'CIRCLE'},
        '6mm-electrode': {'footprint': 'CustomComponents:2036-3-57-15_D5.99mm', 'radius': 3.0, 'entity': 'CIRCLE'},
        #'m4-mount': {'footprint': 'MountingHole:MountingHole_4.3mm_M4_ISO14580_Pad', 'radius': 2.0, 'entity': 'CIRCLE'},
        'm3-mount': {'footprint': 'MountingHole:MountingHole_3.2mm_M3_DIN965_Pad', 'radius': 1.5, 'entity': 'CIRCLE'},
        'pcb-m3-mount': {'footprint': 'MountingHole:MountingHole_3.2mm_M3_DIN965_Pad', 'radius': 2.0, 'entity': 'CIRCLE'},
    }
    style = 'A2' # Define the KiCad PCB editor schematic style
    offset = (13.0,-69.5) # Offset to apply to the coordinates
    flip_y = False # Match y layout in PCB editor.
    #shape_key = '6mm-electrode'  # The custom key to use for parsing the shape data
    shape_key = 'pcb-m3-mount'
    # ================================================

    # Define paths to the DXF and PCB files
    root_path = os.path.dirname(os.path.abspath(__file__))
    dxf_filepath = os.path.join(root_path, '..', dxf_filename)
    pcb_filepath = os.path.join(root_path, '..', pcb_filename)

    # Get the coordinates of all entities detected in the DXF file. Will can pass in our dictionary containing extra
    # info about the footprints we are using, the entity type, and shape, otherwise create unique ids for new shapes
    results = KiCadUtils.get_coordinates_from_dxf(dxf_filepath, pcb_data)

    # Apply remapping of specific footprint coordinates, use PCB schematic style to center the design
    remapped_df = KiCadUtils.apply_remapping_v2(results, 'forearm-pattern', shape_key, style, offset, flip_y, True)

    # Update the PCB file with the new electrode coordinates
    print("=== Updating PCB file with shape coordinates ===")
    data_df = remapped_df[remapped_df['label'] == shape_key]
    KiCadUtils.update_footprint(pcb_filepath, data_df, pcb_data[shape_key]['footprint'])
    print("Done updating PCB file. Please open the PCB editor to view the changes.")
