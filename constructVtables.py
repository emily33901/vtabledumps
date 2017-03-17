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

def FindUniqueName(string):
        i = FindLastNumber(string);
        return string[i:string.find(".")];

def FindUniqueMatchingFile(fileName, folder):
    searchedString = FindUniqueName(fileName);
   
    #print(searchedString);
    for file in os.listdir(folder):
        if(file.find(searchedString) != -1):
            #print("\n\nmatch: win " + file + " osx " + fileName);
            return searchedString;
        
    for file in os.listdir(folder):
        i = 0;
        while(i < len(file)):
            if(file.find(searchedString[:-i]) != -1):
                #print("\n\n2match: win " + file + " osx " + searchedString[:-i]);
                return searchedString[:-i];
            i += 1;

def FindMatchingWindowsFile(fileName, folder):

    searchedString = FindUniqueName(fileName);
   
    #print(searchedString);
    for file in os.listdir(folder):
        if(file.find(searchedString) != -1):
            #print("\n\nmatch: win " + file + " osx " + fileName);
            return file;
        
    for file in os.listdir(folder):
        i = 0;
        while(i < len(file)):
            if(file.find(searchedString[:-i]) != -1):
                #print("\n\n2match: win " + file + " osx " + searchedString[:-i]);
                return file;
            i += 1;

    # stage 2

def ProcessContents(osx, win, file):
    #print(osx);
    #print(win);
    win_index_offset = 0;
    first_destructor = True;

    with open(file, "w") as output:

        def finishLine():
            output.write("\r\n");

        output.write("//=================================\r\n");
        output.write("// Merged Vtable - Errors expected \r\n");
        output.write("//=================================\r\n");
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

            #print(osx_line);
            index = win_line[0:win_line.find("\t")];
            text = osx_line[len(str(index)):];
            output.write(index + text);
            finishLine();
        finishLine();

def ProcessVtablePair(osx, win, file):
    with open(osx) as osx_file, open(win) as win_file:
        ProcessContents(osx_file.read().split("\n"), win_file.read().split("\n"), file);
    
def ProcessFolderPair(osx_folder, win_folder, out_folder):
    #print("osx " + osx_folder + " win " + win_folder);
    i = 0
    for file in os.listdir(osx_folder):

        win_file = FindMatchingWindowsFile(file, win_folder);


        #print(file + " | " + win_file);
        out_file = out_folder + "\\" + file;
        print(out_file);
        ProcessVtablePair(osx_folder + "\\" + file, win_folder + "\\" + win_file, out_file);
        
        # only do one for now
        i += 1;
        #if(i > 100):
        #    break;

        
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
