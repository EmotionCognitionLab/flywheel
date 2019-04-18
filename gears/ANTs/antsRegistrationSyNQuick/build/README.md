At the time of this writing the pre-packaged versions of ANTs (2.1.x) didn't provide the results we needed,
from antsRegistrationSynQuick (the slab was too high and didn't included the brainstem),
so it needs to be compiled from scratch for the gear. To do that, follow these steps:

    docker build . -t matherlab/ants-builder
    docker run --name ants-builder matherlab/ants-builder && docker cp ants-builder:/usr/lib/ants ../bin/ants && docker rm ants-builder

The build will take a while (probably more than an hour), so kick it off when you have other things to do. It will also
produce warnings; you can ignore them.