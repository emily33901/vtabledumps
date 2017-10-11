from idaapi import *;
from idc import *;
import json;

# general helper functions
def MakeValidFilename(filename):
    keepcharacters = (' ','.','_')
    return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip("_")

#
#
# Helper functions to do with JSON serialisation
# the indent of 4 could be changed to be more space efficent
# rather than providing clean, human readable output.
#
#
def default_jsonable(obj):
    d = obj.__dict__;
    d["__class"] = type(obj).__name__;
    return d;

class Jsonable(object):
    @classmethod
    def from_json(cls, json_string):
        attributes = json.loads(json_string);
        if not isinstance(attributes, dict) or attributes.pop('__class') != cls.__name__:
            raise ValueError;
        self = cls.__new__(cls);
        self.__dict__ = attributes;

        return self;

    def to_json(self):
        return json.dumps(self, indent=4, default=default_jsonable);


def DemangleNameAtAddress(name_addr):
    demangle_string = '??_7' + GetString(name_addr)[4:] + '6B@';
    s = Demangle(demangle_string, 8)
    if s != None:
        return s[0:len(s)-11]
    else:
        return GetString(name_addr)


# all address based structures inherit from this
class AddressBasedStructure(Jsonable):
    def __init__(self, ea):
        self.ea = ea;

"""
struct RTTITypeDescriptor
{
	void** pVMT;
	dword spare;
	char name[1];
};

"""

class TypeDescriptor(AddressBasedStructure):
    def __init__(self, ea):
        AddressBasedStructure.__init__(self, ea);
        self.name = GetString(self.ea + 8);
        self.demangled_name = DemangleNameAtAddress(self.ea + 8);
            
    def GetName(self):
        return self.name;
    def GetDemangledName(self):
        return self.demangled_name;

"""
struct RTTIClassHierarchyDescriptor
{
	dword signature;		// Always zero?
	dword attributes;		// Bit 0 set = multiple inheritance, bit 1 set = virtual inheritance.
	dword numBaseClasses;	// Number of classes in pBaseClassArray.
	RTTIBaseClassArray* pBaseClassArray;
};
"""

class ClassHierarchyDescriptor(AddressBasedStructure):
    def __init__(self, ea):
        AddressBasedStructure.__init__(self, ea);
        self.signature = Dword(self.ea);
        self.attributes = Dword(self.ea + 4);
        self.num_base_classes = Dword(self.ea + 8);
        self.base_classes = [BaseClassDescriptor(Dword(Dword(self.ea + 12) + a * 4)) for a in range(0, self.GetNumBaseClasses())];
    def GetSignature(self):
        return self.signature;
    def GetAttributes(self):
        return self.attributes;
    def GetNumBaseClasses(self):
        return self.num_base_classes;
    def GetBaseClasses(self):
        return self.base_classes;

"""
struct RTTICompleteObjectLocator
{
	dword signature;	// Always zero ?
	dword offset;		// Offset of this vtable in the complete class.
	dword cdOffset;		// Constructor displacement offset.
	RTTITypeDescriptor* pTypeDescriptor; // TypeDescriptor of the complete class.
	RTTIClassHierarchyDescriptor* pClassDescriptor; // Describes inheritance hierarchy.
};
"""

class CompleteObjectLocator(AddressBasedStructure):
    def __init__(self, ea):
        AddressBasedStructure.__init__(self, ea);
        self.signature = Dword(self.ea);
        self.offset = Dword(self.ea + 4);
        self.constructor_offset = Dword(self.ea + 8);
        self.type_descriptor = TypeDescriptor(Dword(self.ea + 12));
        self.hierarchy_descriptor = ClassHierarchyDescriptor(Dword(self.ea + 16));
    def GetSignature(self):
        return self.signature
    def GetOffset(self):
        return self.offset;
    def GetConstructorOffset(self):
        return self.constructor_offset;
    def GetTypeDescriptor(self):
        return self.type_descriptor;
    def GetClassHierarchyDescriptor(self):
        return self.heierarchy_descriptor;


"""
struct PMD
{
	int mdisp;	// Member displacement.
	int pdisp;	// Vbtable displacement.
	int vdisp;	// Displacement inside vbtable.
};

struct RTTIBaseClassDescriptor
{
	RTTITypeDescriptor* pTypeDescriptor; // Type descriptor of the class.
	dword numContainedBases;	// Number of nested classes following in the Base Class Array.
	PMD disp;					// Pointer-to-member displacement info.
	dword attributes;			// Flags, usually 0.
};
"""

class BaseClassDescriptor(AddressBasedStructure):
    def __init__(self, ea):
        AddressBasedStructure.__init__(self, ea);
        self.type_descriptor = TypeDescriptor(Dword(self.ea));
        self.num_contained_bases = Dword(self.ea + 4);
        self.member_displacement = Dword(self.ea + 8);
        self.vtable_displacement = Dword(self.ea + 12);
        self.internal_displacement = Dword(self.ea + 16);
        self.attributes = Dword(self.ea + 20);
        
    def GetTypeDescriptor(self):
        return self.type_descriptor;
    def GetNumContainedBases(self):
        return self.num_contained_bases;
    def GetMemberDisplacement(self):
        return self.member_displacement;
    def GetVtableDisplacement(self):
        return self.vtable_displacement;
    def GetInternalDisplacement(self):
        return self.internal_displacement;
    def GetAttributes(self):
        return self.attributes;

addr = ScreenEA();

# we need to keep track of what vtables we have actually processed and ones we havent 
# make this a function to make recursion easier


while(addr != -1):
    searchStr = "`vftable";
    addr = FindText(addr, SEARCH_DOWN|SEARCH_NEXT, 0, 0, searchStr);

    rttiObject = CompleteObjectLocator(Dword(addr - 4));

    encoded = rttiObject.to_json();

    #print(MakeValidFilename(rttiObject.GetTypeDescriptor().GetDemangledName()));

    filename = "C:\\Users\\joshua\\Documents\\GitHub\\vtabledumps\\test\\" + MakeValidFilename(rttiObject.GetTypeDescriptor().GetDemangledName()) + ".json";

    if(len(filename) > 260):
        filename = filename[0:255];

    print(len(filename));

    with open(filename, "w") as file:
        file.write(encoded);

    addr += 4

"""
while(addr != BADADDR):
    isValid = True;
    mangledName = Name(Addr);
"""
