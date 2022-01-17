import cProfile
import os
import pstats
import traceback
from inspect import signature
from io import StringIO
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Union, Sequence, Set

import cv2
import numpy as np
from numpy import ndarray
from scipy.ndimage import grey_dilation

import config

import atexit
import line_profiler
lprofile = line_profiler.LineProfiler()
atexit.register(lprofile.print_stats)


def qprofile(func):
    """Print runtime information in a function

    References
    ----------
    Modified from the code here: https://stackoverflow.com/questions/40132630/python-cprofiler-a-function
    Author: Sanket Sudake
    """

    def profiled_func(*args, **kwargs):
        para_num = len(signature(func).parameters)

        if not config.debug:
            return func() if para_num == 0 else func(*args, **kwargs)

        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func() if para_num == 0 else func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            s = StringIO()
            ps = pstats.Stats(profile, stream=s).strip_dirs().sort_stats('cumulative')
            ps.print_stats(15)
            print(s.getvalue())

    return profiled_func


def load_image(path: Path) -> ndarray:
    img_file_path = get_files(path)
    img = []
    for img_path in img_file_path:
        img.append(cv2.imread(img_path, -1))
    img_array = np.array(img).transpose((1, 2, 0))
    return img_array


def get_files(path: Path) -> List[str]:
    """Return all paths of .tiff or .tif files"""
    return [str(file) for file in sorted(path.glob("*.tif*"))]


def shorten_filename(foldername: str, new_length: int):
    for filename in os.listdir(foldername):
        print(filename[-new_length:])
        os.rename(os.path.join(foldername, filename), os.path.join(foldername, filename[-new_length:]))


def dilation_scipy(label_image: ndarray, filter_size: Tuple[int, int, int]) -> ndarray:
    """3D dilation using scipy, quicker than dilation_opencv"""
    return grey_dilation(label_image, filter_size)


def add_blank_lines(string: str, max_lines: int) -> str:
    num_lines = string.count("\n") + 1
    if num_lines < max_lines:
        return string + "\n" * (max_lines - num_lines)
    else:
        return string


def print_information(operation: Optional[str] = None, print_errors: bool = True) -> Callable:
    def deco(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                if operation is not None:
                    print(operation)
                func(*args, **kwargs)
            except Exception:
                if print_errors:
                    print(f"!!!Error occurred in {func.__name__}()!!!")
                    print(traceback.format_exc())
                    raise

        return wrapper

    return deco


def make_folder(path_i: Path) -> Path:
    if not path_i.exists():
        path_i.mkdir()
    return path_i


class TinyCells:
    def __init__(self, image3d: ndarray):
        labels, areas = np.unique(image3d, return_counts=True)
        idxes_sorted = sorted(range(1, len(labels)), key=lambda i: areas[i], reverse=True)
        self.sorted_labels = labels[idxes_sorted]
        self.sorted_areas = areas[idxes_sorted]

    def min_area(self, max_cell_num: int = 65535) -> Tuple[int, int]:
        """Return the minimum areas and the number of labels to be deleted"""
        if max_cell_num > len(self.sorted_labels):
            min_area_ = self.sorted_areas[-1]
            del_num = 0
        else:
            min_area_ = self.sorted_areas[max_cell_num - 1]
            del_num = len(self.sorted_labels) - max_cell_num
        return min_area_, del_num

    def remove_tiny_cells(self, image3d: ndarray, max_cell_num: int):
        """Deprecated as slow"""
        image3d[np.isin(image3d, self.sorted_labels[max_cell_num:])] = 0
        return image3d

    def remove_tiny_cells_quick(self, image3d: ndarray, max_cell_num: int):
        maps = np.arange(0, np.max(self.sorted_labels) + 1)
        maps[np.isin(maps, self.sorted_labels[max_cell_num:])] = 0
        return maps[image3d]

    def remove_and_relabel(self, image3d: ndarray, max_cell_num: Optional[int] = None) -> ndarray:
        maps = np.arange(0, np.max(self.sorted_labels) + 1)
        if max_cell_num is None:
            self.relabel_sorted_labels(maps, self.sorted_labels)
        else:
            maps[np.isin(maps, self.sorted_labels[max_cell_num:])] = 0
            self.relabel_sorted_labels(maps, self.sorted_labels[:max_cell_num])
        return maps[image3d]

    def relabel_sorted_labels(self, maps: ndarray, sorted_labels: ndarray) -> int:
        """Relabel according to areas (descending)"""
        cell_num = len(sorted_labels)
        ori_labels = sorted_labels.tolist()
        tgt_labels = list(range(1, cell_num + 1))
        maps_ = maps.copy()
        for o, t in zip(ori_labels, tgt_labels):
            if o != t:
                maps[maps_ == o] = t

    def relabel_minimize_change(self, maps, max_cell_num):
        """Unused"""
        cell_num = len(self.sorted_labels[:max_cell_num])
        ori_labels = [l for l in self.sorted_labels[:max_cell_num] if l > cell_num]
        tgt_labels = [i for i in range(1, cell_num + 1) if i not in sorted(self.sorted_labels[:max_cell_num])]
        if len(ori_labels) != 0:
            for o, t in zip(ori_labels, tgt_labels):
                maps[maps == o] = t


def replace(labels_old: Union[int, Set[int]], label_new: int, array: ndarray) -> ndarray:
    if isinstance(labels_old, set):
        array[np.isin(array, list(labels_old))] = label_new
    else:
        array[array == labels_old] = label_new
    return array