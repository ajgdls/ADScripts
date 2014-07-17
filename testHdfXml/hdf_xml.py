#!/bin/env dls-python
import xml.dom.minidom as xml

CONSTANT = 'constant'
NDATTRIBUTE = 'ndattribute'
GROUP = 'group'
DATASET = 'dataset'
ATTRIBUTE = 'attribute'
SOURCE = 'source'
DETECTOR = 'detector'
NAME = 'name'
INT = 'int'
FLOAT = 'float'
WHEN = 'when'
TYPE = 'type'
VALUE = 'value'

class HdfAttribute:
    def __init__(self, name, parent, source):
        self.name = name
        self.parent = parent
        self.source = None
        try:
            [CONSTANT, NDATTRIBUTE].index(source)
            self.source = source
        except ValueError:
            raise "\'%s\' is not a valid attribute source (in attribute: %s)" % (source, name)
        # constant details
        self.type = None
        self.value = None
        # NDAttribute details
        self.ndattribute = None
        self.when = None
        
    def is_constant(self):
        return self.source == CONSTANT
    def is_ndattribute(self):
        return self.source == NDATTRIBUTE
    def __repr__(self):
        s = "<HdfAttribute: %s %s[%s]"%(self.source, self.parent, self.name) 
        if self.is_constant():
            s  += " = %s"%(self.value)
        elif self.is_ndattribute():
            s  += ": %s"%(self.ndattribute)
        s += ">"
        return s

def getChildrenByName(node, name):
    '''Utility function that seems to be missing from the xml.dom.minidom module'''
    for child in node.childNodes:
        if child.localName==name:
            yield child

class HdfXmlDefinition:
    ''' Read the XML definition of the layout of a HDF5 file.
    The layout model is populated in containers within the class: gropus and datasets which
    in turn contain attributes.
    The group and dataset containers can then be used to verify the correct configuration
    of groups and datasets inside a generated HDF5 file.
    
    Attributes:
        groups:   Dictionary of groups as defined in the XML definition. 
                  The keys are full names and the values are tuples: 
                    <bool: default destination>, 
                    <Attribute Dictionary: {Name: HdfAttribute}>
        datasets: Dictionary of datasets as defined in the XML definition.
                  The keys are full names and the values are tuples:
                    <str: dataset source [detector, ndattribute]>, 
                    <NDAttribute source string or None>,
                    <Attribute Dictionary: {Name: HdfAttribute}> 
    '''
    def __init__(self):
        # The resulting definition from the XML will be loaded into these containers
        self.groups = dict()
        self.datasets = dict()
        self.attributes = list()
        
    def populate(self, xmlfile):
        dom = xml.parse ( xmlfile ) 
        self._handle_groups( dom.getElementsByTagName(GROUP) )
        self._handle_datasets( dom.getElementsByTagName(DATASET))
        self._handle_attributes( dom.getElementsByTagName(ATTRIBUTE))

    def _parent_name(self, element):
        parent = element.parentNode
        parent_name = ""
        delimiter = ""
        while parent.getAttribute(NAME) != "":
            parent_name = "%s%s%s"%( parent.getAttribute(NAME), delimiter, parent_name )
            parent = parent.parentNode
            delimiter = "/"
        parent_name = "%s%s" %( delimiter, parent_name)
        return parent_name
    
    def _handle_groups(self, groups):
        for group in groups:
            group_name = "/".join([self._parent_name(group), group.getAttribute(NAME)])
            ndattr_default = group.hasAttribute('ndattr_default')
            hdfattributes = self._get_attributes(group)
            self.groups.update( {group_name: ( ndattr_default, hdfattributes) } )
        
    def _handle_datasets(self, datasets):
        for dataset in datasets:
            dset_name = "/".join([self._parent_name(dataset), dataset.getAttribute(NAME)])
            dset_source = dataset.getAttribute(SOURCE)
            dset_ndattribute = None
            if dset_source == NDATTRIBUTE:
                dset_ndattribute = dataset.getAttribute(NDATTRIBUTE)
            dset_hdfattributes = self._get_attributes(dataset)
            self.datasets.update( {dset_name: (dset_source, dset_ndattribute, dset_hdfattributes)})
                
    def _get_attributes(self, element):
        attributes = dict()
        for child in getChildrenByName(element, ATTRIBUTE):
            attr_name = child.getAttribute(NAME)
            attr_parent = self._parent_name(child)
            attr_source = child.getAttribute(SOURCE)
            attribute = HdfAttribute(attr_name, attr_parent, attr_source)
            # source: "constant" attributes have their type and value defined in the XML
            if attribute.is_constant():
                attribute.type = child.getAttribute(TYPE)
                attribute.value = child.getAttribute(VALUE)
                if attribute.type == INT:
                    attribute.value = [int(val) for val in attribute.value.split(',')]
                    if len(attribute.value) == 1: attribute.value = attribute.value[0]
                elif attribute.type == FLOAT:
                    attribute.value = [float(val) for val in attribute.value.split(',')]
                    if len(attribute.value) == 1: attribute.value = attribute.value[0]
            # source: "ndattribute" specify an (areaDetector) NDAttribute name where to get data from
            # and a 'when' parameter which can be 'OnFileClose', 'OnFileOpen' or defaults to nothing (on every frame)
            elif attribute.is_ndattribute():
                attribute.ndattribute = child.getAttribute(NDATTRIBUTE)
                attribute.when = child.getAttribute(WHEN)
            attributes.update( {attr_name: attribute} )
        return attributes

        
    def _handle_attributes(self, attributes):
        for attr in attributes:
            attr_name = attr.getAttribute(NAME)
            attr_parent = self._parent_name(attr)
            attr_source = attr.getAttribute(SOURCE)
            attribute = HdfAttribute(attr_name, attr_parent, attr_source)
            # source: "constant" attributes have their type and value defined in the XML
            if attribute.is_constant():
                attribute.type = attr.getAttribute(TYPE)
                attribute.value = attr.getAttribute(VALUE)
                if attribute.type == INT:
                    attribute.value = [int(val) for val in attribute.value.split(',')]
                    if len(attribute.value) == 1: attribute.value = attribute.value[0]
                elif attribute.type == FLOAT:
                    attribute.value = [float(val) for val in attribute.value.split(',')]
                    if len(attribute.value) == 1: attribute.value = attribute.value[0]
            # source: "ndattribute" specify an (areaDetector) NDAttribute name where to get data from
            # and a 'when' parameter which can be 'OnFileClose', 'OnFileOpen' or defaults to nothing (on every frame)
            elif attribute.is_ndattribute():
                attribute.ndattribute = attr.getAttribute(NDATTRIBUTE)
                attribute.when = attr.getAttribute(WHEN)
            self.attributes.append( attribute )
            
            
def main():
    xml_def = HdfXmlDefinition()
    xml_def.populate('data/layout.xml')
    print xml_def.groups, "\n"
        
    print xml_def.datasets, "\n"
    
if __name__=="__main__":
    main()
    



