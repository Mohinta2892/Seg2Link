"""
Slice/Crop the corrected segmentation.npy file ONLY along the Z-axis and save it as tiffs.
Note: Tested briefly on one dataset to save last 20 slices from the z-dimension.

Author: Samia Mohinta
Affiliation: Cardona lab, Cambridge University, UK
"""

import numpy as np
import tifffile as t
import os
import argparse


def slice_segmentations(seg, slices):
    segm = np.load(seg, mmap_mode='r')
    original_shape = segm.shape
    print(f"Shape of original segmentation: {original_shape}")

    # print(f"Uniques in segm: {np.unique(segm)}")
    segm = segm[slices]

    print(f"Shape of cropped segmentation: {segm.shape}")

    output_folder = f"{os.path.dirname(seg)}/tiffs"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for z_index, slice in enumerate(range(segm.shape[2])):
        # Extract the Z slice
        z_slice = segm[:, :, z_index]
        if z_slice.dtype not in [np.uint16, np.uint8]:
            z_slice = z_slice.astype(np.uint16)

        # for 0 indexing deduct -1
        tiff_filename = f"{output_folder}/slice_{original_shape[2]-z_index-1:04}.tiff"
        t.imwrite(str(tiff_filename), z_slice)


# Custom function to parse None
def none_or_int(value):
    if value.lower() == 'none':
        return None
    return int(value)


def main():
    parser = argparse.ArgumentParser(description="This script extracts Z-slices from a corrected segmentation file saved"
                                                 "from Seg2Link. If Start End slices are both provided as None, "
                                                 " the script will return without making any changes.")
    parser.add_argument('-f', help='Pass the corrected segmentation .npy file')
    parser.add_argument('-ss', type=none_or_int, default=None, help='Start slice for cropping. Default: None.'
                                                                    ' If `None`, we will use the end slice like `-:End`')
    parser.add_argument('-es', type=none_or_int, default=None, help='End slice for cropping. Default: None.'
                                                                    ' If `None`, we will use the start slice like `:Start`')
    args = parser.parse_args()

    if args.ss is None and args.es is None:
        raise Exception("You must provide values in `-ss` and/or `-es` to crop the segmentation file. No action taken!")

    z_slice = slice(None)
    y_slice = slice(None)
    x_slice = slice(None)

    slices = (x_slice, y_slice, z_slice)

    if args.ss is None:
        # last `end` slices
        slices = (x_slice, y_slice, slice(-args.es, None))
    if args.es is None:
        # first `start` slices
        slices = (x_slice, y_slice, slice(None, args.ss))

    slice_segmentations(seg=args.f, slices=slices)


if __name__ == '__main__':
    main()
