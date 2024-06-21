%EXAMPLE_UPDATE_ELECTRODE_PCB_FROM_DXF  Example indicating how to update PCB layout from parsing DXF coordinates and inserting to KICAD_PCB file.
clear;
clc;

%% 1. Extract coordinates and plot them for sanity-check.
FILENAME_DXF = 'human-arm-left_grid-v8.DXF';
FILENAME_KICAD_PCB = '128ch-hdemg-sleeve.kicad_pcb';
ELECTRODE_FOOTPRINT_ID = sprintf('\t("CustomComponents:1625-5-57-15_D3.18mm_disk")\r\n');

ELEC_RADIUS = 1.5;


[x, y, r] = getElectrodeCoordinatesFromDXF(FILENAME_DXF, ELEC_RADIUS);
fig = plotDXFparsedLayout(x(1:128),y(1:128));

%% 2. ??? Get the actual channel mapping so you can re-order `x` and `y`

%% 3. Apply the channel-mapped `x` and `y` to the new `kicad_pcb` file.
updateFootprintLocations(FILENAME_KICAD_PCB, x, y, ELECTRODE_FOOTPRINT_ID, ...
    'UpdatedNameTag', '_updated_v1');