function maskimg=ASLtbx_createbrainmask(P)
% create a brain mask using hard threshold
v=spm_vol(P);
dat=spm_read_vols(v);
mdat=squeeze(mean(dat,4));
mdat(isnan(mdat))=0;
mask=mdat>0.23*max(mdat(:));
[pth,nam,ext,num] = spm_fileparts(P(1,:));
vo=v(1);
vo.fname=fullfile(pth, ['brainmask.nii']);
vo.dt=[2 1];
vo.n=[1 1];
vo=spm_write_vol(vo, mask);
maskimg=vo.fname;