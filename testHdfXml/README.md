testHdfXml
==========

A few scripts to run python unittests to verify the correctness of HDF5 files, produced by the areaDetector HDF5 file writer.

adclientxmlhdf.py
-----------------

A small Channel Access client script to operate a simDetector driver together with the HDF5 File Writer Plugin.

Dependencies: [DLS cothread and catools](http://controls.diamond.ac.uk/downloads/python/cothread)

CLI interface:


    usage: adclientxmlhdf.py [-h] [--exposure T] [--num N] [--simpv SIMPV]
                             [--hdfpv HDFPV]
                             XMLFILE HDF5FILE

    EPICS areaDetector client to control the acquisition of (simulated) images and
    the associated HDF5 file writer
    
    positional arguments:
      XMLFILE             XML file describing the layout of the output HDF5 file
      HDF5FILE            Output HDF5 file
    
    optional arguments:
      -h, --help          show this help message and exit
      --exposure T, -e T  Set the camera exposure time in seconds
      --num N, -n N       Number of images to record
      --simpv SIMPV       Base PV of the simulated camera driver
      --hdfpv HDFPV       Base PV of the HDF5 file writer plugin

test_hdf_xml.py
---------------

This is the unittest script. It reads its test configuration (which HDF5 and XML files to use) from a ini file. See for example the test_hdf_xml.ini. 

Dependencies: [h5py](http://docs.h5py.org/en/2.3) which depends on the HDF5 libraries and numpy.
If the [cothread.atools](http://controls.diamond.ac.uk/downloads/python/cothread) module is present in the system, this test will import the adclientxmlhdf.py script and attempt to generate a HDF5 output file by operating an EPICS AD IOC with simDetector and the HDF5 file writer (which has to be previously started by the user).

CLI interface: 

    usage: test_hdf_xml.py [-h] [--verbosity LEVEL] [--failfast] [INIFILE]
    
    Testing of the HDF5 file writer XML layout featureThis test compare a HDF5
    file with an XML definition file.
    
    positional arguments:
      INIFILE               INI file which can list a number of combinations of
                            HDF5 and XML files to be checked
    
    optional arguments:
      -h, --help            show this help message and exit
      --verbosity LEVEL, -v LEVEL
                            Verbosity of the unittest output
      --failfast, -f        Abort on first encounted test failure or error

Example Test Run
----------------

An example INI file is provided in test_hdf_xml.ini:

    [LAYOUT TEST]
    xml_file = data/layout.xml
    hdf_file = data/layout_test.h5
    
    [NEW TXM TEST]
    xml_file = data/new_txm_sample.xml
    hdf_file = data/new_txm_sample_test.h5

In this example there are two test-runs (set of input/output files), with a number of individual checks being done for each. The output looks something like this for a simple overview:

    [up45@pc0009 testHdfXml]$ ./test_hdf_xml.py -v1
    ........
    ----------------------------------------------------------------------
    Ran 8 tests in 4.026s
    
    OK

With a more verbose setting, some more information about the testing is printed:

    [up45@pc0009 testHdfXml]$ ./test_hdf_xml.py -v5
    test_all_defined_groups (__main__.TestHdfXml: LAYOUT TEST)
    Check if all XML defined groups are present in HDF5 ... ok
    test_all_detector_dset (__main__.TestHdfXml: LAYOUT TEST)
    Check if all defined detector datasets exist in HDF5 ... ok
    test_dataset_attributes (__main__.TestHdfXml: LAYOUT TEST)
    Check if all datasets in HDF5 have the pre-defined attributes present ... ok
    test_group_attributes (__main__.TestHdfXml: LAYOUT TEST)
    Check if all groups in HDF5 have the pre-defined attributes present ... ok
    test_all_defined_groups (__main__.TestHdfXml: NEW TXM TEST)
    Check if all XML defined groups are present in HDF5 ... ok
    test_all_detector_dset (__main__.TestHdfXml: NEW TXM TEST)
    Check if all defined detector datasets exist in HDF5 ... ok
    test_dataset_attributes (__main__.TestHdfXml: NEW TXM TEST)
    Check if all datasets in HDF5 have the pre-defined attributes present ... ok
    test_group_attributes (__main__.TestHdfXml: NEW TXM TEST)
    Check if all groups in HDF5 have the pre-defined attributes present ... ok
    
    ----------------------------------------------------------------------
    Ran 8 tests in 4.028s
    
    OK



