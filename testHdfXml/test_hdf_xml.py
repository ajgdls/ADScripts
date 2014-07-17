#!/bin/env dls-python
try:
    from pkg_resources import require
    require('h5py')
    require('numpy')
except:
    # Some may not use setuptools/require for package management
    # and that is OK too...
    pass
    
import os, argparse
import unittest
import ConfigParser
import h5py 

import hdf_xml

# The adclientxmlhdf module imports the DLS cothread.catools module
# which is an EPICS Channel Access client.
# If this package is not available on the system, then we just don't
# run the IOC client code which generates the HDF5 output files based on
# the users XML definition. The user will have to manually supply the HDF5 file
# instead (defined in the .ini file).
try:
    import adclientxmlhdf
    RUN_CA_CLIENT=True
    print "DLS cothread.catools module is available."
except ImportError:
    RUN_CA_CLIENT=False

def make_classes(cls, ini_file):
    '''Programatically generate (yield) a number of classes.
    The classes are based on the cls input and the section names of the
    ini_file input. The content of the ini file sections is stored as constants
    in the generated classes.'''
    cfg = ConfigParser.SafeConfigParser()
    cfg.read(ini_file)
    sections = cfg.sections()
    for section in sections:
        name = '%s: %s' %(cls.__name__, section)
        yield type(name, (cls,), {'hdf_file': os.path.abspath(cfg.get(section, "hdf_file")),
                                  'xml_file': os.path.abspath(cfg.get(section, "xml_file"))})       

