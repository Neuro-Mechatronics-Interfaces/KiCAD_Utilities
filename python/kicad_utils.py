import os
import re
import ezdxf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class KiCadUtils:

    @staticmethod
    def get_coordinates_from_dxf(filename, radius_dict=None, flip_y=True, visualize=False, export=True):
        """
        Extract x and y coordinates of circles from a DXF file based on specified radii and return as a DataFrame.

        Parameters:
        filename (str): Name of the DXF file.
        radius_dict (dict, optional): Dictionary with custom names as keys and radii as values.
                                      Default is None, which means all shapes are in the same category.
        flip_y (bool, optional): If True, flips the y-coordinates. Default is True.
        visualize (bool, optional): If True, plots the extracted coordinates. Default is False.
        export (bool, optional): If True, exports the extracted coordinates to a CSV file. Default is True.

        Returns:
        DataFrame: DataFrame with columns 'x', 'y', 'r', 'label', and 'channel'.
        """
        # Open the DXF file
        doc = ezdxf.readfile(filename)
        msp = doc.modelspace()

        # Initialize the results dictionary
        if radius_dict is None:
            radius_dict = {'shape': None}

        results = {'x': [], 'y': [], 'r': [], 'label': []}

        # Iterate through all circle entities
        for entity in msp.query('CIRCLE'):
            x = round(entity.dxf.center.x, 2)
            y = round(entity.dxf.center.y, 2)
            r = round(entity.dxf.radius, 1)

            if flip_y:
                y = -y

            matched = False
            for name, radius in radius_dict.items():
                if radius is None or np.isclose(r, radius):
                    results['x'].append(x)
                    results['y'].append(y)
                    results['r'].append(r)
                    results['label'].append(name)
                    matched = True
                    break

            # If no specific radius matched and a general shape category exists
            if not matched and 'shape' in radius_dict:
                results['x'].append(x)
                results['y'].append(y)
                results['r'].append(r)
                results['label'].append('shape')

        # Create a DataFrame and drop duplicates
        df = pd.DataFrame(results).drop_duplicates().reset_index(drop=True)

        # Because the duplicates have been removed, we can now include a new header called 'channel' and assign the channel number
        # to each electrode. This is done by grouping the dataframe by the 'label' column and then assigning a channel number to each
        # electrode in the group.
        df['channel'] = df.groupby('label').cumcount() + 1


        # Debugging output
        for label in df['label'].unique():
            print(f"\nExtracted {label} Coordinates:")
            for index, row in df[df['label'] == label].iterrows():
                print(f"  X: {row['x']}, Y: {row['y']}, R: {row['r']}")
        print("\n")

        # Visualization
        if visualize:
            plt.figure(figsize=(10, 8))
            plt.gca().invert_yaxis()  # Invert y-axis to match DXF coordinate system

            colors = {'electrode': 'blue', 'grommet': 'red', 'shape': 'green'}
            for label, group in df.groupby('label'):
                plt.scatter(group['x'], group['y'], s=[(r * 2) ** 2 for r in group['r']],
                            color=colors.get(label, 'black'), label=label, alpha=0.5)
                for idx, row in group.iterrows():
                    plt.text(row['x'], row['y'], f'{label[0].upper()}{idx + 1}', fontsize=9, ha='right',
                             color=colors.get(label, 'black'))

            plt.xlabel('X Coordinate')
            plt.ylabel('Y Coordinate')
            plt.title('Shapes Visualization')
            plt.legend()
            plt.grid(True)
            plt.show()

        # Export to CSV
        if export:
            for label, group in df.groupby('label'):
                csv_filename = f'{label}_coordinates.csv'
                group.to_csv(csv_filename, index=False)
                print(f"Exported {label} coordinates to {csv_filename}")

        return df

    @staticmethod
    def update_footprint_locations(filename, df, footprint_name, updated_name_tag='_updated', x_offset=0, y_offset=0, verbose=False):
        """
        Update footprint locations in a KiCad PCB file based on DataFrame.

        Parameters:
        filename (str): Name of the KiCad PCB file.
        df (DataFrame): DataFrame with columns 'x', 'y', 'r', 'label', and 'channel'.
        footprint_name (str): Name of the footprint to update.
        updated_name_tag (str, optional): Tag to append to the updated file name. Default is '_updated'.
        x_offset (float, optional): Offset to add to the x-coordinates. Default is 0.
        y_offset (float, optional): Offset to add to the y-coordinates. Default is 0.

        """
        # Apply the offset and flip y-coordinates if needed
        df['x'] = df['x'] + x_offset
        df['y'] = df['y'] + y_offset

        # Debugging output
        print("\nCoordinates to be applied to the PCB:")
        for _, row in df.iterrows():
            print(f"  X: {row['x']}, Y: {row['y']}, Channel: {row['channel']}")

        # Read the file contents
        with open(filename, 'r') as file:
            lines = file.readlines()

        # Initialize variables
        num_footprints = df.shape[0]
        footprints_updated = 0
        inside_footprint = False
        found_channel = False
        have_coordinates = False
        coordinates_line = None
        current_channel = None


        for i, line in enumerate(lines):

            if footprints_updated >= num_footprints:
                break

            # First check if inside a footprint section
            if f'(footprint "{footprint_name}"' in line and 'property' not in line:
                if verbose: print(f"1: Found footprint {footprint_name} at line {i}")
                inside_footprint = True

            # Second, look for the first occurrence inside the footprint with the coordinates, usually starting with '(at ' and save the line number
            if inside_footprint and '(at ' in line and 'property' not in line:
                old_coords = line.split('(at ')[1].split(')')[0]
                if verbose: print(f"2: Found original coordinates at line {i}: {old_coords}")
                have_coordinates = True
                coordinates_line = i

            # Third, look for the line containing the channel name/number which starts with "U"
            if inside_footprint and '(property "Reference" "' in line:
                ref = line.split('"Reference" "')[1].split('"')[0]
                new_ref = re.split(r'(\d+)', ref)
                letter = new_ref[0]
                current_channel = int(new_ref[1])
                if verbose: print(f"3: Found footprint with Reference {letter}{current_channel} at line {i}")
                found_channel = True

            # Lastly, update the coordinates if the channel number was found
            if inside_footprint and have_coordinates and found_channel:
                row = df[df['channel'] == current_channel]
                if not row.empty:
                    xi = row['x'].values[0]
                    yi = row['y'].values[0]
                    if verbose: print(f"4:   Updating coordinates for {letter}{current_channel} at line {coordinates_line}: (at {xi} {yi}) \n")
                    lines[coordinates_line] = f'\t\t(at {xi} {yi})\n'
                    footprints_updated += 1
                inside_footprint = False
                have_coordinates = False
                found_channel = False
                current_channel = None

        # Combine the lines back into a single string
        updated_contents = ''.join(lines)

        # Create the new filename
        filepath, ext = os.path.splitext(filename)
        new_filename = f"{filepath}{updated_name_tag}{ext}"

        # Write the updated contents to the new file
        with open(new_filename, 'w') as file:
            file.write(updated_contents)

        print(
            f'Updated {footprints_updated} footprints in the file (from {len(lines)} detected lines). New file saved as {new_filename}.')
        if footprints_updated < num_footprints:
            print(
                f'Warning: Only updated {footprints_updated} out of {num_footprints} footprints. Some footprints may be missing or not matched correctly.')

    @staticmethod
    def parse_remapping_file(remapping_file):
        """
        Parse the remapping file to create a dictionary of original to modified indices.

        Parameters:
        remapping_file (str): Path to the remapping file.

        Returns:
        dict: Dictionary with original indices as keys and modified indices as values.
        """
        remapping = {}
        with open(remapping_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    original, modified = line.split(':')
                    remapping[int(original.strip())] = int(modified.strip())
        return remapping

    @staticmethod
    def apply_remapping(df, remapping, label='electrode'):
        """
        Apply the remapping to the DataFrame based on channel numbers.

        Parameters:
        df (DataFrame): DataFrame with columns 'x', 'y', 'r', 'label', and 'channel'.
        remapping (dict): Dictionary with current channel numbers as keys and new channel numbers as values.
        label (str, optional): The label to filter coordinates. Default is 'electrode'.

        Returns:
        DataFrame: DataFrame with remapped coordinates and unchanged coordinates.
        """
        # Make a copy of the DataFrame to preserve the original data
        remapped_df = df.copy()

        # Filter the DataFrame by the specified label
        filtered_df = remapped_df[remapped_df['label'] == label].copy()

        # Create a mapping from new channel to the current index
        new_coords = {}
        for current_channel, new_channel in remapping.items():
            if current_channel in filtered_df['channel'].values:
                row = filtered_df[filtered_df['channel'] == current_channel]
                new_coords[new_channel] = (row['x'].values[0], row['y'].values[0], row['r'].values[0])

        # Update the coordinates based on the new channel mapping
        for new_channel, (x, y, r) in new_coords.items():
            filtered_df.loc[filtered_df['channel'] == new_channel, ['x', 'y', 'r']] = x, y, r

        # Ensure the channel numbers for the specified label go through 1 to the length of the filtered DataFrame
        filtered_df['channel'] = range(1, len(filtered_df) + 1)

        # Update the main DataFrame with the remapped channels and coordinates
        remapped_df.update(filtered_df)

        # Sort by label and channel to maintain order
        remapped_df = remapped_df.sort_values(by=['label', 'channel']).reset_index(drop=True)

        return remapped_df

    @staticmethod
    def apply_remapping_v2(df, remapping_style='8-by-8_swap', label='electrode'):
        """
        Apply the remapping to the DataFrame based on remapping style.

        Parameters:
        df (DataFrame): DataFrame with columns 'x', 'y', 'r', 'label', and 'channel'.
        label (str, optional): The label to filter coordinates. Default is 'electrode'.

        Returns:
        DataFrame: DataFrame with remapped coordinates and unchanged coordinates.
        """
        # Filter the DataFrame by the specified label
        filtered_df = df[df['label'] == label].copy()

        # Sort by x coordinate first, then by y coordinate
        filtered_df = filtered_df.sort_values(by=['y', 'x'], ascending=[False, True]).reset_index(drop=True)

        # Assign new channel numbers from 0 to n
        filtered_df['channel'] = range(0, len(filtered_df))

        # Get the number of electrodes
        num_electrodes = len(filtered_df)

        # Check if there are enough channels to reassign
        if num_electrodes >= 129:
            # Reassign the first and last channels to 129 and 130
            filtered_df.loc[0, 'channel'] = 129
            filtered_df.loc[num_electrodes - 1, 'channel'] = 130

        # Check if the remapping style requires swapping specific ranges
        if remapping_style == '8-by-8':
            # Define the ranges to be swapped
            swap_pairs = [
                (9, 16, 17, 24),
                (17, 24, 33, 40),
                (49, 56, 25, 32),
                (65, 72, 33, 40),
                (81, 88, 41, 48),
                (97, 104, 49, 56),
                (113, 120, 57, 64),

                (97, 104, 73, 80),
                (113, 120, 89, 96),
                (113, 120, 105, 112)
            ]

            # Perform the swapping for specific ranges
            for start1, end1, start2, end2 in swap_pairs:
                range1_indices = filtered_df[
                    (filtered_df['channel'] >= start1) & (filtered_df['channel'] <= end1)].index
                range2_indices = filtered_df[
                    (filtered_df['channel'] >= start2) & (filtered_df['channel'] <= end2)].index

                temp = filtered_df.loc[range1_indices, ['x', 'y', 'r']].values.copy()
                filtered_df.loc[range1_indices, ['x', 'y', 'r']] = filtered_df.loc[
                    range2_indices, ['x', 'y', 'r']].values
                filtered_df.loc[range2_indices, ['x', 'y', 'r']] = temp

        if remapping_style == '8-by-8_swap':
            # Define the ranges to be swapped
            swap_pairs = [
                (9, 16, 17, 24),
                (17, 24, 33, 40),
                (49, 56, 25, 32),
                (65, 72, 33, 40),
                (81, 88, 41, 48),
                (97, 104, 49, 56),
                (113, 120, 57, 64),
                (97, 104, 73, 80),
                (113, 120, 89, 96),
                (113, 120, 105, 112)
            ]

            # Perform the swapping for specific ranges
            for start1, end1, start2, end2 in swap_pairs:
                range1_indices = filtered_df[
                    (filtered_df['channel'] >= start1) & (filtered_df['channel'] <= end1)].index
                range2_indices = filtered_df[
                    (filtered_df['channel'] >= start2) & (filtered_df['channel'] <= end2)].index

                temp = filtered_df.loc[range1_indices, ['x', 'y', 'r']].values.copy()
                filtered_df.loc[range1_indices, ['x', 'y', 'r']] = filtered_df.loc[
                    range2_indices, ['x', 'y', 'r']].values
                filtered_df.loc[range2_indices, ['x', 'y', 'r']] = temp

            # Swap channels 1-64 with 65-128
            range1_indices = filtered_df[(filtered_df['channel'] >= 1) & (filtered_df['channel'] <= 64)].index
            range2_indices = filtered_df[(filtered_df['channel'] >= 65) & (filtered_df['channel'] <= 128)].index

            temp = filtered_df.loc[range1_indices, ['x', 'y', 'r']].values.copy()
            filtered_df.loc[range1_indices, ['x', 'y', 'r']] = filtered_df.loc[
                range2_indices, ['x', 'y', 'r']].values
            filtered_df.loc[range2_indices, ['x', 'y', 'r']] = temp

        # Update the main DataFrame with the remapped channels and coordinates
        df.update(filtered_df)

        # Sort by label and channel to maintain order
        df = df.sort_values(by=['label', 'channel']).reset_index(drop=True)

        return df

    @staticmethod
    def visualize_footprints(df):
        """
        Visualize the coordinates from the results dictionary.

        :param df:
        :return:
        """
        # Visualization
        if True:
            plt.figure(figsize=(10, 8))
            plt.gca().invert_yaxis()  # Invert y-axis to match DXF coordinate system

            colors = {'electrode': 'blue', 'grommet': 'red', 'shape': 'green'}
            for label, group in df.groupby('label'):
                plt.scatter(group['x'], group['y'], s=[(r * 2) ** 2 for r in group['r']],
                            color=colors.get(label, 'black'), label=label, alpha=0.5)
                for idx, row in group.iterrows():
                    plt.text(row['x'], row['y'], str(row['channel']), fontsize=9, ha='right',
                             color=colors.get(label, 'black'))

            plt.xlabel('X Coordinate')
            plt.ylabel('Y Coordinate')
            plt.title('Shapes Visualization')
            plt.legend()
            plt.grid(True)
            plt.show()


