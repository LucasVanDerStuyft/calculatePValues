import json
import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ranksums


def add_files_to_set(path, file_paths, enginename, instance_range):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)) and enginename in file and "Brussel" in file:
            instance_size = int(file.split("_")[3])
            if instance_range[0] <= instance_size <= instance_range[1]:
                file_path = os.path.join(path, file)
                file_paths.append(file_path)


def get_nested_value(data, keys):
    if not keys:
        return data
    return get_nested_value(data.get(keys[0], {}), keys[1:])


def read_json_file(file_path, keys):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return get_nested_value(data, keys)


def calculate_param(param, variant, key):
    if (variant == "PDP" or variant == "PDP_TW") and key[0] == "CargoAnalysisResult":
        return -1
    if isinstance(param, dict):
        return np.mean(list(param.values()))
    else:
        return param


def make_pvalues_table(necessary_keys, vrpvariants, instance_range):
    pvalues = []
    names = []
    for keys in necessary_keys:
        pvalues_row = []
        for vrpvariant in vrpvariants:
            file_paths_gh = []
            file_paths_ors = []
            add_files_to_set(
                "C:\\Users\\lucas\\Documents\\masterproef2023_2024\\metavrp-toolkit\\cli\\etc\\demoproblems\\analysisResultsJSON\\" + vrpvariant + "\\",
                file_paths_gh, "ORS", instance_range)
            add_files_to_set(
                "C:\\Users\\lucas\\Documents\\masterproef2023_2024\\metavrp-toolkit\\cli\\etc\\demoproblems\\analysisResultsJSON\\" + vrpvariant + "\\",
                file_paths_ors, "GH", instance_range)

            values_gh = [calculate_param(read_json_file(file_gh, keys), vrpvariant, keys) for file_gh in file_paths_gh]
            values_ors = [calculate_param(read_json_file(file_ors, keys), vrpvariant, keys) for file_ors in file_paths_ors]

            if values_ors.__contains__(-1):
                pvalue = 2.0
            else:
                _, pvalue = ranksums(values_gh, values_ors)
            pvalues_row.append(pvalue)
        names.append(keys[1])
        pvalues.append(pvalues_row)
    return pvalues, names


def create_pvalues_table(pvalues_small, pvalues_large, vrpvariants, names, instance_ranges):
    fig, axes = plt.subplots(2, 1, figsize=(13, 12))
    for ax, pvalues, instance_range in zip(axes, [pvalues_small, pvalues_large], instance_ranges):
        transposed_pvalues = list(map(list, zip(*pvalues)))
        rounded_pvalues = [[round(val, 4) for val in row] for row in transposed_pvalues]

        col_labels = vrpvariants.copy()
        col_labels.insert(0, "Metric name")

        threshold = 0.1
        cell_colors = [['green' if value < threshold else 'white' for value in row] for row in rounded_pvalues]
        white_colors = ['white'] * len(cell_colors[0])
        colour_data = list(zip(white_colors, *cell_colors))
        rounded_pvalues = [[round(val, 4) if val != 2 else '' for val in row] for row in transposed_pvalues]
        table_data = list(zip(names, *rounded_pvalues))

        # style for the table
        table = ax.table(cellText=table_data, cellLoc="center", colLabels=col_labels, loc='center',
                         cellColours=colour_data)
        ax.axis('off')
        instance_range_str = f"Instances Range: {instance_range[0]}-{instance_range[1]}"
        ax.set_title(f"P-values GraphHopper vs Openrouteservice: Brussels\n{instance_range_str}")
        table.auto_set_column_width([0])
        table.auto_set_font_size(False)
        table.set_fontsize(11)

    figname = "GHvsORS/GHvsORS_shipments_Brussel.png"
    #figname="test"
    plt.savefig(figname)
    plt.show()


small_instance_range = (1, 100)
large_instance_range = (200, 500)
instance_ranges = [small_instance_range, large_instance_range]

list_keys = [['WorkingShiftAnalysisResult', 'meanworkingShift'],
             ['WorkingShiftAnalysisResult', 'stddevWorkingShifts'],
             ['WorkingShiftAnalysisResult', 'shortestWorkingShift'],
             ['WorkingShiftAnalysisResult', 'longestWorkingShift'],
             ['RouteCompositionAnalysisResult', 'totalDistanceMeters'],
             ['RouteCompositionAnalysisResult', 'runTime'],
             ['RouteCompositionAnalysisResult', 'failureRate'],
             ['RouteCompositionAnalysisResult', 'numberOfRoutes'],
             ['RouteCompositionAnalysisResult', 'stopsLongestRoute'],
             ['RouteCompositionAnalysisResult', 'stopsShortestRoute'],
             ['RouteCompositionAnalysisResult', 'meanStops'],
             ['RouteCompositionAnalysisResult', 'stdDevStops'],
             ['VisualAttractivenessAnalysisResult', 'meanDistanceToGeographicCenter'],
             ['VisualAttractivenessAnalysisResult', 'meanTravelTimeBetweenStops'],
             ['VisualAttractivenessAnalysisResult', 'meanDistanceToConvexHull'],
             ['CargoAnalysisResult', 'biggestLoad'],
             ['CargoAnalysisResult', 'biggestLoadVolume'],
             ['CargoAnalysisResult', 'smallestLoad'],
             ['CargoAnalysisResult', 'smallestLoadVolume'],
             ['CargoAnalysisResult', 'meanLoad'],
             ['CargoAnalysisResult', 'meanLoadVolume']]

#variants = ["Priority", "Shift", "Skills", "Skills_TW", "TW"]
variants = ["Capacity", "Capacity_TW", "MultiDepot", "Open", "PDP", "PDP_TW", "Sameaddresses"]

pvaluessmall, names = make_pvalues_table(list_keys, variants, small_instance_range)
pvalueslarge, names = make_pvalues_table(list_keys, variants, large_instance_range)

array_small = np.array(pvaluessmall)
array_large = np.array(pvalueslarge)

create_pvalues_table(array_small, array_large, variants, names, instance_ranges)
