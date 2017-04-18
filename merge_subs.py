import re
import sys
import fnmatch

def TryMergeSub(mode, str1, pat, sub):
    if(fnmatch.fnmatch(str1, pat)!= True):
        return None;
    if(mode == "replace"):
        # replace is always from index 0
        transfer = "";
        wildcard = pat.find("*");
        if(wildcard != -1):
            transfer = str1[wildcard:];

        wildcard = sub.find("*");

        if(wildcard != -1):
            return sub[:wildcard] + transfer + sub[wildcard + 1:];
        else:
            return sub;
    else:
        raise NameError("\"" + mode + "\" is not a valid mode");

def TryMerge(string, l):
    out = [];
    for t in l:
        n = TryMergeSub(t[0], string, t[1], t[2]);
        if(n != None):
            out.append(n);

    return out;
    
def ParseMergeSub(filename):
    out = [];
    with open(filename) as file:
        for line in file:
            if(line[0] == "#"):
                # comments
                continue;
            out.append(line[:-1].split(" "));
    return out;

# main
if __name__ == "__main__":
    print(str(sys.argv[1:]));
    o = [];
    for c in ParseMergeSub(sys.argv[1]):
        o.append(TryMergeSub(c[0], sys.argv[2], c[1], c[2]));
    print(o);
