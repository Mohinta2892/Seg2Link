from collections import OrderedDict
from dataclasses import dataclass
from typing import Tuple, List, Union, Dict, Optional, Set

import numpy as np
import skimage as ski
from numpy import ndarray
from scipy.spatial import KDTree
from skimage.measure import regionprops

from seg2link.cache_bbox import array_isin_labels_quick, NoLabelError
from seg2link import config
from seg2link.link_by_overlap import match_return_seg_img
from seg2link.watersheds import dist_watershed

if config.DEBUG:
    pass

@dataclass
class DivideMode:
    _2D: str = "2D"
    _2D_Link: str = "2D Link"
    _3D: str = "3D"


class NoDivisionError(Exception):
    pass

BBox2D = Tuple[slice, slice]
BBox = Tuple[slice, slice, slice]

def segment_link(label_subregion: ndarray, max_division: int, pre_region: Optional[ndarray], max_label: int):
    seg = segment_one_cell_2d_watershed(label_subregion, max_division)
    if pre_region is None:
        return seg
    else:
        return match_return_seg_img(pre_region, seg[..., 0], max_label, ratio_overlap=0.5)[..., np.newaxis]


def segment_one_cell_2d_watershed(labels_img3d: ndarray, max_division: int = 2) -> ndarray:
    """Input: a 3D array with shape (x,x,1). Segmentation is based on watershed"""
    result = np.zeros_like(labels_img3d, dtype=np.uint16)
    seg2d = dist_watershed(labels_img3d[..., 0], h=2)
    result[..., 0] = merge_tiny_labels(seg2d, max_division)
    return result


def separate_one_label_r1(seg_img2d: ndarray, label: int, max_label: int) -> Tuple[ndarray, List[int]]:
    sub_region, slice_subregion = get_subregion_2d(seg_img2d, label)

    seg2d = dist_watershed(sub_region, h=2)
    return keep_largest_label_unchange(max_label, seg2d, seg_img2d, slice_subregion)


def keep_largest_label_unchange(max_label, seg2d, seg_img2d, slice_subregion: Union[slice, BBox2D]=slice(None)):
    seg2d, other_labels = _suppress_largest_label(seg2d)
    smaller_regions = seg2d > 0
    seg_img2d[slice_subregion][smaller_regions] = seg2d[smaller_regions] + max_label
    return seg_img2d, other_labels


def separate_one_cell_3d(sub_region: ndarray) -> ndarray:
    return ski.measure.label(sub_region, connectivity=3)


def _suppress_largest_label(seg: ndarray) -> Tuple[ndarray, List[int]]:
    """Revise the _labels: largest label (of area): l = 0; _labels > largest label: l = l - 1"""
    regions = regionprops(seg)
    max_idx = max(range(len(regions)), key=lambda k: regions[k].area)
    max_label = regions[max_idx].label
    seg[seg == max_label] = 0
    seg[seg > max_label] -= 1
    other_labels = [region.label for region in regions if region.label != max_label]
    other_labels_ = np.array(other_labels)
    other_labels_[other_labels_ > max_label] -= 1
    return seg, other_labels_.tolist()


def merge_tiny_labels(seg2d: ndarray, max_division: int) -> ndarray:
    """Merge tiny regions with other regions
    """
    if max_division == "Inf":
        max_division = float("inf")
    regions = regionprops(seg2d)
    num_labels_remove = len(regions) - max_division if len(regions) > max_division else 0
    if num_labels_remove == 0:
        return seg2d

    sorted_idxes: List[int] = sorted(range(len(regions)), key=lambda k: regions[k].area)
    sorted_coords = OrderedDict({regions[k].label: regions[k].coords for k in sorted_idxes})
    sorted_regions = SortedRegion(sorted_coords, seg2d)
    for i in range(num_labels_remove):
        sorted_regions.remove_tiny()
    return sorted_regions.seg2d


class SortedRegion():
    def __init__(self, coords: Dict[int, ndarray], seg2d: ndarray):
        self.coords = coords  # OrderedDict: sorted coords from small region to big region
        self.seg2d = seg2d

    def remove_tiny(self):
        coords = iter(self.coords.items())
        label_ini, smallest_coord = next(coords)
        label_tgt = label_ini
        dist_min = np.inf
        for label, coord in coords:
            dist = min_dist_knn_scipy(smallest_coord, coord)
            if dist < dist_min:
                dist_min = dist
                label_tgt = label
        self.coords[label_tgt] = np.vstack((self.coords[label_tgt], self.coords.pop(label_ini)))
        self.seg2d[self.seg2d == label_ini] = label_tgt


def min_dist_knn_scipy(coord1, coord2):
    tree = KDTree(coord2)
    return np.min(tree.query(coord1, k=1)[0])


def get_subregion2d_and_preslice(labels_img3d: ndarray, label: Union[int, List[int]], layer_from0: int) \
        -> Tuple[ndarray, BBox, Optional[ndarray]]:
    subregion_2d, bbox = get_subregion_2d(labels_img3d[..., layer_from0], label)
    slice_subregion = bbox[0], bbox[1], slice(layer_from0, layer_from0 + 1)
    if layer_from0 == 0:
        pre_region_2d = None
    else:
        pre_region_2d = labels_img3d[bbox[0], bbox[1], layer_from0 - 1].copy()

    return subregion_2d[:, :, np.newaxis], slice_subregion, pre_region_2d


def bbox_2D_quick(img_2d: ndarray) -> BBox2D:
    r = np.any(img_2d, axis=1)
    if not np.any(r):
        raise NoLabelError
    rmin, rmax = np.where(r)[0][[0, -1]]

    c = np.any(img_2d[rmin:rmax + 1, :], axis=0)
    cmin, cmax = np.where(c)[0][[0, -1]]

    return slice(rmin, rmax+1), slice(cmin, cmax+1)


def get_subregion_2d(labels_img2d: ndarray, label: Union[int, List[int]]) -> Tuple[
    ndarray, BBox2D]:
    """Get the subregion (bbox) and the corresponding slice for the subregion in a 2d label image
    """
    subregion = array_isin_labels_quick(label, labels_img2d)
    bbox = bbox_2D_quick(subregion)
    return subregion[bbox], bbox




