Making the mac installer uses pyinstaller (tested on 3.6.0). This must be done with
miniconda to properly package the LLVMLite package for numba. In order to set up the
proper build environment, simply install from source as in the RAW documentation, then
additionally install pyinstaller through pip: pip install pyinstaller.

Note: currently requires setuptools<45 to work.

Steps:
1)  Make a fresh git-free folder for RAW: git archive master | tar -x -C /somewhere/else
2)  Set the appropriate python path, if needed: export PATH=~/miniconda2/bin:$PATH
3)  Build the extensions and run RAW in that new folder.
4)  Build the html documentation
5)  In the installer directory, run “pyinstaller -y RAW.spec”
6)  The app file is located at ./dist/RAW.app #NOTE: The dist/RAW/RAW executable will not open because the resources path is wrong if it's not in the .app package!
7)  Open disk utility
8)  Create a new disk image (File->New Image>Blank Image) that is ~12% larger than the
    .app package. Name it RAW, but save it as untitled.
9)  Open the mounted disk image. Copy the .app file and a shortcut of the applications
    folder to the disk image. Size and arrange as desired.
10) In Disk Utility, Image->Convert, select the prepared disk image, and name it RAW-x.y.z-mac
    (note, the disk image must be ejected for this to work


5/6/22 notes:
- Don't need to do the wxpython thing below on arm64
- Have to use nomkl on >=10.14 for x86_64 with most recent versions of numpy, scipy
- To use the nweer versions of pyisntaller, you have to build on 10.14 so that codesigning in pyinstaller works correctly (fails on earlier versions). That's still failing by giving a file is damaged error once you upload to sourceforg then download and trying to run the .app.
- Still building on 10.11, using pyinstaller 4.3 (conda env py37)

Need to use wxpython >=4.1 to eliminate some weird GUI glitches on MacOS 11 (conda's wx env on 10.11 build machine).
To do so at the moment with pyinstaller 4.2 requires some manual modification
to the app package, as described here:
https://github.com/pyinstaller/pyinstaller/issues/5710
Commands from that:
cd dist/program.app/Contents/MacOS/
rm -f libwx_osx_cocoau_core-3.1.5.0.0.dylib libwx_baseu-3.1.5.0.0.dylib
ln -s libwx_osx_cocoau_core-3.1.dylib libwx_osx_cocoau_core-3.1.5.0.0.dylib
ln -s libwx_baseu-3.1.dylib libwx_baseu-3.1.5.0.0.dylib

Note: For RAW to work on macbooks older than 2011 need to install all packages
through conda forge. The new ones through conda have some weird error. See:
https://github.com/conda/conda/issues/9678

Note: For RAW to build on 10.9, using python 3, install miniconda from the
4.5.12 installer (not latest!)

Note: It looks like when the intel mkl library is linked to numpy, the Mac build
gets really big (~750 MB). Can unlink it by install conda package nomkl if desired.

Note: In order to refresh the size of the RAW.app package you need to first delete the .DS_store file
that is in the folder it is in, then relaunch Finder from the force quit menu.

Note: To install on arm64 (as of 4/2022), install through conda as normal. You have to install wxpython, fabio, and pyfai through pip, and resolve some weird numpy dependency thing by downgrading it to 1.21.

More info on disk images here:
https://el-tramo.be/blog/fancy-dmg/

Pyinstaller command used to generate initial .spec file:

pyinstaller --add-data ./resources:resources --hidden-import _sysconfigdata --additional-hooks-dir ../MacLib/installer/ --exclude-module PyQt5 --exclude-module tk --exclude-module ipython --exclude-module tcl -d all -i resources/raw.icns --osx-bundle-identifier edu.bioxtas.raw --windowed RAW.py

