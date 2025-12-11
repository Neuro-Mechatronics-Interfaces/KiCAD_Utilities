"""
Update KiCad PCB File from DXF

This script extracts circular element coordinates from a DXF file and updates
corresponding footprint locations in a KiCad PCB file. Features include:
- Interactive file selection dialogs
- Visual element selection from DXF
- Configurable coordinate transformations
- Support for multiple element types (electrodes, mounting holes, etc.)

Author: jshulgac@andrew.cmu.edu
Last updated: 2025-12-11
"""

import os
import sys
from pathlib import Path
from tkinter import Tk, filedialog, simpledialog, messagebox
from kicad_utils import KiCadUtils, kicad_pcb_schematic
import re


def discover_footprints_in_pcb(pcb_filepath):
    """Scan PCB file and return unique footprint names."""
    footprints = set()
    
    try:
        with open(pcb_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # Match footprint declarations
                match = re.search(r'^\s*\(footprint\s+"([^"]+)"', line)
                if match:
                    footprints.add(match.group(1))
    except Exception as e:
        print(f"Warning: Could not scan PCB file for footprints: {e}")
        return []
    
    return sorted(list(footprints))


def select_file(title, file_types):
    """Open file dialog and return selected file path."""
    root = Tk()
    root.withdraw()  # Hide the root window
    root.attributes('-topmost', True)  # Bring dialog to front
    
    file_path = filedialog.askopenfilename(
        title=title,
        filetypes=file_types
    )
    root.destroy()
    
    return file_path if file_path else None


def select_elements(available_labels):
    """Allow user to select which element types to process."""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    message = "Available circular elements found:\n\n"
    for i, label in enumerate(available_labels, 1):
        message += f"{i}. {label}\n"
    message += "\nEnter the number of the element type to update (or press Cancel to exit):"
    
    result = simpledialog.askinteger(
        "Select Element Type",
        message,
        minvalue=1,
        maxvalue=len(available_labels),
        parent=root
    )
    
    root.destroy()
    
    if result is None:
        return None
    
    return available_labels[result - 1]


def get_transformation_params():
    """Get coordinate transformation parameters from user."""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # PCB schematic style
    style_msg = "Select KiCad PCB schematic style:\n1. A4\n2. A3\n3. A2 (default)"
    style_choice = simpledialog.askinteger(
        "Schematic Style",
        style_msg,
        initialvalue=3,
        minvalue=1,
        maxvalue=3,
        parent=root
    )
    
    if style_choice is None:
        root.destroy()
        return None
    
    styles = {1: 'A4', 2: 'A3', 3: 'A2'}
    style = styles.get(style_choice, 'A2')
    
    # Offset
    offset_x = simpledialog.askfloat(
        "X Offset",
        "Enter X offset (mm):",
        initialvalue=0.0,
        parent=root
    )
    
    if offset_x is None:
        root.destroy()
        return None
    
    offset_y = simpledialog.askfloat(
        "Y Offset",
        "Enter Y offset (mm):",
        initialvalue=0.0,
        parent=root
    )
    
    if offset_y is None:
        root.destroy()
        return None
    
    # Flip Y
    flip_y = messagebox.askyesno(
        "Flip Y Axis",
        "Flip Y coordinates?",
        parent=root
    )
    
    root.destroy()
    
    return {
        'style': style,
        'offset': (offset_x, offset_y),
        'flip_y': flip_y
    }


def main():
    """Main execution function."""
    print("=" * 60)
    print("KiCad PCB Updater from DXF")
    print("=" * 60)
    
    # Define element metadata
    pcb_data = {
        '3mm-electrode': {
            'footprint': 'CustomComponents:1625-5-57-15_D3.18mm_disk',
            'radius': 1.5,
            'entity': 'CIRCLE'
        },
        '6mm-electrode': {
            'footprint': 'CustomComponents:2036-3-57-15_D5.99mm_6.25mmPad_6.3mmMask',
            'radius': 3.0,
            'entity': 'CIRCLE'
        },
        'm3-mount': {
            'footprint': 'MountingHole:MountingHole_3.2mm_M3_DIN965_Pad',
            'radius': 1.5,
            'entity': 'CIRCLE'
        },
        'pcb-m3-mount': {
            'footprint': 'MountingHole:MountingHole_3.2mm_M3_DIN965_Pad',
            'radius': 2.0,
            'entity': 'CIRCLE'
        },
    }
    
    # Step 1: Select DXF file
    print("\nStep 1: Select DXF file")
    dxf_filepath = select_file(
        "Select DXF File",
        [("DXF files", "*.dxf *.DXF"), ("All files", "*.*")]
    )
    
    if not dxf_filepath:
        print("No DXF file selected. Exiting.")
        return
    
    print(f"Selected: {Path(dxf_filepath).name}")
    
    # Step 2: Select PCB file
    print("\nStep 2: Select KiCad PCB file")
    pcb_filepath = select_file(
        "Select KiCad PCB File",
        [("KiCad PCB files", "*.kicad_pcb"), ("All files", "*.*")]
    )
    
    if not pcb_filepath:
        print("No PCB file selected. Exiting.")
        return
    
    print(f"Selected: {Path(pcb_filepath).name}")
    
    # Step 3: Extract coordinates from DXF
    print("\nStep 3: Extracting circular elements from DXF...")
    results = KiCadUtils.get_coordinates_from_dxf(dxf_filepath, pcb_data, verbose=False)
    
    if results is None or results.empty:
        print("No circular elements found in DXF file. Exiting.")
        return
    
    # Step 4: Select which element type to update
    print("\nStep 4: Select element type to update")
    available_labels = results['label'].unique().tolist()
    
    selected_label = select_elements(available_labels)
    
    if not selected_label:
        print("No element selected. Exiting.")
        return
    
    print(f"Selected element type: {selected_label}")
    
    # Verify the footprint exists in metadata
    if selected_label not in pcb_data:
        print(f"\nWarning: '{selected_label}' not found in metadata.")
        print("Available metadata keys:", list(pcb_data.keys()))
        
        # Discover available footprints in the PCB file
        print("\nScanning PCB file for available footprints...")
        available_footprints = discover_footprints_in_pcb(pcb_filepath)
        
        if available_footprints:
            print(f"Found {len(available_footprints)} unique footprint types:")
            for fp in available_footprints:
                print(f"  - {fp}")
        
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        footprint_list_text = "\n".join([f"  {fp}" for fp in available_footprints[:10]])
        if len(available_footprints) > 10:
            footprint_list_text += f"\n  ... and {len(available_footprints) - 10} more"
        
        proceed = messagebox.askyesno(
            "Footprint Not Found",
            f"No footprint metadata found for '{selected_label}'.\n\n"
            "This element may have been auto-detected. You can still proceed,\n"
            "but you'll need to manually specify the footprint name.\n\n"
            f"Available footprints in PCB file:\n{footprint_list_text}\n\n"
            "Continue?",
            parent=root
        )
        
        root.destroy()
        
        if not proceed:
            print("Operation cancelled.")
            return
        
        # Ask for footprint name
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        footprint_name = simpledialog.askstring(
            "Footprint Name",
            f"Enter the exact KiCad footprint name for '{selected_label}':\n\n"
            "(Check console output for available footprints)",
            parent=root
        )
        
        root.destroy()
        
        if not footprint_name:
            print("No footprint name provided. Exiting.")
            return
        
        pcb_data[selected_label] = {
            'footprint': footprint_name,
            'radius': results[results['label'] == selected_label]['r'].iloc[0],
            'entity': 'CIRCLE'
        }
    
    # Step 5: Get transformation parameters
    print("\nStep 5: Configure coordinate transformation")
    transform_params = get_transformation_params()
    
    if not transform_params:
        print("Transformation cancelled. Exiting.")
        return
    
    print(f"Style: {transform_params['style']}")
    print(f"Offset: {transform_params['offset']}")
    print(f"Flip Y: {transform_params['flip_y']}")
    
    # Step 6: Apply coordinate transformation
    print("\nStep 6: Applying coordinate transformation...")
    remapped_df = KiCadUtils.apply_remapping_v2(
        results,
        remapping_style='forearm-pattern',
        label=selected_label,
        style=transform_params['style'],
        offset=transform_params['offset'],
        flip_y=transform_params['flip_y'],
        verbose=True
    )
    
    # Step 7: Update PCB file
    print("\nStep 7: Updating PCB file...")
    data_df = remapped_df[remapped_df['label'] == selected_label]
    
    print(f"Updating {len(data_df)} footprints of type: {pcb_data[selected_label]['footprint']}")
    
    KiCadUtils.update_footprint(
        pcb_filepath,
        data_df,
        pcb_data[selected_label]['footprint']
    )
    
    print("\n" + "=" * 60)
    print("✓ PCB update complete!")
    print(f"Updated file saved with '_updated' suffix")
    print("Open the file in KiCad PCB editor to verify changes.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
