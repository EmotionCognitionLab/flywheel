A gear for running [ASLtbx](https://cfn.upenn.edu/~zewang/ASLtbx.php). This gear requires no inputs; it uses the Flywheel SDK to download all of the input files. Designating the input files requires using the [tagger tool](http://flywheel-tagger.s3-website-us-west-2.amazonaws.com/) (source is at https://github.com/EmotionCognitionLab/flywheel/tree/master/utils/mark-inputs) to assign a tag to all of your input files and to upload the tag file to the project in Flywheel.

Once you've done that, you're ready to run the gear. Specify the tag file you just created as the input and set the other
parameters as appropriate for your analysis.

Note: It is important that your files are named consistently. ASLtbx requires a T1 anatomical scan for each subject and a 4D ASL file per session (both in NIfTI format). The gear requires all of the structural file names to share one common prefix and all of the functional files to share a different common prefix.