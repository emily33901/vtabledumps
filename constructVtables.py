import os
import re

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

def FindUniqueName(string):
    i = FindLastNumber(string);
    return string[i:string.find(".")];

def FindUniqueMatchingFile(fileName, folder):
    searchedString = FindUniqueName(fileName);
   
    for file in os.listdir(folder):
        if(file.find(searchedString) != -1):
            return searchedString;
        
    for file in os.listdir(folder):
        found = TryMatchName(file, searchedString);
        if(found):
            return found;

def FindMatchingWindowsFile(fileName, folder):
    searchedString = FindUniqueName(fileName);
   
    for file in os.listdir(folder):
        if(file.find(searchedString) != -1):
            return file;
        
    for file in os.listdir(folder):
        i = 0;
        while(i < len(file)):
            if(file.find(searchedString[:-i]) != -1):
                return file;
            i += 1;

def UsesMultipleInheritance(fileName, folder):
    searchedString = FindUniqueName(fileName);
    foundFiles = [];
    i = 0;
    for file in os.listdir(folder):
        foundIndex = file.find(searchedString)
        if(foundIndex != -1):
            if(file.find("@", 0, foundIndex) != -1 || file.find("@", 0, foundIndex) != foundIndex + 1):
                # this is from inheritance not actual class name
                # or
                # this name is longer than we are expecting
                continue;
            foundFiles.append(file);
            i += 1;
    return i > 1, foundFiles;

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
    
def ProcessFolderPair(osx_folder, win_folder, out_folder):
    i = 0
    for file in os.listdir(osx_folder):
        mi, found = UsesMultipleInheritance(file, win_folder);
        if(mi):
           print("----> Uses multiple inheritance!");
           print("----> Unique name: " + FindUniqueName(file));
           for f in found:
               print("----> ----> " + f);

        win_file = FindMatchingWindowsFile(file, win_folder);

        out_file = out_folder + "\\" + file;
        print(out_file);
        ProcessVtablePair(osx_folder + "\\" + file, win_folder + "\\" + win_file, out_file);
        
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
            ProcessFolderPair("." + "\\" + file, "." + "\\" + newFile, "." + "\\" + output);
