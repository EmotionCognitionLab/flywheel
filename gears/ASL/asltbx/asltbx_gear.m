function run_gear()
%   Main entry point for the ASL gear
%   This gear runs an ASLtbx (https://cfn.upenn.edu/~zewang/ASLtbx.php)
%   analysis on a given set of files. Specify which files you wish to
%   analyze by assiging a tag to the session(s) containing the file(s). 
%   Then add a "tag" field to the info object of each file you wish to
%   analyze in the tagged sessions. This two-step process is necessary
%   because at this time (a) files don't fully support tags and (b) files
%   don't have any information associating them with a given subject - the
%   session is what ties the subject and the files together.

    fprintf('[matherlab/ASLtbx] initiated\n');
    
    % set up SPM
    spm('Defaults', 'fmri');
    spm_jobman('initcfg');
    spm_get_defaults('cmdline', true);

    global flywheel_base; flywheel_base = '/flywheel/v0';
    global input_dir; input_dir = fullfile(flywheel_base, 'input');
    global output_dir; output_dir = fullfile(flywheel_base, 'output');
    
    % names for structural and functional directories
    global struct_dir; struct_dir = 'struct';
    global func_dir; func_dir = 'func';
    
    % load the config and initalize the Flywheel client
    config_file = fullfile(flywheel_base, 'config.json');
    config = jsondecode(fileread(config_file));
    api_key = config.inputs.api_key.key;
    global fw; fw = flywheel.Client(api_key);
    
    % find the project and sessions
    proj_label = config.config.project;
    fprintf('proj_label: %s\n', proj_label);
    
    project = fw.projects.findFirst(['label=', proj_label]);
    if numel(project) < 1
        error('No project named "%s" was found. Exiting.', proj_label);
    end
    if numel(project) > 1
        error('More than one project named "%s" was found. Exiting.', proj_label);
    end
    
    sessions = project.sessions.find(strcat('tags=', config.config.tag));
    if numel(sessions) < 1
        error('No sessions with the tag %s were found in project %s. Exiting.', config.config.tag, proj_label);
    end
    
    struct_prefix = config.config.struct_prefix; % names of all structural files start with this prefix
    func_prefix = config.config.func_prefix;
    calib_prefix = config.config.calib_prefix;
    validate_prefixes(struct_prefix, func_prefix, calib_prefix);

    % download input files and process them
    input_files = download_files(proj_label, sessions, config.config.tag, struct_prefix);
    asl_params = build_parameters(config, struct_prefix, func_prefix);
    batch_run(asl_params); % call the actual ASLtbx analysis code
    save_outputs(unique([{input_files.file_name}]));
    analysis_id = config.destination.id;
    save_inputs_to_analysis(analysis_id, input_files);
end

function validate_prefixes(struct_prefix, func_prefix, calib_prefix)
    % Checks to make sure that none of the prefixes are equal to or
    % subsets of one another. Exits with error message if any of them are.
    if strcmp(struct_prefix, func_prefix)
       error('The prefix for structural file names must be different from the prefix for functional file names. Exiting.');
    end
    if startsWith(struct_prefix, func_prefix)
        error('The prefix for functional file names must not be a subset of the prefix for structural file names. Exiting.');
    end
    if startsWith(func_prefix, struct_prefix)
        error('The prefix for structural file names must not be a subset of the prefix for functional file names. Exiting.');
    end
    
    if strcmp(struct_prefix, calib_prefix)
        error('The prefix for structural file names must be different from the prefix for calibration file names. Exiting.');
    end
    if startsWith(struct_prefix, calib_prefix)
        error('The prefix for calibration file names must not be a subset of the prefix for structural file names. Exiting.');
    end
    if startsWith(calib_prefix, struct_prefix)
        error('The prefix for structural file names must not be a subset of the prefix for calibration file names. Exiting.');
    end

    if strcmp(func_prefix, calib_prefix)
        error('The prefix for functional file names must be different from the prefix for calibration file names. Exiting.');
    end
    if startsWith(func_prefix, calib_prefix)
        error('The prefix for calibration file names must not be a subset of the prefix for functional file names. Exiting.');
    end
    if startsWith(calib_prefix, func_prefix)
        error('The prefix for functional file names must not be a subset of the prefix for calibration file names. Exiting.');
    end
end


function input_files = download_files(proj_label, sessions, tag, struct_prefix)
    % For each session in sessions, downloads all of the files in that
    % session that have the key-value pair 'Tags=<tag parameter>' in their
    % info object. Functional, structural and calibration files are all
    % required for ASLtbx analysis and the struct_prefix is used to
    % determine which is which. (All files whose names start with
    % struct_prefix are assumed to be structural files, and all others
    % are put in the functional directory, which is where both functional
    % and calibration files belong.)
    
    global fw;
    global struct_dir;
    global func_dir;
    
    for i = 1:numel(sessions)
       sess = sessions{i};
       tagged_file_info = find_tagged_files(sess, tag);
       if numel(tagged_file_info) > 0
           subj_dir = make_subject_folder(proj_label, sess.subject.label, sess.label);
           for f = 1:numel(tagged_file_info)
               acquisition_id = tagged_file_info(f).acquisition_id;
               files = tagged_file_info(f).files;
               for j = 1:numel(files)
                    file = files(j);
                    dest_dir = '';
                    if startsWith(file.name, struct_prefix)
                        dest_dir = struct_dir;
                    else
                        dest_dir = func_dir;
                    end
                    dest_file = fullfile(subj_dir, dest_dir, file.name);
                    fprintf('Downloading %s_%s/%s/%s to %s\n', sess.subject.label, sess.label, acquisition_id, file.name, dest_file);
                    fw.downloadFileFromAcquisition(acquisition_id, file.name, dest_file);
                    if (endsWith(dest_file, '.gz'))
                            fprintf('gunzipping %s...\n', dest_file);
                            gunzip(dest_file);
                            delete(dest_file);
                    end
                    if (i == 1 && f == 1 && j == 1) 
                        input_files = struct('subject', sess.subject.label, 'session', sess.label,'acquisition_id', acquisition_id, 'file_id', file.id, 'file_name', file.name);
                    else
                        input_files(numel(input_files) + 1) = struct('subject', sess.subject.label, 'session', sess.label,'acquisition_id', acquisition_id, 'file_id', file.id, 'file_name', file.name);
                    end
               end
           end
       end
    end
end

function tagged_files = find_tagged_files(session, tag)
    % Returns a struct array where each element has an acquisition_id field
    % and a files field. The files field is an array of structs (file id
    % and name) for the files in the acquisition tagged with the tag parameter.
    global fw;
    tagged_files = [];
    acquisitions = session.acquisitions();
    for a = 1:numel(acquisitions)
        cur_idx = numel(tagged_files) + 1;
        files = acquisitions{a}.files;
        no_tagged_file_found = true;
        for f = 1:numel(files)
            file = fw.getAcquisitionFileInfo(acquisitions{a}.id, files{f}.name);
            file_info = file.info.struct;
            if isfield(file_info, 'Tags') && strcmp(file_info.Tags, tag) && strcmp(file.type, 'nifti')
                tagged_files(cur_idx).acquisition_id = acquisitions{a}.id;
                if no_tagged_file_found
                    tagged_files(cur_idx).files = struct('id', file.id, 'name', file.name);
                    no_tagged_file_found = false;
                else
                    tagged_files(cur_idx).files(numel(tagged_files(cur_idx).files) + 1) = struct('id', file.id, 'name', file.name);;
                end
            end
        end
    end
end

function subj_dir = make_subject_folder(proj_label, subj, sess)
    % Makes a folder for the subject/session in the input directory, with
    % functional and structural subdirectories. 
    global input_dir;
    global struct_dir;
    global func_dir;
    
    % Replace all filesep (i.e. / or \) with --, otherwise mkdir
    % will create multi-level directory hierarchy
    safe_labels = strrep({proj_label, subj, sess}, filesep, '--');
    subj_dir = fullfile(input_dir, sprintf("%s_%s_%s", safe_labels{1}, safe_labels{2}, safe_labels{3}));
    if exist(subj_dir, 'dir') == 7
        return; % subject folder has already been created
    elseif exist(subj_dir, 'file') == 2
        error('Found a file named %s when trying to create a folder with that name. Exiting.', subj_dir);
    else
        % create the folder structure
        mkdir(subj_dir);
        mkdir(fullfile(subj_dir, struct_dir));
        mkdir(fullfile(subj_dir, func_dir));
    end  
end

function params = build_parameters(config, struct_prefix, func_prefix)
    % builds up the parameter structure that the ASL toolbox batch_*
    % scripts use. See par.m in ASLtbx.
    global input_dir;
    global struct_dir;
    global func_dir;
    
    params = [];
    params.root = input_dir;
    params.groupdir = 'STAT';
    params.img4analysis = 'cbf';
    params.ana_dir = 'glm_cbf';
    params.confilters = {func_dir};
    params.ncond = numel(params.confilters);
    params.structfilter = {struct_dir};
    params.Filter = 'cbf_0_sr';
    params.mp = 'no';
    params.FWHM = [6];
    params.delaytime = config.config.delay_time;
    params.TE = config.config.TE;
    
    input_items = dir(input_dir);
    % All directories in input_dir whose name doesn't start with '.' should
    % be subject directories
    subject_dirs = input_items([input_items.isdir] == 1 & strncmp({input_items.name}, '.', 1) == 0);
    params.subjects = ({subject_dirs.name});
    params.nsubs = numel(params.subjects);
    for i=1:numel(params.subjects)
        sdir = fullfile(input_dir, params.subjects{i}, struct_dir);
        fdir = fullfile(input_dir, params.subjects{i}, func_dir);
        if size(dir(sdir), 1) < 3 % if sdir exists it will contain . and .., so size of 3 means it has at least one file
            error('No structural files found for subject %s. Exiting.', params.subjects{i});
        end
        if size(dir(fdir), 1) < 3
            error('No functional files found for subject %s. Exiting.', params.subjects{i});
        end
        params.structdir{i} = sdir;
        params.condirs{i, 1} = fdir;
    end
    params.TRs = ones(1,params.nsubs)*6;
    params.structprefs = struct_prefix;
    params.funcimgfilters = {func_prefix};
end

function save_outputs(input_files)
    % ASLtbx generates output files in the input directory.
    % It also generates output files that have identical names
    % for each subject, meaning that they cannot be put into
    % one directory without overwriting each other.
    % This function deletes the original input files and then
    % renames the remaining output files, prefixing them with
    % their subject id. Also writes the Flywheel output manifest.
    global input_dir;
    global output_dir;

    % we un-gzipped the files, so they no longer have .gz ext
    input_files_no_gz = regexprep(input_files, ".gz$", ""); 

    % build find syntax to delete input files
    ors = cell(1, numel(input_files_no_gz));
    ors(:) = {'-or -name'};
    inputs = reshape([ors; input_files_no_gz], 1, []);
    inputs = inputs(2:end);

    % find . -type f \( -name input_file1 -or -name input_file2... \) | xargs rm
    delete_cmd = strjoin(['find ', '.', '-type', 'f', '\( -name', inputs, ' \) -print0 | xargs -0 rm']);
    fprintf('Deleting downloaded input files with command: %s \n', delete_cmd);
    
    % run the find/delete command
    curdir = pwd();
    cd(input_dir);
    system(delete_cmd);

    % find remaining files, rename them with subject id prefixes
    % and move them to the output directory
    subj_dirs = dir(input_dir);

    % filter out the '.' and '..' dirs (shouldn't be any other dirs
    % starting with '.')
    valid_dirs = subj_dirs(strncmp({subj_dirs.name}, '.', 1) == 0);
    subj_sess = {valid_dirs.name};

    % for each subject dir, rename all the files and move them to output
    % dir using this command (here subject id is 7003)
    % find /flywheel/v0/input/7003 -type f | while read -r file; do mv -n
    % "$file" "/flywheel/v0/output/7003_$(basename $file)"; done
    for i=1:numel(subj_sess)
        find_and_mv_cmd = sprintf('find ''./%s\'' -type f | while read -r file; do mv -vn "$file" "%s/%s_$(basename "$file")"; done', subj_sess{i}, output_dir, subj_sess{i});
        fprintf('Renaming output files for subject %s with command: %s \n', subj_sess{i}, find_and_mv_cmd);
        system(find_and_mv_cmd);
    end

    cd(curdir);
    
    % get list of all files in output directory
    output_files = dir(output_dir);
    valid_output_files = output_files(strncmp({output_files.name}, '.', 1) == 0);
    valid_output_file_names = {valid_output_files.name};

    % write manifest file for Flywheel
    manifest_file = fopen(fullfile(output_dir, '.manifest.json'), 'w');
    fprintf(manifest_file, '{ "acquisition": { "files": [');
    for j=1:numel(valid_output_file_names)
       fprintf(manifest_file, '"%s"', valid_output_file_names{j});
       if (j ~= numel(valid_output_file_names))
          fprintf(manifest_file, ", ");
       end
    end
    fprintf(manifest_file, '] } }\n');
    fclose(manifest_file);
end

function save_inputs_to_analysis(analysis_id, input_files)
    global fw;
    
    iui = flywheel.model.InfoUpdateInput();
    iui.set = containers.Map('inputs', input_files);
    fw.modifyAnalysisInfo(analysis_id, iui);
end
