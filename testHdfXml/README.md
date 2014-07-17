testHdfXml
==========

A few scripts to run python unittests to verify the correctness of HDF5 files, produced by the areaDetector HDF5 file writer.

adclientxmlhdf.py
-----------------

A small Channel Access client script to operate a simDetector driver together with the HDF5 File Writer Plugin.

Dependencies: [DLS cothread and catools](http://controls.diamond.ac.uk/downloads/python/cothread)

CLI interface:

{{{
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
}}}

test_hdf_xml.py
---------------

This is the unittest script. It reads its test configuration (which HDF5 and XML files to use) from a ini file. See for example the test_hdf_xml.ini. 

Dependencies: [h5py](http://docs.h5py.org/en/2.3) which depends on the HDF5 libraries and numpy.
If the [cothread.atools](http://controls.diamond.ac.uk/downloads/python/cothread) module is present in the system, this test will import the adclientxmlhdf.py script and attempt to generate a HDF5 output file by operating an EPICS AD IOC with simDetector and the HDF5 file writer (which has to be previously started by the user).

CLI interface: Run with the -h flag to see the available options and arguments.


