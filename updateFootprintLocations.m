function updateFootprintLocations(filename, x, y, footprintName, options)
    % UPDATEFOOTPRINTLOCATIONS Update footprint locations in a KiCad PCB file.
    %
    %   updateFootprintLocations(filename, x, y, footprintName) updates the
    %   coordinates of the specified footprint in the given KiCad PCB file.
    %
    %   updateFootprintLocations(filename, x, y, footprintName, options) allows
    %   additional options to be specified using name-value pairs.
    %
    %   Arguments:
    %       filename (char) - Name of the KiCad PCB file.
    %       x (double array) - Array of x-coordinates for the footprints.
    %       y (double array) - Array of y-coordinates for the footprints.
    %       footprintName (char) - Name of the footprint to update.
    %       options (struct) - Optional parameters:
    %           'UpdatedNameTag' (char) - Tag to append to the updated file name.
    %
    %   Example:
    %       filename = '128ch-hdemg-sleeve.kicad_pcb';
    %       footprintName = sprintf('\t("CustomComponents:1625-5-57-15_D3.18mm_disk")\r\n');
    %       x = ones(128, 1);
    %       y = zeros(128, 1);
    %       options.UpdatedNameTag = '_updated';
    %       updateFootprintLocations(filename, x, y, footprintName, options);

    arguments
        filename (1,:) char
        x (:,1) double
        y (:,1) double
        footprintName (1,:) char
        options.UpdatedNameTag (1,:) char = '_updated'
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

    % Iterate through the lines and update coordinates
    numFootprints = length(x);
    footprintsUpdated = 0;
    
    for ii = 1:length(lines)
        if footprintsUpdated >= numFootprints
            break;
        end

        if contains(lines{ii}, footprintName)
            % Look for the (at <x> <y>) line
            for jj = ii+1:length(lines)
                if contains(lines{jj}, '(at ')
                    % Update the coordinates
                    lines{jj} = sprintf('\t\t(at %g %g)', x(footprintsUpdated + 1), y(footprintsUpdated + 1));
                    footprintsUpdated = footprintsUpdated + 1;
                    break;
                end
            end
        end
    end

    % Combine the lines back into a single string
    updatedContents = strjoin(lines, '\n');

    % Create the new filename
    [filepath, name, ext] = fileparts(filename);
    newFilename = fullfile(filepath, [name, options.UpdatedNameTag, ext]);

    % Write the updated contents to the new file
    fid = fopen(newFilename, 'w');
    if fid == -1
        error('Could not open file %s for writing.', newFilename);
    end
    fwrite(fid, updatedContents);
    fclose(fid);

    fprintf('Updated %d footprints in the file. New file saved as %s.\n', footprintsUpdated, newFilename);
end
