#!/bin/env dls-python

# A small test script to reproduce the heap corruption bug as found
# and described by Arhtur here: 
# https://github.com/areaDetector/ADCore/pull/24

from pkg_resources import require
require("numpy")
require("cothread")

import cothread
from cothread.catools import *

def load_settings( settings ):
    '''Load a whole bunch of PV values in one go
    settings is a list of tuples: (pv, value, datatype)
    '''
    for (pv, value, dtype,) in settings:
        caput( pv, value, datatype=dtype, wait=True ) 
    

def setup_hdf_writer_plugin():
    settings = [
                ("13SIM1:HDF1:FilePath","H:/tmp/hdfbug", DBR_CHAR_STR),
                ("13SIM1:HDF1:FileName", "testbug", DBR_CHAR_STR),
                ("13SIM1:HDF1:AutoIncrement", "Yes", None),
                ("13SIM1:HDF1:FileTemplate", "%s%s%d.h5", DBR_CHAR_STR),
                ("13SIM1:HDF1:AutoSave", "Yes", None),
                ("13SIM1:HDF1:FileWriteMode", "Single", None),
                ("13SIM1:HDF1:NumCapture", 1, None),
                ("13SIM1:HDF1:DeleteDriverFile", "No", None),
                ("13SIM1:HDF1:NumRowChunks", 0, None),
                ("13SIM1:HDF1:NumColChunks", 0, None),
                ("13SIM1:HDF1:NumFramesChunks", 0, None),
                ("13SIM1:HDF1:BoundaryAlign", 0, None),
                ("13SIM1:HDF1:BoundaryThreshold", 65536, None),
                ("13SIM1:HDF1:NumFramesFlush", 0, None),
                ("13SIM1:HDF1:Compression", "None", None),
                ("13SIM1:HDF1:NumExtraDims", 0, None),
                ("13SIM1:HDF1:ExtraDimSizeN", 1, None),
                ("13SIM1:HDF1:ExtraDimSizeX", 1, None),
                ("13SIM1:HDF1:ExtraDimSizeY", 1, None),
                ]
    load_settings( settings )

def stop_ioc():
    print "Waiting 30sec for autosave to do its thing"
    cothread.Sleep(30.0)
    print "Please SHUT DOWN the IOC - and restart it!"
    raw_input("Hit enter when IOC is running again and autosave has restored PVs... ")
    
def capture_one_image_single():
    settings = [
                ("13SIM1:cam1:ImageMode", "Single", None),
                ("13SIM1:cam1:ArrayCallbacks", "Enable" , None),
                ("13SIM1:cam1:ArrayCounter", 0, None),
                ("13SIM1:HDF1:EnableCallbacks", "Enable", None),
                ("13SIM1:HDF1:ArrayCounter", 0, None),
                ]
    load_settings( settings )
    timeout = caget( "13SIM1:cam1:AcquirePeriod_RBV" ) * 1.5 + 1.0
    print "Acquiring and storing a single image in \'Single\' mode"
    caput( "13SIM1:cam1:Acquire", 1, wait=True, timeout=timeout )
    # Wait for a brief moment to allow the file saving to complete
    cothread.Sleep( 1.0 )
    fname = caget( "13SIM1:HDF1:FullFileName_RBV", datatype=DBR_CHAR_STR )
    print "Captured into image file: ", fname

def capture_one_image_capture():
    settings = [
                ("13SIM1:HDF1:FileWriteMode", "Capture", None),
                ]
    load_settings( settings )
    print "Start capture mode"
    caput( "13SIM1:HDF1:Capture", 1, wait=False )
    # Wait for a brief moment to allow the file saving plugin to create the file
    cothread.Sleep(1.0)
    print "Acquire a single frame"
    caput( "13SIM1:cam1:Acquire", 1, wait=False )

def capture_one_image_stream():
    settings = [
                ("13SIM1:HDF1:FileWriteMode", "Stream", None),
                ]
    load_settings( settings )
    print "Start capture mode"
    caput( "13SIM1:HDF1:Capture", 1, wait=False )
    # Wait for a brief moment to allow the file saving plugin to create the file
    cothread.Sleep(1.0)
    print "Acquire a single frame"
    caput( "13SIM1:cam1:Acquire", 1, wait=False )
    
def enable_asyn_trace():
    hdfport = caget("13SIM1:HDF1:PortName_RBV")
    settings = [
                ("13SIM1:cam1:AsynIO.PORT", hdfport, None),
                ("13SIM1:HDF1:PoolUsedMem.SCAN", "Passive", None),
                ("13SIM1:cam1:AsynIO.TMSK", 0x31, None),
                ("13SIM1:cam1:AsynIO.TINM", 0x4, None),
                ]
    load_settings( settings )

def main():
    setup_hdf_writer_plugin()
    stop_ioc()
    #enable_asyn_trace()
    capture_one_image_single()
    enable_asyn_trace()
    capture_one_image_capture()
    
    #capture_one_image_stream()
if __name__=="__main__":
    main()
