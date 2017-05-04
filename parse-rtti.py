from idaapi import *
from idc import *

def DemangleNameAtAddress(name_addr):
    demangle_string = '??_7' + GetString(name_addr)[4:] + '6B@';
    s = Demangle(demangle_string, 8)
    if s != None:
        return s[0:len(s)-11]
    else:
        return GetString(name_addr)

"""
struct RTTITypeDescriptor
{
	void** pVMT;
	dword spare;
	char name[1];
};

"""

class RTTITypeDescriptor:
    def __init__(self, ea):
        self.ea = ea;
    def GetName(self):
		return GetString((self.ea + 8));
    def GetDemangledName(self):
        return DemangleNameAtAddress((self.ea + 8));

"""
struct RTTIClassHierarchyDescriptor
{
	dword signature;		// Always zero?
	dword attributes;		// Bit 0 set = multiple inheritance, bit 1 set = virtual inheritance.
	dword numBaseClasses;	// Number of classes in pBaseClassArray.
	RTTIBaseClassArray* pBaseClassArray;
};
"""

class RTTIClassHierarchyDescriptor:
    def __init__(self, ea):
        self.ea = ea;
    def GetSignature(self):
        return Dword(self.ea);
    def GetAttributes(self):
        return Dword(self.ea + 4);
    def GetNumBaseClasses(self):
        return Dword(self.ea + 8);
    def GetBaseClassArray(self):
        return [RTTIBaseClassDescriptor(Dword(Dword(self.ea + 12) + a * 4)) for a in range(0, self.GetNumBaseClasses()) ]

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

class RTTICompleteObjectLocator:
    def __init__(self, ea):
        self.ea = ea;
    def GetSignature(self):
        return Dword(self.ea);
    def GetOffset(self):
        return Dword(self.ea + 4);
    def GetConstructorOffset(self):
        return Dword(self.ea + 8);
    def GetTypeDescriptor(self):
		return RTTITypeDescriptor(Dword(self.ea + 12));
    def GetClassHierarchyDescriptor(self):
        return RTTIClassHierarchyDescriptor(Dword(self.ea + 16));

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

class RTTIBaseClassDescriptor:
    def __init__(self, ea):
        self.ea = ea;
    def GetTypeDescriptor(self):
        return RTTITypeDescriptor(Dword(self.ea));
    def GetNumContainedBases(self):
        return Dword(self.ea + 4);
    def GetMemberDisplacement(self):
        return Dword(self.ea + 8);
    def GetVtableDisplacement(self):
        return Dword(self.ea + 12);
    def GetInternalDisplacement(self):
        return Dword(self.ea + 16);
    def GetAttributes(self):
        return Dword(self.ea + 20);
    

def PrintBaseObject(rttiObject, level = 0):
    print(("\t" * level) + "@RTTI " + rttiObject.GetTypeDescriptor().GetDemangledName());
    print(("\t" * level) + "{");
    print(("\t" * (level + 1)) + "@MDISP " + str(rttiObject.GetMemberDisplacement()));
    print(("\t" * (level + 1)) + "@VDISP " + str(rttiObject.GetInternalDisplacement()));
    print(("\t" * (level + 1)) + "@IDISP " + str(rttiObject.GetInternalDisplacement()));
    print(("\t" * level) + "}");


def PrintCompleteObject(rttiObject, level = 0):
    print("@RTTI %s" % rttiObject.GetTypeDescriptor().GetDemangledName());
    print(("\t" * level) + "{");
    for bo in rttiObject.GetClassHierarchyDescriptor().GetBaseClassArray():
        PrintBaseObject(bo, level + 1);
    print(("\t" * level + "}"))
    

startAddr = ScreenEA();

searchStr = "`vftable";

addr = FindText(startAddr, SEARCH_DOWN|SEARCH_NEXT, 0, 0, searchStr);

rttiObject = RTTICompleteObjectLocator(Dword(addr - 4));

PrintCompleteObject(rttiObject);

"""
while(addr != BADADDR):
    isValid = True;
    mangledName = Name(Addr);
"""
