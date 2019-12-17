This gear is highly specific to the 2018_HRVT project. In that project, some multi-echo acquisitions arrived split into three parts. This gear merges the three of them into one new acquisition and marks the originals for deletion (by adding "_DELETE" to the acquisition name).

Parameters:
 - all_sessions If checked, runs the gear on all sessions in the project.
 - session_id  Only run the gear on this session. Overrides all_sessions.
 - acquisition_prefixes Comma-separated list of acquisition prefixes that will be identified as a split acquisition. For example, if you enter "ER1_, RS_" then all acquisitions whose labels match the pattern "^ER1_[123]$" or "^RS1_[123]$" will treated as a multi-part acquisition to be merged.
