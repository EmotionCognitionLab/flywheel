To build the asltbx gear you first need to set up your build environment. You'll need to have docker installed to do that; install it now if you don't have it already.

### Setting Up Your Build Environment
1. Download the installer for Matlab R2018b (Linux) to this directory. Once you've done that this directory should contain a file named matlab_R2018b_glnxa64.zip .
2. Build a docker image from this directory:

        docker build . -t asltbx-gear-builder:setup

3. Figure out how to get X windows to work between docker and your system. Instructions for the Mac are [here](https://cntnr.io/running-guis-with-docker-on-mac-os-x-a14df6a76efc); you're on your own for other operating systems.
4. Run the docker image you built in step 2. Note that you do *not* want to use --rm and that your -e argument(s) may be different (or not needed at all) depending on how you've got X windows set up to work with docker:

        docker run -it -e DISPLAY=192.168.2.100:0 asltbx-gear-builder:setup

5. Run the matlab installer. Be sure to select the Matlab Compiler and Matlab Compiler SDK as components to be installed, and to activate it once you're done installing.

        cd /matlab-installer
        ./install

6. Test to make sure matlab runs ok:

        /usr/local/MATLAB/R2018b/bin/matlab

7. Assuming that everything is in order, save the container as an image so that you don't have to re-install matlab every time you want to build the gear. Open a new command line prompt (on your local host, not in the docker container) and type:

        docker ps

You should see something like this:

        CONTAINER ID        IMAGE                       COMMAND                  CREATED             STATUS              PORTS               NAMES
        0e72334a5260        asltbx-gear-builder:setup   "/bin/sh -c /bin/bash"   43 minutes ago      Up 43 minutes                           dreamy_northcutt

Now type:

        docker commit 0e72334a5260 asltbx-gear-builder:installed

And you're now done setting up your buid environment. If you want to build the gear right now you can skip straight to step 2 of the "Building the Gear" instructions below.

 ### Building the Gear

 1. Run the docker image you set up:

        docker run --rm -it asltbx-gear-builder:installed

2. In the docker container, run matlab:

        cd /flywheel/gears/ASL/asltbx/build
        /usr/local/MATLAB/R2018b/bin/matlab

3. At the matlab command prompt, type 'build_gear' . Get a cup of coffee - this will take a while.

4. Assuming that all went well, open another command line prompt (on your local machine, not the docker container) and copy the build results to your local machine. Use docker ps (see step 7 above for an example) to get the container id and then:

    docker cp container_id:/flywheel/gears/ASL/asltbx/build/asltbx_gear ./asltbx_gear

You're done. You can shut down your docker container.