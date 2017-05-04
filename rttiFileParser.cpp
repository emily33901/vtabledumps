#include <cstdlib>
#include <windows.h>

// Declarations
struct RTTICompleteObjectLocator;
struct RTTIClassHierarchyDescriptor;
struct RTTITypeDescriptor;
typedef RTTIClassHierarchyDescriptor* RTTIBaseClassArray;

// Get the CompleteObjectLocator from an instance.
static inline const RTTICompleteObjectLocator* RTTIGet( const void* inst, long offset = 0 )
{
	return reinterpret_cast<const RTTICompleteObjectLocator*>( getvtable( inst, offset )[ -1 ] );
}

struct RTTITypeDescriptor
{
	void** pVMT;
	dword spare;
	char name[1];
};

struct RTTICompleteObjectLocator
{
	dword signature;	// Always zero ?
	dword offset;		// Offset of this vtable in the complete class.
	dword cdOffset;		// Constructor displacement offset.
	RTTITypeDescriptor* pTypeDescriptor; // TypeDescriptor of the complete class.
	RTTIClassHierarchyDescriptor* pClassDescriptor; // Describes inheritance hierarchy.
};

struct RTTIClassHierarchyDescriptor
{
	dword signature;		// Always zero?
	dword attributes;		// Bit 0 set = multiple inheritance, bit 1 set = virtual inheritance.
	dword numBaseClasses;	// Number of classes in pBaseClassArray.
	RTTIBaseClassArray* pBaseClassArray;
};

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


int main()
{
	char *buffer = new char[4000000];

	std::string filePath = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Team Fortress 2\\tf\bin\\client.dll"
	FILE *client_dll = fopen(filePath.c_str(), "r");

	DWORD RebasePointer = DWORD [&](DWORD addr)
	{
		return addr + &buffer;
	};

	if (client_dll)
	{
		size_t newLen = fread(buffer, sizeof(char), 4000000, client_dll);

		if (ferror(client_dll) != 0) {
			fputs("Error reading file", stderr);
		}
		else {
			buffer[newLen++] = '\0'; // Just to be safe. 
		}


		// Some offsets that are stolen from ida
		DWORD 

		fclose(client_dll);

	}
	else
	{
		Log::Error("Error loading %s", filePath.c_str());
	}

}