class TestHdfXml(unittest.TestCase):
    hdf_file = None
    xml_file = None
    
    def setUp(self):
        # First check that an XML definition file already exist
        self.assertTrue(os.path.exists(self.xml_file), \
                        "Cannot complete tests without XML file: \'%s\'"%(self.xml_file))
        if RUN_CA_CLIENT:
            # Use the XML file (and some IOC out there) to create a HDF5 file
            adclientxmlhdf.run_xml_hdf_writer(self.xml_file, self.hdf_file)
        
        # Now check that the HDF5 file really exists
        self.assertTrue(os.path.exists(self.hdf_file),\
                        "Cannot complete tests without HDF5 file: \'%s\'"%(self.hdf_file))
        
        self.xml_def = hdf_xml.HdfXmlDefinition()
        self.xml_def.populate(self.xml_file)
        self.hdf = h5py.File(self.hdf_file)
        
        # Build some convenient lists of gropus and datasets
        self.hdf_groups = []
        self.hdf_datasets = []
        def build_hdf_lists(name):
            name = "/"+name
            #print "build_hdf_lists: ", name
            if type(self.hdf[name]) == h5py._hl.dataset.Dataset:
                self.hdf_datasets.append(name)
            elif type(self.hdf[name]) == h5py._hl.group.Group:
                self.hdf_groups.append(name)
        self.hdf.visit(build_hdf_lists)
    
    def tearDown(self):
        self.hdf.close()
            
    def test_all_defined_groups(self):
        ''' Check if all XML defined groups are present in HDF5'''
        for group in self.xml_def.groups:
            self.assertTrue(group in self.hdf, "Group \'%s\' should exist in the HDF file"%(group))
                    
    def test_group_attributes(self):
        '''Check if all groups in HDF5 have the pre-defined attributes present'''
        for hdf_group_name in self.hdf_groups:
            try:
                attributes = self.xml_def.groups[hdf_group_name][1]
                hdf_group = self.hdf[hdf_group_name]
            except:
                # No group of that name defined. Probably not reason to fail, so we just continue
                continue
            for attribute in attributes.itervalues():
                #print "Group: %s  attr: %s" % (hdf_dset_name, attribute.name)
                self.assertTrue(attribute.name in hdf_group.attrs, "Group \'%s\' should contain attribute \'%s\'"%(hdf_group_name, attribute.name))
                # If the attribute is a constant we verify it's value too
                if attribute.is_constant():
                    # Numpy arrays (h5py uses numpy) are evaluated slightly differently
                    if type( attribute.value ) == list:
                        array_equal = (attribute.value == hdf_group.attrs[attribute.name])
                        self.assertTrue( array_equal.all(), \
                                         msg = "Group \'%s:%s\' constant value: %s == %s" \
                                         %(hdf_group_name, attribute.name, attribute.value, hdf_group.attrs[attribute.name]) )
                    else:
                        self.assertEqual(attribute.value, hdf_group.attrs[attribute.name], \
                                         msg = "Group \'%s:%s\' constant value: %s == %s" \
                                         %(hdf_group_name, attribute.name, attribute.value, hdf_group.attrs[attribute.name]) )
        
    def test_all_detector_dset(self):
        ''' Check if all defined detector datasets exist in HDF5'''
        for xml_dset in self.xml_def.datasets:
            if self.xml_def.datasets[xml_dset][0] == hdf_xml.DETECTOR:
                self.assertTrue(xml_dset in self.hdf, "Detector dataset \'%s\' should exist in HDF5"%xml_dset)
        
    
    def test_dataset_attributes(self):
        ''' Check if all datasets in HDF5 have the pre-defined attributes present'''
        for hdf_dset_name in self.hdf_datasets:
            try:
                attributes = self.xml_def.datasets[hdf_dset_name][2]
            except:
                # This dataset was not defined in the XML - it could have been added
                # by anyone, which is in principle fine, so we just continue the loop here.
                continue
            hdf_dset = self.hdf[hdf_dset_name]
            for attribute in attributes.itervalues():
                #print "Group: %s  attr: %s" % (hdf_dset_name, attribute.name)
                self.assertTrue(attribute.name in hdf_dset.attrs, \
                                "Dataset \'%s\' should contain attribute \'%s\'"\
                                %(hdf_dset_name, attribute.name))
                # If the attribute is a constant we verify it's value too
                if attribute.is_constant():
                    # Numpy arrays (h5py uses numpy) are evaluated slightly differently
                    if type( attribute.value ) == list:
                        array_equal = (attribute.value == hdf_dset.attrs[attribute.name])
                        self.assertTrue( array_equal.all(), \
                                         msg = "Dataset \'%s\:%s' constant value: %s == %s" \
                                         %(hdf_dset_name, attribute.name, attribute.value, hdf_dset.attrs[attribute.name]) )
                    else:
                        self.assertEqual(attribute.value, hdf_dset.attrs[attribute.name], \
                                         msg = "Dataset \'%s:%s\' constant value: %s == %s" \
                                         %(hdf_dset_name, attribute.name, attribute.value, hdf_dset.attrs[attribute.name]) )


def main():
    class AbsPathAction(argparse.Action):
        def __call__(self, parser, namespace, value, option_string=None):
            value = os.path.abspath(value)
            if not os.path.exists(value):
                raise IOError('No such file: \'%s\''%value)
            setattr(namespace, self.dest, value)
    parser = argparse.ArgumentParser(description="Testing of the HDF5 file writer XML layout feature"
                                     "This test compare a HDF5 file with an XML definition file.")
    parser.add_argument('inifile', metavar='INIFILE', type=str, nargs='?', action=AbsPathAction, default='test_hdf_xml.ini',
                        help='INI file which can list a number of combinations of HDF5 and XML files to be checked')
    parser.add_argument('--verbosity', '-v', metavar='LEVEL', dest='verbosity', action='store', type=int, default=1,
                        help='Verbosity of the unittest output')
    parser.add_argument('--failfast', '-f', dest='failfast', action='store_true', default=False,
                        help='Abort on first encounted test failure or error')
    
    args = parser.parse_args()
    args = vars(args)

    suite = unittest.TestSuite()
    for cls in make_classes(TestHdfXml, args['inifile']):
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(cls))
    unittest.TextTestRunner(verbosity=args['verbosity'], failfast=args['failfast']).run(suite)
    
            
if __name__=="__main__":
    main()
