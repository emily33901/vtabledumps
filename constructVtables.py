import os
import re
import subprocess
import msvcDemangler

def FileExists(filename):
    for file in os.listdir():
        if(file == filename):
            return True;
    return False;

def FindLastNumber(string):
    lastNumber = -1;
    for i in range(len(string)):
        if(string[i].isdigit()):
            lastNumber = i;
    return lastNumber + 1;

def TryMatchName(string1, string2):
    i = 0;
    while(i < len(string1)):
        if(file.find(string2[:-i]) != -1):
            return string2[:-i];
        i += 1;

def FindUniqueWindowsName(string):
    if(string.find("___7_") != -1):
        string = string[3:]; # only remove 3 as the next 2 will be removed next
    n, _ = msvcDemangler.symbol_demangle("??" + string[2:-4], False);

    # if the demangled name contains a for then that is what is unique for this vtable
    forindex = n.find("for");
    if(forindex != -1):
        #print(n[n.find("`", forindex) + 1:n.find("'", forindex)]);
        return n[n.find("`", forindex) + 1:n.find("'", forindex)];
    # otherwise we want to return the first item before the ::
    else:
        return n[n.find(" ") + 1:n.find("::")];
    

def FindUniqueOSXName(string):
    c = subprocess.run(["__cxa_demangle", string[1:-4]], stdout=subprocess.PIPE, shell=True);
    if(c.stdout != None and c.stdout[0] != "-"):
        #print(c.stdout);
        # vtable name is whatever is after the for to the end
        n = str(c.stdout);
        return n[n.find("for ") + 5:-1];

def CreateOSXFileMapping


# assumes string is already unique
def FindMatchingOSXFile(string, folder):
    for file in os.listdir(folder):
        uniqueName = FindUniqueOSXName(file);
        if(uniqueName == string):
            print(string + " -- " + uniqueName);
            return file;

def ProcessContents(osx, win, file):
    win_index_offset = 0;
    first_destructor = True;

    with open(file, "w") as output:

        def finishLine():
            output.write("\n");

        output.write("//=================================\n");
        output.write("// Merged Vtable - Errors expected \n");
        output.write("//=================================\n");
        for i in range(len(osx)):
            osx_line = osx[i];

            if(osx_line == ""):
                continue;

            # dont process comments
            if(osx_line.find("//") == 0):
                output.write(osx_line);
                finishLine();
                continue;

            # only the first destructor counts
            if(osx_line.find("~") != -1):
                if(first_destructor):
                    first_destructor = False;
                else:
                    win_index_offset -= 1;
                    continue;

            if(i + win_index_offset >= len(win)):
                continue;
            
            win_line = win[i + win_index_offset];

            if(win_line == ""):
                continue;

            # print the windows index and the mac function
            index = win_line[0:win_line.find("\t")];
            text = osx_line[len(str(index)):];
            output.write(index + text);
            finishLine();
        finishLine();

def ProcessVtablePair(osx, win, file):
    with open(osx) as osx_file, open(win) as win_file:
        ProcessContents(osx_file.read().split("\n"), win_file.read().split("\n"), file);

# process everything windows first
def ProcessFolderPair(osx_folder, win_folder, out_folder):
    i = 0
    for file in os.listdir(win_folder):
        if(file.find("CUser") != -1):
            print(FindMatchingOSXFile(FindUniqueWindowsName(file), osx_folder));

        #osx_file = FindMatchingWindowsFile(file, win_folder);

        #out_file = out_folder + "/" + file;
        #print(out_file);
        #ProcessVtablePair(osx_folder + "/" + file, win_folder + "/" + win_file, out_file);
        
# main
for file in os.listdir():
    fileSplit = file.split("_");
    #print(fileSplit);
    
    if(len(fileSplit) > 1):
        
        fileExension = ""
        
        if(fileSplit[1] == "osx"):
            fileExension = "win32";
        else:
            continue;   # we dont want to do from windows to osx
                        # that would be pointless
        
        newFile = fileSplit[0] + "_" + fileExension;

        exists = FileExists(newFile);

        if(exists):
            output = fileSplit[0] + "_" + "merge";
            ProcessFolderPair("." + "/" + file, "." + "/" + newFile, "." + "/" + output);
