clear;
clc;

FILENAME_DXF = 'human-arm-left_grid-v8.DXF';
ELEC_RADIUS = 1.5;


[x, y, r] = getElectrodeCoordinatesFromDXF(FILENAME_DXF, ELEC_RADIUS);
fig = plotDXFparsedLayout(x(1:128),y(1:128));

%%