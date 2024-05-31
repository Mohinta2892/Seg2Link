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

    segm = segm.transpose((2, 0, 1))

    original_shape = segm.shape
    print(f"Shape of original segmentation: {original_shape}")

    # print(f"Uniques in segm: {np.unique(segm)}")
    segc = segm[slices]

    print(f"Shape of cropped segmentation: {segc.shape}")

    # todo change it use only split.ext
    output_folder = f"{os.path.dirname(seg)}/sliced_{os.path.splitext(os.path.basename(seg))[0]}_tiffs"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # default z_index_range
    z_index_range = []
    # calculate the original indices of the seg file
    if slices[0].start is not None and slices[0].stop is not None:
        z_index_range = range(slices[0].start, slices[0].stop)
    elif slices[0].start is not None and slices[0].stop is None:
        # slices[0].start is negative
        z_index_range = range(original_shape[0] + slices[0].start, original_shape[0])
    elif slices[0].start is None and slices[0].stop is not None:
        z_index_range = range(0, slices[0].stop)

    for z_index, slice in enumerate(z_index_range):
        # Extract the Z slice
        z_slice = segc[z_index, ...]
        if z_slice.dtype not in [np.uint16, np.uint8]:
            z_slice = z_slice.astype(np.uint16)

        tiff_filename = f"{output_folder}/slice_{(slice):04}.tiff"
        t.imwrite(str(tiff_filename), z_slice)


# Custom function to parse None
def none_or_int(value):
    if value.lower() == 'none':
        return None
    return int(value)


def main():
    parser = argparse.ArgumentParser(
        description="This script extracts Z-slices from a corrected segmentation file saved"
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

    z_slice = slice(args.ss, args.es)
    y_slice = slice(None)
    x_slice = slice(None)

    slices = (z_slice, y_slice, x_slice)

    if args.ss is None:
        # last `end` slices
        slices = (slice(-args.es, None), x_slice, y_slice)
    if args.es is None:
        # first `start` slices
        slices = (slice(None, args.ss), x_slice, y_slice)


    slice_segmentations(seg=args.f, slices=slices)


if __name__ == '__main__':
    main()
