
% Batch mode scripts for running spm2 in TRC
% Created by Ze Wang, 08-05-2004
% zewang@mail.med.upenn.edu

function batch_run(PAR)

    % set the center to the center of each images
    % batch_3Dto4D;
    batch_reset_orientation(PAR);


    %realign the functional images to the first functional image of eachsubject
    batch_realign(PAR);

    %coreg the functional images to the anatomical image
    batch_coreg(PAR);

    batch_filtering(PAR);

    %smooth the coreged functional images
    batch_smooth(PAR);

    %create perfusion mask
    batch_create_mask(PAR);


    batch_perf_subtract(PAR);

    %coreg the result images to MNI template image
    batch_norm_spm12(PAR);
end

