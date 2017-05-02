import os
import fnmatch
import platform
import threading
import ast
import copy

import msvcDemangler
import merge_subs
import subprocess

# TODO list:
#   vtable dumper needs to include as much info as possible about each function
#       UPDATE THE IDA FUNCTION TO INCLUDE RTTI: THIS WILL INCLUDE THE CLASS HIERARCHY
#       WE NEED TO TRY TO INCLUDE RETURN TYPE
#       strings, argument number, (maybe control flow)
#       should probably include whether it is an mi class
#           (i have a feeling its alot easier for ida to figure out)
#   or we could just save the type info to a the typeinfo_vtable.txt file (this would help alot) 
#
#   windows filename map
#
#


class vtable:
    # this class represents a vtable

    # it should:
    #   track functions and which clases they belong to
    #   be able to output a c++ representation of this vtable (complete with mi interpretation)
    #   be able to calculate this an input files


    # this is a static store of all the hierarchies we have already enumerated
    # kv map where key: string - vtable name value: vtable with hierarchy
    # this works because the hierarchy is deterministic
    enumeratedStructures = {}

    def __init__(self, win_file, win_folder, osx_folder, is_mi = False, parent = None):
        self.win_file = win_file;
        self.win_vtable = self.FindUniqueWinName(win_file);
        self.win_folder = win_folder;
        self.osx_folder = osx_folder;
        self.classnames = [];
        self.functions = [];
        self.hasDestructor = 0;
        self.MergeSubs = [];
        self.possibleWindowsVtables = [];
        self.osxVtables = [];
        self.miVtables = [];
        self.is_mi = is_mi;
        self.OSXFileNameMap = {};

        # this is a list of vtables that represent the structure of this vtable
        # this instance is the top of this structure - but not necessarily top overall
        self.hierarchy = [];

        # this points to the parent of this vtable - essentially doubly linked list
        self.parent = parent;

        self.top = parent.top if parent != None else self;
        # check to see if we are already enumerated 
        try:
            self = vtable.enumeratedStructures[self.win_vtable];
            miString = " MI" if is_mi == True else "";
            print("using enumerated values for vtable " + self.win_vtable + miString + "...");
            return;
        except:
            pass; # carry on setup if this fails

        print("constructing vtable for " + self.win_vtable);


        self.EnumerateMergeSubsForFolder(self.win_folder);

        print("finding siblings...");
        
        self.possibleWindowsVtables, _ = self.FindSiblings();

        print("done.");

        # we now know if we are an mi class and what those mi vtables are
        # we now need to find matching osx files

        # first find all the osx vtable names
        self.EnumerateOSXNames(self.osx_folder);

        print("finding osx tables...");

        # next find the corresponding osx vtables to our vtables (this does merge subs for us)
        self.FindOSXVtables();

        print("done.");

        print("processing osx table...");

        # then process the real vtables
        self.ProcessOSX(False);

        print("done.");

        # once we have those, we need to recurse down the mi tables first
        # we do it in this order because the mi tables tend to not inherit anything
        # (or they dont exist)
        # this will contstruct the mi side of the hierarchy
        # we only need to do this as the top of the tree

        print("processing osx table for mi...");
        self.ProcessOSX(True);

        print("done.");        


        # copy to enumeratedStructures list
        vtable.enumeratedStructures[self.win_vtable] = self;

        #self.ProcessOSX();

        print("finished constructing vtable " + self.win_vtable + "\n\n");
        #print("processed vtable: " + self.win_vtable);
        #print("classes: ");
        #print(self.classnames);
        #print("functions:");
        #print(self.functions);
    
    alreadyPrinted = [];
    def RecursePrintHierarchy(self, l = 0):
        for v in self.hierarchy:

            # do base classes first
            # TODO: we also need to do MI classes firster
            
            v.RecursePrintHierarchy(l);
            
            miString = "MI" if v.is_mi == True else "Not MI";
            inheritString = " : " + ", ".join(map(lambda v: v.win_vtable, v.hierarchy)) if len(v.hierarchy) >= 1 else "";

            # begin class
            print("\n" + ('\t' * l) + "class " + v.win_vtable + inheritString + " { // " + miString);

            index = 0;
            for f in map(lambda l: l[0], v.functions):
                if f not in vtable.alreadyPrinted:
                    print(('\t' * (l + 1)) + "/*" + str(index) + "*/ virtual DWORD " + f + " = 0;");
                    index += 1;
                    vtable.alreadyPrinted.append(f);

            # end class
            print(('\t' * l) + "} // " + v.win_vtable + "\n\n");

    def PrintHierarchy(self):
        self.RecursePrintHierarchy(0);        
        print("class " + self.win_vtable + " : " + ", ".join(map(lambda v: v.win_vtable, self.hierarchy)) + " {");

        # TODO: DRY PRICIPLES
        index = 0
        for f in map(lambda l: l[0], self.functions):
            if f not in vtable.alreadyPrinted:
                print("\t/*" + str(index) + "*/virtual DWORD " + f + " = 0;");
                index += 1;
                vtable.alreadyPrinted.append(f);

        print("} // " + self.win_vtable);

            
    @staticmethod
    def RecurseCorrectHierarchy(v):
        contains = []
        ret = [];
        for nv in v.hierarchy:
            contains = contains + vtable.RecurseCorrectHierarchy(nv);
            #print("contains " + str(contains));
        for nv in v.hierarchy:
            for c in contains:
                if(c == nv.win_vtable):
                    try:
                        v.hierarchy.remove(nv);
                        #ret.append(c);
                        #print("removing " + c + " from " + v.win_vtable);
                        break;
                    except:
                        pass;
            else:
                ret.append(nv.win_vtable);

        return ret + contains;
                
    def CorrectHierarchy(self):
        oldR = [];
        while True:
            r = vtable.RecurseCorrectHierarchy(self.top);
            if(r == oldR):
                return;
            #print(str(r) + " | " + str(oldR));
            oldR = r;

    def FileToVtableName(self, string, osx):
        if(osx):
            return self.LookupUniqueOSXName(string);
        else:
            return self.LookupUniqueWinName(string);

    def EnumerateMergeSubsForFolder(self, folder):
        print("enumerating merge subs...");
        self.MergeSubs = [];
        for file in os.listdir(folder):
            if(fnmatch.fnmatch(file, "*merge_subs.txt")):
                self.MergeSubs = merge_subs.ParseMergeSub(folder + "/" + file);

        print("done " + str(self.MergeSubs));

    # processes a line and returns:
    #   the osx index
    #   the class name
    #   the function prototype (that being the function)
    # example:
    # 6 CGame::SetGameWindow(void *)
    unclassedFunctionCounter = 0;
    def processFunctionLine(self, line):
        split = line.split("\t");
        noClass = False;
        classname = "";
        if(split[1].find("::") != -1):
            classname = split[1][:split[1].find("::")];
        else:
             classname = self.win_vtable;
             noClass = True;
        functionname = split[1][split[1].find("::") + 2:-1]; # strip \n

        if(noClass == True):
            # make this unique (it is probably __cxa_pure_virtual)
            functionname = functionname + "_" + classname + "_" + str(vtable.unclassedFunctionCounter);
            vtable.unclassedFunctionCounter += 1;

        if(functionname[0] == "~"):
            self.hasDestructor = 1;
            return int(split[0]), classname, functionname;
        
        return int(split[0]) - self.hasDestructor, classname, functionname;

    def ProcessOSX(self, doMi):
        print("processing...");
        vtableList = self.osxVtables;
        if(doMi == True):
            vtableList = self.miVtables;

        # clear classnames from mi classes
        # TODO: this is a small fix for a bigger problem
        #   RETHINK THIS !
        self.classnames = [];

        for v in vtableList:
            print(str(v));
            if(v[0] == ""):
                continue;
            # first take the osx file and process all the lines that arent comments
            with open(v[0]) as osxFile:
                for line in osxFile:
                    if(line.find("//") == 0):
                        continue;
                    index, classname, functionname = self.processFunctionLine(line);
                    if(classname not in self.classnames):
                        self.classnames.append(classname);
                    if(functionname not in map(lambda l: l[0], self.functions)):
                        self.functions.append([functionname, classname, index]);
        
        if(len(self.classnames) <= 1):
            print("no children");
            return;
        else:
            print("found " + str(len(self.classnames)) + " classes: " + str(self.classnames));

        # copy classnames to allow us to remove them once we find them
        remainingClassnames = self.classnames.copy();
    
        # enumerate these classnames as vtables and add them to the hierarchy
        print("finding child vtables...")
        for c in remainingClassnames:
            for f in os.listdir(self.win_folder):
                if(f.find(c) == -1):
                    continue;
                try:
                    demangled = self.FindUniqueWinName(f);
                    if(demangled == c and demangled != self.win_vtable):
                        #print("===> removing " + c);
                        #remainingClassnames.remove(c);
                        v = vtable(f, self.win_folder, self.osx_folder, doMi, self);
                        self.hierarchy.append(vtable.enumeratedStructures[c]);
                        break;
                except:
                        continue;
        print("done.");

    # look for vtables that match what we need
    def FindOSXVtables(self):
        leftOverVtables = self.possibleWindowsVtables.copy();
        for file in os.listdir(self.osx_folder):
            osx_vtable_name = self.LookupUniqueOSXName(file);
            matched = False;
            for vtable in leftOverVtables:
                if(osx_vtable_name == vtable[2]):
                    miString = "";
                    if(vtable[0] == True):
                        miString = " MI";
                        self.miVtables.append([self.osx_folder + "/" + file, osx_vtable_name, []]);
                    else:
                        self.osxVtables.append([self.osx_folder + "/" + file, osx_vtable_name, []]);

                    print("match " + vtable[2] + " => " + osx_vtable_name + " (" + file + ")" + miString);

                    leftOverVtables.remove(vtable);
        for vtable in leftOverVtables:
            if(vtable[0] == True):
                self.miVtables.append(["", vtable[2], []]);
            else:
                self.osxVtables.append(["", vtable[2], []]);
            
        print("unable to match: ")
        for l in leftOverVtables:
            print("\t" + l[2]);
                
            

    # finds vtables that are siblings to this one
    # for example
    #   ??_7C_TFKnife@@6B@
    # siblings:
    #   ??_7C_TFKnife@@6BCGameEventListener@@@
    #   ??_7C_TFKnife@@6BIHasOwner@@@
    #   ??_7C_TFKnife@@6BIHasAttributes@@@
    #   ??_7C_TFKnife@@6BIModelLoadCallback@@@
    # so on
    def FindSiblings(self):
        out = [];
        mi = False;
        demangledName = self.FindUniqueWinName(self.win_file);

        #print(demangledName);
        #out.append([False, self.win_folder + "/" + win_file, df[df.find("const ") + 6:df.find("`") - 2]]);
        for file in os.listdir(self.win_folder):
            if(file.find(demangledName) != -1):
                # dont use FindUniqueWinFile here as we need to determine whether it is an mi vtable
                df, _ = msvcDemangler.symbol_demangle("??" + file[2:-4], False);

                isMi = False; # mi for this vtable
                if(df == "??" + file[2:-4]):
                    continue;

                if(df.find("for `") != -1):
                    mi = True;
                    isMi = True;
                
                vtableName = "";
                if(isMi == False):
                    vtableName = df[df.find("const ") + 6:df.find("`") - 2];
                    # check that these are equal - no substrings allowed
                    if(vtableName != demangledName):
                        continue;
                else:
                    # still do this check anyway this is important !
                    if(df[df.find("const ") + 6:df.find("`") - 2] != demangledName):
                        continue;
                    vtableName = df[df.find("for `") + 5:df.find("'}")];
                    # this is too check whether we are adding an unrelated vtable where we are the multiple inheritance part
                    if(vtableName == demangledName):
                        continue;
                
                subs = [vtableName] + merge_subs.TryMerge(vtableName, self.MergeSubs);

                for s in subs:
                    out.append([isMi, self.win_folder + "/" + file, s]);
                    print("sibling " + s + " (" + df + ")");

        return out, False;

    def FindUniqueWinName(self, string):
        if(string.find("___7_") != -1):
            string = string[3:]; # only remove 3 as the next 2 will be removed next
        n, _ = msvcDemangler.symbol_demangle("??" + string[2:-4], False);

        # if the demangled name contains a for then that is what is unique for this vtable
        #forindex = n.find("for");
        #if(forindex != -1):
        #    return n[n.find("`", forindex) + 1:n.find("'", forindex)];
        # otherwise we want to return the first item before the ::
        #else:
        return n[n.find(" ") + 1:n.find("::`vftable'")];

    def LookupUniqueOSXName(self, string):
        try:
            if(self.OSXFileNameMap[string] != None):
                return self.OSXFileNameMap[string]
        except:
            self.OSXFileNameMap[string] = self.FindUniqueOSXName(string);
            #print("m " + string + " => " + self.OSXFileNameMap[string]);
            return self.OSXFileNameMap[string];

    # this enumerates all the osx names in one go - could easily be improved
    def EnumerateOSXNames(self, folder):
        print("performing osx demangling", end="");
        try:
            with open(folder + "/" + "osx_demangle.txt", "r") as f:
                # if we get here this file is valid !
                for line in f:
                    self.OSXFileNameMap = ast.literal_eval(line)
                print("\ndone - loaded from file");
                return;
        except:
            pass;
        threads = [];
        for file in os.listdir(folder):
            print(".", end="", flush=True);
            t = threading.Thread(target=self.LookupUniqueOSXName, args=(file,));
            t.start();
            threads.append(t);

        for t in threads:
            t.join();

        # save this to disk for quicker loading next time
        with open(folder + "/" + "osx_demangle.txt", "w") as f:
            f.write(str(self.OSXFileNameMap));

        print("done");

    def FindUniqueOSXName(self, string):
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
                       
        

def main():
    v = vtable("___7C_TFKnife@@6B@.txt", "client_win32", "client_osx");
    v.CorrectHierarchy();
    v.PrintHierarchy();
    return;

if __name__ == "__main__":
    main();
