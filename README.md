# KiCAD_Utilities

MATLAB or Python functions/scripts to help with things like electrode coordinate placement etc. on PCB layouts in KiCAD specifically.

## Features

- **Extract coordinates from DXF files**: Parse circular elements (electrodes, mounting holes) from CAD drawings
- **Interactive GUI**: File dialogs and element selection for easy workflow
- **Update KiCad PCB files**: Automatically update footprint locations based on DXF coordinates
- **Coordinate transformations**: Apply offsets, flipping, and centering based on PCB schematic style
- **Flexible element mapping**: Supports multiple element types with configurable metadata

## Python Usage

### Interactive Mode (Recommended)

Run the script and follow the GUI prompts:

```bash
cd python
python example_update_pcb_from_dxf.py
```

The script will guide you through:
1. Selecting a DXF file
2. Selecting a KiCad PCB file
3. Choosing which circular elements to update
4. Configuring coordinate transformations
5. Updating the PCB file

### Requirements

```bash
pip install -r python/requirements.txt
```

Required packages:
- ezdxf
- numpy
- pandas
- matplotlib

