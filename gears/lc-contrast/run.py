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

from nibabel.affines import apply_affine
import nibabel as nib
import numpy as np
import pandas as pd
import fw_gear


def load_nifti_canonical_f32(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load NIfTI and convert to closest canonical orientation (RAS-like),
    returning (data, affine). This makes axis-based operations consistent.
    """
    img = nib.as_closest_canonical(nib.load(path))
    data = img.get_fdata(dtype=np.float32)
    return data, img.affine

    
def assert_compatible(
name_a: str, a_data: np.ndarray, a_aff: np.ndarray,
name_b: str, b_data: np.ndarray, b_aff: np.ndarray,
affine_atol: float = 1e-4,
) -> None:
    if a_data.shape != b_data.shape:
        raise ValueError(f"Shape mismatch: {name_a} {a_data.shape} vs {name_b} {b_data.shape}")
    # After canonicalization, these should match for same-grid images.
    if not np.allclose(a_aff, b_aff, rtol=0.0, atol=affine_atol):
        raise ValueError(
            f"Affine mismatch between {name_a} and {name_b} (after canonicalization). "
            "If these should be on the same template grid, resample upstream."
        )


def split_roi_lr_by_world_x(mask: np.ndarray, aff: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Split ROI voxels by WORLD x coordinate sign in template space:
    Left = x < 0
    Right = x > 0
    Assumes a typical MNI-like space where the mid-sagittal plane is near x=0.
    Fallback to midpoint split if one side is empty.
    """
    coords = np.argwhere(mask > 0)
    left = np.zeros_like(mask, dtype=mask.dtype)
    right = np.zeros_like(mask, dtype=mask.dtype)

    if coords.size == 0:
        return left, right

    xyz = apply_affine(aff, coords)   # (N, 3) world coords
    x = xyz[:, 0]

    left_coords = coords[x < 0]
    right_coords = coords[x > 0]

    # Fallback if split fails (e.g., unilateral ROI or weird origin)
    if left_coords.size == 0 or right_coords.size == 0:
        nx = mask.shape[0]
        mid = nx // 2
        left[:mid, :, :] = mask[:mid, :, :]
        right[mid:, :, :] = mask[mid:, :, :]
        return left, right

    left[tuple(left_coords.T)] = mask[tuple(left_coords.T)]
    right[tuple(right_coords.T)] = mask[tuple(right_coords.T)]
    return left, right



def compute_ref_mean(lc_img: np.ndarray, ref_mask: np.ndarray) -> float:
    """Scan-wise reference mean inside ref_mask."""
    vox = ref_mask > 0
    return float(lc_img[vox].mean()) if np.any(vox) else float("nan")

def compute_ref_max_by_slice(lc_img: np.ndarray, ref_mask: np.ndarray) -> Dict[int, float]:
    """
    Return {z: refMax(z)} where:
    refMax(z) = max(lc_img[:,:,z] within ref_mask[:,:,z])
    """
    nz = lc_img.shape[2]
    out: Dict[int, float] = {}
    for z in range(nz):
        m = ref_mask[:, :, z] > 0
    if np.any(m):
        out[z] = float(lc_img[:, :, z][m].max())
    return out


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
    ref_max_by_slice: Dict[int, float],
) -> Tuple[List[Dict], float, float]:
    """
    Compute slicewise rows + (mean,std) of ratios for one hemisphere using slice-wise refMax(z).
    Keeps CSV column name "refMax" but now it is refMax(z) per slice (not refMean).
    """
    max_by_slice = slice_roi_max(lc_img, hemi_mask)

    rows: List[Dict] = []
    ratios: List[float] = []

    for z, roi_max in max_by_slice.items():
        ref_max = float(ref_max_by_slice.get(int(z), float("nan")))

        if math.isnan(ref_max) or math.isclose(ref_max, 0.0):
            ratio = float("nan")
        else:
            ratio = (float(roi_max) - ref_max) / ref_max
            ratios.append(ratio)

        rows.append(
            {
                "hemisphere": hemi_label,
                "sliceIndex": int(z),
                "roiMax": float(roi_max),
                "refMax": float(ref_max),   # <-- now slice-wise refMax(z)
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
    # Load required (canonicalized)
    lc_img, lc_aff = load_nifti_canonical_f32(lc_img_path)
    roi_mask, roi_aff = load_nifti_canonical_f32(mask_roi_path)
    assert_compatible("lc_img", lc_img, lc_aff, "roi_mask", roi_mask, roi_aff)

    # Load reference mask (canonicalized)
    ref_mean = float("nan") 
    ref_max_by_slice: Dict[int, float] = {}

    if mask_ref_path:
        ref_mask, ref_aff = load_nifti_canonical_f32(mask_ref_path)
        assert_compatible("lc_img", lc_img, lc_aff, "ref_mask", ref_mask, ref_aff)
        ref_mean = compute_ref_mean(lc_img, ref_mask)

        # NEW: slice-wise refMax(z) for CSV+ratio
        ref_max_by_slice = compute_ref_max_by_slice(lc_img, ref_mask)

    # Hemispheres (robust L/R)
    if split_hemi:
        left_mask, right_mask = split_roi_lr_by_world_x(roi_mask, roi_aff)
        hemis = [("left", left_mask), ("right", right_mask)]
    else:
        hemis = [("bilat", roi_mask)]

    all_rows: List[Dict] = []
    summary: Dict[str, float] = {"refMean": float(ref_mean)}  # still present if you want

    for hemi_label, hemi_mask in hemis:
        rows, mean_r, std_r = compute_rows_for_hemi(
            lc_img, hemi_mask, hemi_label, ref_max_by_slice
        )
        all_rows.extend(rows)
        summary[f"{hemi_label}_meanRatio"] = float(mean_r)
        summary[f"{hemi_label}_stdRatio"] = float(std_r)
        summary[f"{hemi_label}_nSlices"] = int(len(rows))

    # Write CSV
    df = pd.DataFrame(all_rows)
    df.to_csv(out_csv, index=False)

    # Write JSON
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
