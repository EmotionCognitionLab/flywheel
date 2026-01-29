#!/usr/bin/env python3
"""
lc_contrast_extract.py

Compute slice-wise LC contrast ratios from:
  - LC image
  - ROI mask (bilateral)
  - reference mask

Per-slice:
  roiMax(z) = max(LC image in ROI on slice z)
Per-scan:
  refMean   = mean(reference mask)            (NaN if no ref mask)
Ratio:
  ratio(z)  = (roiMax(z) - refMean) / refMean (NaN if refMean is NaN/0)

Outputs:
  - slicewise CSV
  - summary JSON (next to CSV)
"""

from __future__ import annotations

import json
import math
from typing import Dict, List, Tuple, Optional

import nibabel as nib
import numpy as np
import pandas as pd
import fw_gear


def load_nifti_f32(path: str) -> Tuple[np.ndarray, nib.Nifti1Image]:
    img = nib.load(path)
    data = img.get_fdata(dtype=np.float32)
    return data, img


def assert_same_shape(name_a: str, a: np.ndarray, name_b: str, b: np.ndarray) -> None:
    if a.shape != b.shape:
        raise ValueError(f"Shape mismatch: {name_a} {a.shape} vs {name_b} {b.shape}")


def split_hemispheres(mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Split a bilateral mask into left/right by x-midpoint."""
    nx = mask.shape[0]
    mid = nx // 2
    left = np.zeros_like(mask, dtype=mask.dtype)
    right = np.zeros_like(mask, dtype=mask.dtype)
    left[:mid, :, :] = mask[:mid, :, :]
    right[mid:, :, :] = mask[mid:, :, :]
    return left, right


def compute_ref_mean(lc_img: np.ndarray, ref_mask: np.ndarray) -> float:
    """Scan-wise reference mean inside ref_mask."""
    vox = ref_mask > 0
    return float(lc_img[vox].mean()) if np.any(vox) else float("nan")


def slice_roi_max(lc_img: np.ndarray, roi_mask: np.ndarray) -> Dict[int, float]:
    """Return {z: roi_max_on_slice_z} for slices with any ROI voxels."""
    nz = lc_img.shape[2]
    out: Dict[int, float] = {}
    for z in range(nz):
        m = roi_mask[:, :, z] > 0
        if np.any(m):
            out[z] = float(lc_img[:, :, z][m].max())
    return out


def compute_rows_for_hemi(
    lc_img: np.ndarray,
    hemi_mask: np.ndarray,
    hemi_label: str,
    ref_mean: float,
) -> Tuple[List[Dict], float, float]:
    """Compute slicewise rows + (mean,std) of ratios for one hemisphere."""
    max_by_slice = slice_roi_max(lc_img, hemi_mask)

    rows: List[Dict] = []
    ratios: List[float] = []

    for z, roi_max in max_by_slice.items():
        if math.isnan(ref_mean) or math.isclose(ref_mean, 0.0):
            ratio = float("nan")
        else:
            ratio = (roi_max - ref_mean) / ref_mean
            ratios.append(ratio)

        rows.append(
            {
                "hemisphere": hemi_label,
                "sliceIndex": int(z),
                "roiMax": float(roi_max),
                # Kept as refMax for compatibility, but it's scan-wise ref mean repeated per slice
                "refMax": float(ref_mean),
                "ratio": float(ratio),
            }
        )

    mean_r = float(np.mean(ratios)) if ratios else float("nan")
    std_r = float(np.std(ratios)) if ratios else float("nan")
    return rows, mean_r, std_r


def run_single_scan(
    lc_img_path: str,
    mask_roi_path: str,
    out_csv: File,
    out_json: File,
    mask_ref_path: Optional[str] = None,
    split_hemi: bool = True,
) -> Dict:
    # Load required
    lc_img, _ = load_nifti_f32(lc_img_path)
    roi_mask, _ = load_nifti_f32(mask_roi_path)
    assert_same_shape("lc_img", lc_img, "roi_mask", roi_mask)

    # Load optional reference mask
    ref_mean = float("nan")
    if mask_ref_path:
        ref_mask, _ = load_nifti_f32(mask_ref_path)
        assert_same_shape("lc_img", lc_img, "ref_mask", ref_mask)
        ref_mean = compute_ref_mean(lc_img, ref_mask)

    # Hemispheres
    if split_hemi:
        left_mask, right_mask = split_hemispheres(roi_mask)
        hemis = [("left", left_mask), ("right", right_mask)]
    else:
        hemis = [("bilat", roi_mask)]

    all_rows: List[Dict] = []
    summary: Dict[str, float] = {"refMean": float(ref_mean)}

    for hemi_label, hemi_mask in hemis:
        rows, mean_r, std_r = compute_rows_for_hemi(lc_img, hemi_mask, hemi_label, ref_mean)
        all_rows.extend(rows)
        summary[f"{hemi_label}_meanRatio"] = float(mean_r)
        summary[f"{hemi_label}_stdRatio"] = float(std_r)
        summary[f"{hemi_label}_nSlices"] = int(len(rows))

    # Write CSV
    df = pd.DataFrame(all_rows)
    df.to_csv(out_csv, index=False)

    # Write JSON summary next to CSV
    json.dump(summary, out_json, indent=2)

    return summary

if __name__ == "__main__":
    with fw_gear.GearContext() as context:
        lc_nifti = context.config.get_input_path("lc_nifti")
        roi_mask = context.config.get_input_path("roi_mask")
        reference_mask = context.config.get_input_path("reference_mask")
        should_split_hemis = context.config.opts.get("split_hemispheres")
        output_filename = context.config.opts.get("output_filename")
        if not output_filename.endswith(".csv"):
            output_filename += ".csv"
        csv_output_file = context.open_output(output_filename)
        json_output_file = context.open_output(
            output_filename.rsplit(".csv", 1)[0] + ".summary.json"
        )

        result = run_single_scan(
            lc_img_path=lc_nifti,
            mask_roi_path=roi_mask,
            out_csv=csv_output_file,
            out_json=json_output_file,
            mask_ref_path=reference_mask,
            split_hemi=should_split_hemis,
        )

        if context.config.opts.get("also_save_summary_as_metadata"):
            acq = context.client.get_acquisition(context.config.destination.get("id"))
            nifti_fname = context.config.get_input_filename("lc_nifti")
            acq.update_file_info(nifti_fname,  {"LCContrastSummary": result})

        print(json.dumps(result, indent=2))
