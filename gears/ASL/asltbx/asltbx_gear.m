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
    if strcmp(struct_prefix, func_prefix)
       error('The prefix for structural file names must be different from the prefix for functional file names. Exiting.');
    end
    if startsWith(struct_prefix, func_prefix)
        error('The prefix for functional file names must not be a subset of the prefix for structural file names. Exiting.');  
    end
    if startsWith(func_prefix, struct_prefix)
        error('The prefix for structural file names must not be a subset of the prefix for functional file names. Exiting.');  
    end
    
    % download input files and process them
    input_files = download_files(sessions, config.config.tag, struct_prefix);
    asl_params = build_parameters(config, struct_prefix, func_prefix);
    batch_run(asl_params); % call the actual ASLtbx analysis code
    save_outputs(unique([{input_files.file_name}]));
    analysis_id = config.destination.id;
    save_inputs_to_analysis(analysis_id, input_files);
end


function input_files = download_files(sessions, tag, struct_prefix)
    % For each session in sessions, downloads all of the files in that
    % session that have the key-value pair 'tag=<tag parameter>' in their
    % info object. Functional and structural files are both required for
    % ASLtbx analysis and the struct_prefix is used to determine 
    % which is which. (All files whose names start with struct_prefix are
    % assumed to be structural files, and all others are assumed to be
    % functional files.)
    
    global fw;
    global struct_dir;
    global func_dir;
    
    for i = 1:numel(sessions)
       sess = sessions{i};
       tagged_file_info = find_tagged_files(sess, tag);
       if numel(tagged_file_info) > 0
           subj_dir = make_subject_folder(sess.subject.label);
           for f = 1:numel(tagged_file_info)
               acquisition_id = tagged_file_info(f).acquisition_id;
               file = tagged_file_info(f).file;
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
               if (i == 1 && f == 1) 
                    input_files = struct('subject', sess.subject.label, 'session', sess.label,'acquisition_id', acquisition_id, 'file_id', file.id, 'file_name', file.name);
               else
                    input_files(numel(input_files) + 1) = struct('subject', sess.subject.label, 'session', sess.label,'acquisition_id', acquisition_id, 'file_id', file.id, 'file_name', file.name);
               end
           end
       end
    end
end

function tagged_files = find_tagged_files(session, tag)
    % Returns a struct array where each element has an acquisition_id field
    % and a file field. The file field is a FileEntry element for the (sole)
    % file in the acquisition tagged with the tag parameter.
    global fw;
    tagged_files = [];
    acquisitions = session.acquisitions();
    for a = 1:numel(acquisitions)
        cur_idx = numel(tagged_files) + 1;
        files = acquisitions{a}.files;
        for f = 1:numel(files)
            file = fw.getAcquisitionFileInfo(acquisitions{a}.id, files{f}.name);
            file_info = file.info.struct;
            if isfield(file_info, 'Tags') && strcmp(file_info.Tags, tag) && strcmp(file.type, 'nifti')
                tagged_files(cur_idx).acquisition_id = acquisitions{a}.id;
                tagged_files(cur_idx).file = file; % We expect only one tagged file per acquisition. If there are more we'll only get the last one.
            end
        end
    end
end

function subj_dir = make_subject_folder(subj) 
    % Makes a folder for the subject in the input directory, with
    % functional and structural subdirectories. 
    global input_dir;
    global struct_dir;
    global func_dir;
    
    subj_dir = fullfile(input_dir, subj);
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
    % This bundles all of the files in the input directory
    % (except for the original input files) into a tar archive
    % and saves that to the output directory. Also writes
    % Flywheel output manifest.
    global input_dir;
    global output_dir;

    % we un-gzipped the files, so they no longer have .gz ext
    input_files_no_gz = regexprep(input_files, ".gz$", ""); 

    % build find syntax to omit input files
    ors = cell(1, numel(input_files_no_gz));
    ors(:) = {'-or -name'};
    omit = reshape([ors; input_files_no_gz], 1, []);
    omit = omit(2:end);

    output_file = fullfile(output_dir, 'results.tar.gz');
    % find . -type f -not \( -name input_file1 -or -name input_file2... \) | xargs tar cvzf /flywheel/v0/output/results.tar.gz
    find_cmd = strjoin(['find ', '.', '-type', 'f', '-not \( -name', omit, ' \) | xargs tar cvzf', output_file]);
    fprintf('Creating output tar archive with command: %s \n', find_cmd);
    
    % finally run the find command and generate tarball
    curdir = pwd();
    cd(input_dir);
    system(find_cmd);
    cd(curdir);
    
    % write manifest file for Flywheel
    manifest_file = fopen(fullfile(output_dir, '.manifest.json'), 'w');
    fprintf(manifest_file, '{ "acquisition": { "files": ["%s"] } }\n', output_file);
    fclose(manifest_file);
end

function save_inputs_to_analysis(analysis_id, input_files)
    global fw;
    
    iui = flywheel.model.InfoUpdateInput();
    iui.set = containers.Map('inputs', input_files);
    fw.modifyAnalysisInfo(analysis_id, iui);
end
