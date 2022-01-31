import warnings
from pathlib import Path

import numpy as np
from magicgui import magicgui

from seg2link import config
from seg2link.entry_1 import load_cells, load_raw, load_mask, _npy_name, check_existence_path, show_error_msg
from seg2link.second_correction import Seg2LinkR2
from seg2link.userconfig import UserConfig

CURRENT_DIR = Path.home()
USR_CONFIG = UserConfig()


@magicgui(
    call_button="Start Seg2Link (Round #2)",
    layout="vertical",
    load_para={"widget_type": "PushButton", "text": "Load parameters (*.ini)"},
    save_para={"widget_type": "PushButton", "text": "Save parameters (*.ini)"},
    cell_value={"label": "Value of the cell region"},
    mask_value={"label": "Value of the mask region", "visible": False},
    paths_exist={"visible": False, "enabled": False},
    error_info={"widget_type": "TextEdit", "label": "Warnings:", "visible": False},
    image_size={"label": "Image size (segmentation)", "enabled": False},
    path_cells={"label": "Open image sequences: Cell regions (*.tiff):", "mode": "d"},
    path_raw={"label": "Open image sequences: Raw images (*.tiff):", "mode": "d"},
    path_mask={"label": "Open image sequences: Mask images (*.tiff):", "mode": "d", "visible": False},
    file_seg={"label": "Open segmentation file (*.npy):", "mode": "r", "filter": '*.npy'},
    enable_mask={"label": "Use the Mask images"},
    enable_cell={"label": "Use the Cell-region images"},
)
def widget_entry2(
        load_para,
        save_para,
        enable_mask=False,
        enable_cell=False,
        path_cells=CURRENT_DIR / "Cells",
        path_raw=CURRENT_DIR / "Raw",
        path_mask=CURRENT_DIR / "Mask",
        file_seg=CURRENT_DIR / "Seg.npy",
        paths_exist=["", "", "", ""],
        image_size="",
        cell_value=2,
        mask_value=2,
        error_info="",
):
    """Run some computation."""
    msg = check_existence_path(data_paths_r2())
    if msg:
        show_error_msg(widget_entry2.error_info, msg)
    else:
        cells = load_cells(cell_value, path_cells, file_cached=_npy_name(path_cells)) if enable_cell else None
        images = load_raw(path_raw, file_cached=_npy_name(path_raw))
        mask_dilated = load_mask(mask_value, path_mask, file_cached=_npy_name(path_mask)) if enable_mask else None
        segmentation = load_segmentation(file_seg)
        Seg2LinkR2(images, cells, mask_dilated, segmentation, file_seg)
        return None


widget_entry2.error_info.min_height = 70


def data_paths_r2():
    paths = [widget_entry2.path_raw.value,
             widget_entry2.file_seg.value]
    if widget_entry2.enable_mask.value:
        paths.insert(-1, widget_entry2.path_mask.value)
    if widget_entry2.path_cells.value:
        paths.insert(0, widget_entry2.path_cells.value)
    return paths


def load_segmentation(file_seg):
    segmentation = np.load(str(file_seg))
    if segmentation.dtype != config.pars.dtype_r2:
        warnings.warn(f"segmentation should has dtype {config.pars.dtype_r2}. Transforming...")
        segmentation = segmentation.astype(config.pars.dtype_r2, copy=False)
    label_shape = segmentation.shape
    widget_entry2.image_size.value = f"H: {label_shape[0]}  W: {label_shape[1]}  D: {label_shape[2]}"
    print("Segmentation shape:", label_shape, "dtype:", segmentation.dtype)
    return segmentation


@widget_entry2.enable_mask.changed.connect
def use_mask():
    visible = widget_entry2.enable_mask.value
    widget_entry2.path_mask.visible = visible
    widget_entry2.mask_value.visible = visible

    msg = check_existence_path(data_paths_r2())
    show_error_msg(widget_entry2.error_info, msg)


@widget_entry2.save_para.changed.connect
def _on_save_para_changed():
    parameters_r2 = {"path_cells": widget_entry2.path_cells.value,
                     "path_raw": widget_entry2.path_raw.value,
                     "path_mask": widget_entry2.path_mask.value,
                     "file_seg": widget_entry2.file_seg.value,
                     "cell_value": widget_entry2.cell_value.value,
                     "mask_value": widget_entry2.mask_value.value}
    USR_CONFIG.save_ini_r2(parameters_r2, CURRENT_DIR)


@widget_entry2.load_para.changed.connect
def _on_load_para_changed():
    try:
        USR_CONFIG.load_ini(CURRENT_DIR)
    except ValueError:
        return
    config.pars.set_from_dict(USR_CONFIG.pars.advanced)

    if USR_CONFIG.pars.r2:
        set_pars_r2(USR_CONFIG.pars.r2)
    else:
        set_pars_r2(USR_CONFIG.pars.r1)


def set_pars_r2(parameters: dict):
    widget_entry2.path_cells.value = parameters["path_cells"]
    widget_entry2.path_raw.value = parameters["path_raw"]
    widget_entry2.path_mask.value = parameters["path_mask"]
    if parameters.get("file_seg"):
        widget_entry2.file_seg.value = parameters["file_seg"]
    widget_entry2.cell_value.value = int(parameters["cell_value"])
    widget_entry2.mask_value.value = int(parameters["mask_value"])


@widget_entry2.file_seg.changed.connect
def _on_file_seg_changed():
    msg = check_existence_path(data_paths_r2())
    show_error_msg(widget_entry2.error_info, msg)


@widget_entry2.path_cells.changed.connect
def _on_path_cells_changed():
    if widget_entry2.path_cells.value.exists():
        new_cwd = widget_entry2.path_cells.value.parent
        widget_entry2.path_raw.value = new_cwd
        widget_entry2.path_mask.value = new_cwd
        widget_entry2.file_seg.value = new_cwd.parent / "Seg.npy"
    msg = check_existence_path(data_paths_r2())
    show_error_msg(widget_entry2.error_info, msg)


@widget_entry2.path_raw.changed.connect
def _on_path_raw_changed():
    msg = check_existence_path(data_paths_r2())
    show_error_msg(widget_entry2.error_info, msg)


@widget_entry2.path_mask.changed.connect
def _on_path_mask_changed():
    msg = check_existence_path(data_paths_r2())
    show_error_msg(widget_entry2.error_info, msg)
