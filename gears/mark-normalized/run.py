#!/usr/bin/env python3
# coding: utf-8

import re
from flywheel_gear_toolkit import GearToolkitContext
import logging
log = logging.getLogger(__name__)

# Adds _rec-{rec-value} to the acquisition label
# (in the correct location as specified by BIDS entity order).
# Raises an exception if the _rec entity is already in the label.
# Returns the new label
def add_rec_entity(label, rec_value):
    m = re.match(r".*_rec-[a-zA-Z0-9]+", label)
    if m:
        raise Exception(f"The 'rec' entity is already in use and cannot be applied to the acquisition {label}.")

    # According to BIDS, the _rec entity should appear
    # after the _ce entity, if it exists. If it doesn't
    # exist then _rec goes after _acq, etc.
    entities = ['ce', 'acq', 'task', 'ses']
    for e in entities:
        m = re.match(fr".*_{e}-([a-zA-Z0-9]+)", label)
        if m:
            return label[0:m.end()] + f"_rec-{rec_value}" + label[m.end():]
            
    # either the label is not in reproin format or
    # the only entity that exists is _sub - either way,
    # just stick it on the end
    return f"{label}_rec-{rec_value}"

def main(context):
    destination = context.get_destination_container()
    filename = context.get_input_filename("dicom")
    for f in destination.files:
        if f.name == filename:
            info = f["info"]
            if not "NORM" in info["ImageType"]:
                log.info(f"{filename} in {destination.label} does not appear to be normalized. Skipping.")
                return
    
            new_label = add_rec_entity(destination.label, context.config.get("rec_value"))
            log.info(f"Changing {destination.label} to {new_label}")
            destination.reload()
            destination.update({"label": new_label})
            break



if __name__ == "__main__":
    with GearToolkitContext(config_path="/flywheel/v0/config.json") as context:
        context.init_logging()
        main(context)