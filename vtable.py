class vtable:
    # this class represents a vtable

    # it should:
    #   track functions and which clases they belong to
    #   be able to output a c++ representation of this vtable
    #   be able to calculate this from input files
    def __init__(self, osx_file, win_files):
        self.osx_file = osx_file;
        self.win_files = win_files;
        self.classnames = [];
        self.functions = [];
        self.process();
        print("processed!");
        print("classes: ");
        print(self.classnames);
        print("functions:");
        print(self.functions);

    # processes a line and returns:
    #   the osx index
    #   the class name
    #   the function prototype (that being the function)
    # example:
    # 6 CGame::SetGameWindow(void *)
    def processFunctionLine(self, line):
        split = line.split("\t");
        classname = split[1][:split[1].find("::")];
        functionname = split[1][split[1].find("::") + 2:-1]; # strip \n
        return int(split[0]), classname, functionname;

    def process(self):
        # first take the osx file and process all the lines that arent comments
        with open(self.osx_file) as osxFile:
            for line in osxFile:
                if(line.find("//") == 0):
                    continue;
                index, classname, functionname = self.processFunctionLine(line);
                if(classname not in self.classnames):
                    self.classnames.append(classname);
                if(functionname not in map(lambda l: l[0], self.functions)):
                    self.functions.append([functionname, classname, index]);

def main():
    v = vtable("steamclient_osx/__ZTV5CUser.txt", "badwinname")

if __name__ == "__main__":
    main();
