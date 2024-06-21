function [x, y, r] = getElectrodeCoordinatesFromDXF(filename, radius)
% GETELECTRODECOORDINATESFROMDXF Extract x and y coordinates of electrodes from a DXF file.
%
%   [x, y, r] = getElectrodeCoordinatesFromDXF(filename, radius) reads the
%   specified DXF file and extracts the x and y coordinates of the electrode
%   footprints that match the specified diameter.
%
%   Arguments:
%       filename (char) - Name of the DXF file.
%       diameter (double) - Diameter of the circles to be considered as electrodes.
%
%   Returns:
%       x (double array) - Array of x-coordinates.
%       y (double array) - Array of y-coordinates.
%
%   Example:
%       filename = 'human-arm-left_grid-v8.DXF';
%       diameter = 5.0;
%       [x, y, d] = getElectrodeCoordinatesFromDXF(filename, diameter);

arguments
    filename (1,:) char
    radius double
end

% Open the file
fid = fopen(filename, 'r');
if fid == -1
    error('Could not open file %s for reading.', filename);
end

% Read the file contents
fileContents = fread(fid, '*char')';
fclose(fid);

% Split the file contents into lines
lines = strsplit(fileContents, '\n', 'CollapseDelimiters', false);

% Initialize arrays to hold the coordinates
x = [];
y = [];
r = [];

% Flags to identify the coordinate lines
isCircle = false;
isXCoord = false;
isYCoord = false;
isRadius = false;

% Parse the file lines to extract coordinates of CIRCLE entities with specified diameter
for ii = 1:length(lines)
    if isXCoord
        xCoord = round(str2double(strtrim(lines{ii})),2);
        x = [x; xCoord]; %#ok<AGROW>
        isXCoord = false;
    elseif isYCoord
        yCoord = round(str2double(strtrim(lines{ii})),2);
        y = [y; yCoord]; %#ok<AGROW>
        isYCoord = false;
    elseif isRadius
        circleRadius = round(str2double(strtrim(lines{ii})),1);
        r = [r; circleRadius]; %#ok<AGROW>
        isRadius = false;
    end

    if contains(lines{ii}, 'CIRCLE')
        isCircle = true;
    end

    if isCircle
        if contains(lines{ii}, ' 10')
            isXCoord = true;
        elseif contains(lines{ii}, ' 20')
            isYCoord = true;
        elseif contains(lines{ii}, ' 40')
            isRadius = true;
            isCircle = false;
        end
    end
end
if ~isempty(radius)
    idx = abs(r - radius) < eps;
    r = r(idx);
    x = x(idx);
    y = y(idx);
end

T = table(x,y);
[~,idx] = unique(T,'rows');
x = x(idx);
y = y(idx);
r = r(idx);
end
