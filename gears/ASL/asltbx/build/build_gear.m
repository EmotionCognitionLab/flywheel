
% Check that we are running a compatible version
if (~contains(version, '9.5.0')) || (~contains(computer, 'GLNXA64'))
    error('You must compile this function using R2018b (9.5.0.1067069) 64-bit (glnxa64). You are using %s, %s', version, computer);
end

disp('Configuring spm to be used as part of a standalone executable...');
addpath('/opt/spm12');

% the last 7 lines of spm_make_standalone.m run mcc to compile SPM into a standalone app
% we don't need or want that, so use head to omit them
system('cp -p /opt/spm12/config/spm_make_standalone.m /opt/spm12/config/spm_make_standalone_orig.m');
system('head -105 /opt/spm12/config/spm_make_standalone_orig.m > /opt/spm12/config/spm_make_standalone.m');
spm_jobman('initcfg');
spm_get_defaults('cmdline', true);
spm_make_standalone();
system('mv /opt/spm12/config/spm_make_standalone_orig.m /opt/spm12/config/spm_make_standalone.m');

addpath('/opt/flywheel-sdk');
delete('/flywheel/gears/ASL/asltbx/bin/asltbx_gear'); % so there's no confusion about whether the build replaced what's there
addpath('/flywheel/gears/ASL/asltbx');
disp('Building gear...');
% We want to avoid adding spm12/external/fieldtrip/compat to the build as functions there re-define core Matlab routines,
% causing errors in Flywheel SDK
spm12_subdirs = get_dirs('/opt/spm12', 'external');
external_subdirs = get_dirs('/opt/spm12/external', 'fieldtrip');
fieldtrip_subdirs = get_dirs('/opt/spm12/external/fieldtrip', 'compat');
dirs_to_add = ['/opt/spm12/*', strcat("/opt/spm12/", {spm12_subdirs.name}), '/opt/spm12/external/*', strcat("/opt/spm12/external/", {external_subdirs.name}), '/opt/spm12/external/fieldtrip/*', strcat("/opt/spm12/external/fieldtrip/", {fieldtrip_subdirs.name}), '/flywheel/gears/ASL/asltbx/batch_scripts', '/opt/flywheel-sdk'];
a = cell(1, numel(dirs_to_add));
a(:) = {'-a'};
add_flags = reshape([a;dirs_to_add], 1, []); % results in 1*N array of {'-a', 'dir1_name', '-a', 'dir2_name', ...};

mcc('-v', '-N', '-R', '-nodisplay', '-d', '/flywheel/gears/ASL/asltbx/bin/', add_flags{:}, '-m', 'asltbx_gear.m')

function subdirs = get_dirs(start_dir, exclude_dirs)
    items = dir(start_dir);
    subdirs = items([items.isdir] == 1 & strncmp({items.name}, '.', 1) == 0 & ~contains({items.name}, exclude_dirs));
end
