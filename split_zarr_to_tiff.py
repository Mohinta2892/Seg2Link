import os
import shutil

import dask
import tifffile
from pathlib import Path
from seg2link.misc import load_zarr
import numpy as np


def split_zarr_and_save_tiffs(zarr_path, output_folder, seg_ds=None):
    # Open the Zarr array
    dict_of_img_arrays = load_zarr(zarr_path, mode='r')

    raw_k = [s for s in list(dict_of_img_arrays.keys()) if "raw" in s][-1]
    images = dict_of_img_arrays[raw_k]  # raw

    # make raw tiffs
    # _split(images, output_folder, raw_k)

    # segmentation/labels
    if seg_ds is None:
        seg_k = [s for s in list(dict_of_img_arrays.keys()) if "seg" in s][-1]
    else:
        seg_k = os.path.join("/", seg_ds)
    segmentation = dict_of_img_arrays[seg_k]  # seg

    # _split(segmentation, output_folder, seg_k)

    # affinities
    cells_k = [s for s in list(dict_of_img_arrays.keys()) if "aff" in s or "bound" in s][-1]
    cells = dict_of_img_arrays[cells_k]  # this is float32, we should probably binarise this
    # binarise aff maps
    cells = np.sum(cells, axis=0)
    # normalise
    cells = (((cells - np.min(cells)) / (np.max(cells) - np.min(cells))) * 255).astype(np.uint8)

    # _split(cells, output_folder, cells_k)

    # Use Dask to parallelize the calls to _split
    delayed_calls = [
        dask.delayed(_split)(*args) for args in [(images, output_folder, raw_k),
                                                 (segmentation, output_folder, seg_k),
                                                 (cells, output_folder, cells_k)]
    ]
    # Compute the delayed calls in parallel
    dask.compute(*delayed_calls)


def _split(zarr_array, output_folder, ds):
    # Ensure the output folder exists
    output_folder = Path(f"{output_folder}/{os.path.basename(ds)}")
    # always remove existing data
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    output_folder.mkdir(parents=True, exist_ok=True)

    # Get the shape of the Zarr array
    shape_zarr = zarr_array.shape

    # Iterate over the Z dimension and save each slice as a TIFF
    for z_index, slice in enumerate(range(shape_zarr[0])):
        # Extract the Z slice
        z_slice = zarr_array[z_index, ...]
        if z_slice.dtype not in [np.uint16, np.uint8]:
            z_slice = z_slice.astype(np.uint16)

        # Save the Z slice as a TIFF - format filename_0000.tif*
        tiff_filename = output_folder / f"slice_{z_index:04}.tiff"
        tifffile.imwrite(str(tiff_filename), z_slice)

        print(f"Saved {tiff_filename}")


if __name__ == '__main__':
    # Example usage
    zarr_path = '/Users/sam/Documents/random_codebases/ssTEM_data_Acardona/Seg2Link/data/crop_A1_z16655-17216_y13231-13903_x7650-8468.zarr'
    output_folder = '/Users/sam/Documents/random_codebases/ssTEM_data_Acardona/Seg2Link/data/crop_A1_z16655-17216_y13231-13903_x7650-8468'
    seg_ds = "volumes/segmentation_05"
    split_zarr_and_save_tiffs(zarr_path, output_folder, seg_ds)
