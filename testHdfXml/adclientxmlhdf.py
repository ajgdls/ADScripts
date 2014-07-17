#!/bin/env dls-python
try:
    from pkg_resources import require
    require('cothread')
except:
    # Some may not use setuptools/require for package management
    # and that is OK too...
    pass

import os
import argparse
from cothread.catools import *

class StrException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def _str_(self):
        return repr(self.msg)

class SimDet:
    def __init__(self, pv):
        self.basepv = pv
        pv += ":"
        self.pv = dict({'period':      pv + 'AcquirePeriod',
                        'exposure':    pv + 'AcquireTime',
                        'mode':        pv + 'ImageMode',
                        'arrays':      pv + 'ArrayCounter',
                        'numimages':   pv + 'NumImages',
                        'acquire':     pv + 'Acquire',
                        'acquire_rbv': pv + 'Acquire'})
                        
        self.portname = caget(pv + "PortName_RBV")
        self.mon_handle = None
        self.acquiring = None
        
    def stop_monitor(self):
        self.mon_handle.close()
        
    def start_monitor(self):
        self.acquiring = caget( self.pv['acquire_rbv']) is 1
        self.mon_handle = camonitor( self.pv['acquire_rbv'], self.monitor_acquire)
        
    def monitor_acquire(self, acquire):
        self.acquiring = acquire is 1
        
    def acquire(self, exposure, num = 1, wait=True):
        # First check if acquisition is running
        if self.acquiring:
            caput( self.pv['acquire'], 0, wait=True)
        # Clear counter
        caput( self.pv['arrays'], 0)
        # Set number of images
        caput( self.pv['mode'], "Multiple")
        caput( self.pv['numimages'], num)
        # Set exposure and period
        caput( self.pv['period'], exposure, wait=True)
        caput( self.pv['exposure'], exposure, wait = True)
        # Calculate timeout: period (or exposure) * num * 1.5
        timeout = exposure * num * 1.5
        caput( self.pv['acquire'], 1, wait=wait, timeout=timeout)
        
class HdfPlugin:
    def __init__(self, pv):
        self.basepv = pv
        pv += ":"
        self.pv = dict( {'enable':      pv + 'EnableCallbacks',
                         'port':        pv + 'NDArrayPort',
                         'arrays':      pv + 'ArrayCounter',
                         'dropped':     pv + 'DroppedArrays',
                         'numcapture':  pv + 'NumCapture',
                         'lazyopen':    pv + 'LazyOpen',
                         'capture':     pv + 'Capture',
                         'capture_rbv': pv + 'Capture_RBV',
                         'path':        pv + 'FilePath',
                         'name':        pv + 'FileName',
                         'template':    pv + 'FileTemplate',
                         'mode':        pv + 'FileWriteMode',
                         'xmlfile':     pv + 'XMLFileName',
                         'xmlvalid':    pv + 'XMLValid_RBV',
                         'xmlerror':    pv + 'XMLErroMsg_RBV'})
                         
        self.portname = caget(pv + "PortName_RBV")
        self.capturing = None
        self.mon_handle = None
        
    def __enter__(self):
        self.start_monitor()
    def __exit__(self, type, value, traceback):
        self.stop_monitor()
        
    def start_monitor(self):
        self.capturing = caget( self.pv['capture_rbv']) is 1
        self.mon_handle = camonitor( self.pv['capture_rbv'], self.monitor_capture )
    def stop_monitor(self):
        self.mon_handle.close()
        
    def monitor_capture(self, capture):
        self.capturing = capture is 1
        
    def set_data_source(self, source_driver):
        #print "Setting %s plugin input: %s" %( self.portname, source_driver.portname)
        caput( self.pv['port'], str(source_driver.portname), wait=True)
        
    def configure_file(self, outputfile, xmldef=None):
        if xmldef:
            caput( self.pv['xmlfile'], os.path.abspath(xmldef), datatype=DBR_CHAR_STR, wait=True)
            validxml = caget( self.pv['xmlvalid'])
            if validxml is 0:
                errmsg = caget( self.pv['xmlerror'] )
                raise StrException(errmsg)
            
        outputfile = os.path.abspath(outputfile)
        fname = os.path.basename(outputfile)
        dname = os.path.dirname(outputfile)
        caput( self.pv['template'], "%s%s", datatype = DBR_CHAR_STR )
        caput( self.pv['path'], dname, datatype = DBR_CHAR_STR)
        caput( self.pv['name'], fname, datatype = DBR_CHAR_STR)
        caput( self.pv['mode'], "Stream", wait=True)
        
    def capture(self, num = 1):
        # first disable plugin
        caput( self.pv['enable'], 0, wait = True)
        # Stop capturing if we are currently doing so
        if self.capturing:
            caput( self.pv['capture'], 0, wait=True)
        # Clear counters
        caput( self.pv['arrays'], 0)
        caput( self.pv['dropped'], 0)
        # Enable lazy open
        caput( self.pv['lazyopen'], 1)
        # Set number of images to capture
        caput( self.pv['numcapture'], num, wait=True)
        # Start capturing
        caput( self.pv['capture'], num, wait=False)
        # Re-enable the plugin
        caput( self.pv['enable'], 1, wait = True)
        
