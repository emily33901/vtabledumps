import fnmatch;
import re;

# standalone module

# takes a cpp class and returns the vtable representation in my "standard vtable layout"

# first line MUST include the classname

#toMutate = input("enter class:\n");

toMutate = """
class IHandleEntity
{
public:
	virtual ~IHandleEntity() {}
	virtual void SetRefEHandle( const CBaseHandle &handle ) = 0;
	virtual const CBaseHandle& GetRefEHandle() const = 0;
};
"""

whitespace = ["\n", " ", "\t", "*"];
def FindNextWhitespace(string, start = 0):
	minList = [];
	for w in whitespace:
		f = string.find(w, start);
		if(f != -1):
			minList.append(f);
	return min(minList);

def FindPrevWhitespace(string, start = 0):
	minList = [];
	for w in whitespace:
		f = string.rfind(w, 0, start);
		if(f != -1):
			minList.append(f);
	return max(minList);

firstSpaceIndex = toMutate.find(" ");
classname = "".join(toMutate[firstSpaceIndex:min(toMutate.find("\n", firstSpaceIndex + 1), toMutate.find(" ", firstSpaceIndex + 1))].split());

lastVirtualIndex = 0;

output = "";

counter = 0;

while True:
	lastVirtualIndex = toMutate.find("virtual", lastVirtualIndex + 1);

	if(lastVirtualIndex == -1):
		break;

	closeBraceLoc = toMutate.find(" = 0;", lastVirtualIndex);

	openBraceLoc = toMutate.rfind("(", 0, closeBraceLoc);

	fnameBegin = FindPrevWhitespace(toMutate, openBraceLoc);

	print(str(counter) + "\t" + classname + "::" + toMutate[fnameBegin + 1:closeBraceLoc]);
	
	counter += 1;
