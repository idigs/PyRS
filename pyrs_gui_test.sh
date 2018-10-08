#!/bin/sh
python setup.py pyuic
python setup.py build
MANTIDLOCALPATH=/home/wzz/Mantid_Project/builds/debug-master/bin/
MANTIDMACPATH=/Users/wzz/MantidBuild/debug-stable/bin/
MANTIDSNSDEBUGPATH=/SNS/users/wzz/Mantid_Project/builds/debug/bin/
MANTIDPATH=$MANTIDMACPATH:$MANTIDLOCALPATH:$MANTIDSNSDEBUGPATH
PYTHONPATH=$MANTIDPATH:$PYTHONPATH
echo "PYTHON PATH"
echo $PYTHONPATH
echo

if [ $1 ]; then
    CMD=$1
else
    CMD=
    echo "1: peak fit, 2: texture, 3: strain stress, 4: manual reduction"
fi

if [ "$1" = "1" ]
then 
	echo "Test peak fitting module"
        PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/peakfitgui_test.py
fi

if [ "$1" = "2" ]
then 
	echo "Test texture calculation module"
        PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/texturegui_test.py
fi

if [ "$1" = "3" ]
then 
	echo "Test strain/stress calculation module"
	PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/strainstressgui_test.py
fi

if [ "$1" = "4" ]
then 
	echo "Test maual reduction mdoule"
	PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/manualreduction_test.py
fi

