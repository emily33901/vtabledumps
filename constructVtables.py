import os
import sys
import re
import subprocess
import threading
import platform
import fnmatch

import msvcDemangler
import merge_subs

def FileExists(filename):
    for file in os.listdir():
        if(file == filename):
            return True;
    return False;

def TryMatchName(string1, string2, thresh):
    i = 0;
    if(len(string2) > len(string1)):
        return None;
    while(i < len(string1)):
        #print(string2[i:]);
        if(string1.find(string2[i:]) != -1):
            if(len(string2[i:]) > thresh):
                return string2[i:];
        i += 1;

MergeSubs = [];
def EnumerateMergeSubsForFolder(folder):
    print("enumerating merge subs...");
    global MergeSubs;
    MergeSubs = [];
    for file in os.listdir(folder):
        if(fnmatch.fnmatch(file, "*merge_subs.txt")):
            MergeSubs = merge_subs.ParseMergeSub(folder + "/" + file);

    print("done " + str(MergeSubs));
            
def FindUniqueWindowsName(string):
    if(string.find("___7_") != -1):
        string = string[3:]; # only remove 3 as the next 2 will be removed next
    n, _ = msvcDemangler.symbol_demangle("??" + string[2:-4], False);

    # if the demangled name contains a for then that is what is unique for this vtable
    forindex = n.find("for");
    if(forindex != -1):
        return n[n.find("`", forindex) + 1:n.find("'", forindex)];
    # otherwise we want to return the first item before the ::
    else:
        return n[n.find(" ") + 1:n.find("::`vftable'")];
    

def FindUniqueOSXName(string):
    c = None;
    p = platform.machine();
    if(os.name == "posix"):
        c = subprocess.run(["./__cxa_demangle_" + p, string[1:-4]], stdout=subprocess.PIPE, shell=False);
    else:
        c = subprocess.run(["__cxa_demangle", string[1:-4]], stdout=subprocess.PIPE, shell=True);
    
    #print(c.stdout);
    
    if(c.stdout != None and c.stdout[0] != "-"):
        #print(c.stdout);
        # vtable name is whatever is after the for to the end
        n = str(c.stdout);
        return n[n.find("for ") + 4:-1];

OSXFileNameMap = {};
def LookupUniqueOSXName(string):
    global OSXFileNameMap;
    try:
        if(OSXFileNameMap[string] != None):
            return OSXFileNameMap[string]
    except:
        OSXFileNameMap[string] = FindUniqueOSXName(string);
        #print("m " + string + " => " + OSXFileNameMap[string]);
        return OSXFileNameMap[string];

def NarrowOSXFileDir(string, folder):
    out = []
    for file in os.listdir(folder):
        n = TryMatchName(file, string, 6);
        if(n != None):
            #print(file);
            out.append(file);

    #input(out);
    return out;

# assumes string is already unique
def FindMatchingOSXFileCore(string, folder):
    subs = [string] + merge_subs.TryMerge(string, MergeSubs);

    for file in folder:
        uniqueName = LookupUniqueOSXName(file);
        for string in subs:
            #print(string + " -- " + uniqueName);
            if(uniqueName == string):
                #input()
                return file;
            
    print("no vtable match found for " + string);

def FindMatchingOSXFile(string, folder):
    narrowDir = NarrowOSXFileDir(string, folder);
    if(narrowDir != []):
        r = FindMatchingOSXFileCore(string, narrowDir);
        if(r != None):
            return r;

    return FindMatchingOSXFileCore(string, os.listdir(folder));
        
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
        threading.Thread(target=ProcessContents, args=(osx_file.read().split("\n"), win_file.read().split("\n"), file)).start();

def EnumerateOSXNames(folder):
    print("performing osx demangling", end="");
    threads = [];
    for file in os.listdir(folder):
        print(".", end="", flush=True);
        t = threading.Thread(target=LookupUniqueOSXName, args=(file,));
        t.start();
        threads.append(t);

    for t in threads:
        t.join();

    print("done");

# process everything windows first
def ProcessFolderPair(osx_folder, win_folder, out_folder):
    i = 0;
    global OSXFileNameMap;
    OSXFileNameMap = {};
    EnumerateOSXNames(osx_folder);

    global MergeSubs;
    MergeSubs = [];
    EnumerateMergeSubsForFolder(win_folder);
    
    for file in os.listdir(win_folder):
        #print(file);
        try:
            unique = FindUniqueWindowsName(file);
        except:
            continue;
        print(unique);
        if(unique == "charNode" or unique.find("virtual") != -1):
            continue;

        osx_file = FindMatchingOSXFile(unique, osx_folder);

        if(osx_file == None):
            continue;

        #osx_file = FindMatchingWindowsFile(file, win_folder);

        out_file = out_folder + "/" + file;
        #print(out_file);
        ProcessVtablePair(osx_folder + "/" + osx_file, win_folder + "/" + file, out_file);

def ProcessFileSplit(file):
    fileSplit = file.split("_");
    #print(fileSplit);
    
    if(len(fileSplit) > 1):
        
        fileExension = ""
        
        if(fileSplit[1] == "osx"):
            fileExension = "win32";
        else:
            return;   # we dont want to do from windows to osx
                        # that would be pointless
        
        newFile = fileSplit[0] + "_" + fileExension;

        exists = FileExists(newFile);

        if(exists):
            output = fileSplit[0] + "_" + "merge";
            print("merging " + file + " + " + newFile + " => " + output);
            ProcessFolderPair("." + "/" + file, "." + "/" + newFile, "." + "/" + output);
        
# main
print("platform " + platform.machine());
print("argv " + str(sys.argv));
if(len(sys.argv) > 1):
    ProcessFileSplit(sys.argv[1]);
else:
    for file in os.listdir():
        ProcessFileSplit(file);