class AreaDetector:
    def __init__(self, drivers, plugins):
        self.drivers = drivers
        self.plugins = plugins
        
    def __enter__(self):
        for plugin in self.plugins + self.drivers:
            plugin.start_monitor()
            
    def __exit__(self, type, value, traceback):
        for plugin in self.plugins + self.drivers:
            plugin.stop_monitor()

def run_xml_hdf_writer(xml_file, hdf_file, exposure=0.1, nimages=4,
                       simpv = 'TESTSIMDETECTOR:CAM',
                       hdfpv = 'TESTSIMDETECTOR:HDF'):
    '''Convenience function to capture a number of simulated images into an HDF5 file'''
    sim = SimDet(simpv)
    hdf = HdfPlugin(hdfpv)
    with AreaDetector([sim], [hdf]) as ad:
        hdf.set_data_source(sim)
        hdf.configure_file(hdf_file, xml_file)
        hdf.capture(nimages)
        sim.acquire(exposure, nimages)

            
def main():
    class AbsPathAction(argparse.Action):
        def __call__(self, parser, namespace, value, option_string=None):
            value = os.path.abspath(value)
            setattr(namespace, self.dest, value)
    parser = argparse.ArgumentParser(description="EPICS areaDetector client to control the acquisition of (simulated) images and the associated HDF5 file writer")
    parser.add_argument('xmlfilename', metavar='XMLFILE', type=str, action=AbsPathAction, 
                        help='XML file describing the layout of the output HDF5 file')
    parser.add_argument('hdf5filename', metavar='HDF5FILE', type=str, action=AbsPathAction,
                        help='Output HDF5 file')
    parser.add_argument('--exposure', '-e', metavar='T', dest='exposure', action='store', type=float, default=0.1,
                        help='Set the camera exposure time in seconds')
    parser.add_argument('--num', '-n', metavar='N', dest='numimages', action='store', type=int, default=1,
                        help='Number of images to record')
    parser.add_argument('--simpv', dest='simpv', action='store', default = "TESTSIMDETECTOR:CAM", 
                        help='Base PV of the simulated camera driver')
    parser.add_argument('--hdfpv', dest='hdfpv', action='store', default = "TESTSIMDETECTOR:HDF",
                        help='Base PV of the HDF5 file writer plugin')
    
    args = parser.parse_args()
    args = vars(args)
    run_xml_hdf_writer(args['xmlfilename'], args['hdf5filename'], args['exposure'], args['numimages'],
                       simpv=args['simpv'], hdfpv=args['hdfpv'])
    
if __name__=="__main__":
    main()
    
