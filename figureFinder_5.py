import re
import os
import sys
from shutil import copy2
from pathlib import Path


class TEXfile(object):
    def __init__(self, path):
        self.includefinder = re.compile(r'includegraphics\[*.*\]*\{.*\}')
        self.namefinder = re.compile(r'\{.*\}')
        self.cwd = Path(os.getcwd())
        if not Path(path).is_absolute:
            self.fPath = (self.cwd / path).resolve()
        else:
            self.fPath = Path(path)
        #print(f'.tex file located at {self.fPath}')
        self.allLines = []
        self.gPaths = []
        self.gPathInfo = [None, None]
        self.included = []
        self.subPaths = []
        self.inputFiles = []
        self.includeLocs = []
        self.inputLocs = []
        self.readFile()
        self.graphicList = [self.findFile(im) for im in self.included]
        self.newRelPaths = [] # For figure names outside the folder structure the .tex file is in
        self.newInputNames = [] # For input files outside the folder structure
        
        for relPath in self.subPaths:
            if self.fPath.parent not in (self.fPath / relPath).resolve().parents: # If path to graphic lies outside .tex file parent folder
                relPath = Path('.')
            self.newRelPaths.append(relPath)

        for n, (subF, subP) in enumerate(self.inputFiles):
            if self.fPath.parent not in (self.fPath / subP).resolve().parents:
                self.newInputNames.append(Path('.'))
        # print('------ \n', self.newRelPaths)
        # print(self.newInputNames)

    def readFile(self):
        '''Reads a LaTeX file in the path given on initialization, assigning class attributes
        for graphicspaths, included graphics and input files on the fly.'''

        with open(self.fPath) as f:
            for n, line in enumerate(f):
                self.allLines.append(line)
                line_naked = line.strip('\n')
                if not line_naked.startswith('%'):
                    if self.getIncluded(line_naked):
                        self.includeLocs.append(n)
                    if self.readInput(line_naked):
                        self.inputLocs.append(n)
                    self.getGraphixpaths(line_naked, n)

    def getGraphixpaths(self, l, n):
        '''Collects all paths defined by \graphicspaths into a python list'''

        if 'graphicspath' in l:
            self.gPaths = []  # Overwrites old graphicspaths to mimick LaTeX behavior
            l = l[l.find('{')+1:-1]  # Removing outer parentheses
            for path in l.split(','):
                newGraphicsPath = Path(path.strip('{} '))
                self.gPaths.append(Path(newGraphicsPath))
            self.gPathInfo[0] = n
            self.gPathInfo[1] = self.fPath

    def getIncluded(self, l):
        '''Collects names of all figures included into the document
           via \includegraphics'''
        match = self.includefinder.search(l)
        if match:
            # Extracts the filename argument, strips parentheses
            picname = self.namefinder.search(match.group()).group().strip('{}')
            self.included.append(picname)
            return True 
        else:
            return False

    def readInput(self, l):
        if l.lower().startswith('\input'):
            subPath = l[l.find('{')+1:-1]
            if not subPath.endswith('.tex'):
                subPath += '.tex'
            fullPath = self.fPath.parents[0] / subPath
            subfile = TEXfile(fullPath)
            if len(subfile.gPaths) > 0:
                self.gPaths = subfile.gPaths
                self.gPathInfo = subfile.gPathInfo
            self.included += subfile.included
            # self.allLines += subfile.allLines
            self.inputFiles.append([subfile, subPath])
            return True 
        else:
            return False

    def findFile(self, fileP):
        '''Returns a DirEntry object corresponding to the name that is input'''
        # print(self.gPaths)
        for n, Gpath in enumerate(self.gPaths):
            fileP = Path(fileP)
            fileName = fileP.stem
            subPath = fileP.parents[0]
            try:
                if not Gpath.is_absolute():
                    Gpath_abs = self.fPath.parents[0] / Gpath
                else:
                    Gpath_abs = Gpath
                Gpath_abs = Gpath_abs / subPath
                for file in os.scandir(Gpath_abs):
                    if Path(file.name).stem == fileName and file.is_file():
                        self.subPaths.append(subPath)
                        return Path(file.path)
            except FileNotFoundError:
                pass    
        print(f'Error. Figure {fileP} could not be found anywhere.')


# if sys.argv[1]:
#     fname = sys.argv[1]
# else:
#     print('First argument (filename) required')
#     exit()

fname = 'testfolder/template.tex'

if not fname.endswith('.tex'):
    fname += '.tex'

tex = TEXfile(fname)

print(
    f'\n These files are included as figures into the TeX document {fname} \n (in order of appearance): \n'


)

for g in tex.graphicList:
    print(g)
print()

def copyFile(TEX, destination):

    destination_full = (destination / TEX.fPath.name).resolve()
    print('*', destination_full)
    if not os.path.isdir(destination_full.parent):
        os.makedirs(destination_full.parent)

    with open(destination_full, 'w') as newfile:
        for n, l in enumerate(TEX.allLines):
            # Modify graphic input-statement if needed
            try:
                gNumber = TEX.includeLocs.index(n)
                gName = TEX.included[gNumber]
                replaceindex_start = l.find(gName)
                replaceindex_end = replaceindex_start + len(gName)
                l_new = l[:replaceindex_start] 
                l_new += str((TEX.newRelPaths[gNumber] / Path(gName).name)) 
                l_new += l[replaceindex_end:]
                print(l_new)
            except ValueError:
                l_new = l

            # Look for input files
            try:
                inpNumber = TEX.inputLocs.index(n)
                inpFile, inpSubPath = TEX.inputFiles[inpNumber]
                newName = TEX.newInputNames[inpNumber]
                if inpSubPath.endswith('.tex'):
                    inpSubPath = inpSubPath[:-4]
                replaceindex_start = l.find(inpSubPath)
                replaceindex_end = replaceindex_start + len(inpSubPath)
                l_new = l[:replaceindex_start] 
                l_new += str((newName / Path(inpSubPath).name)) 
                l_new += l[replaceindex_end:]
                copyFile(inpFile, destination / newName.parent)
                print(l_new)

            except ValueError:
                l_new = l

            newfile.write(l_new)


# Copies files to directory if second argument is given
try:
    # copypath = Path(sys.argv[2])
    copypath = Path('copycat')

    # Making Copy Directory
    if not os.path.isdir(copypath):
        os.mkdir(copypath)

    # Copying graphic files
    for g, relPath in zip(tex.graphicList, tex.newRelPaths):
        deepPath = copypath / 'figures' / relPath

        if not os.path.isdir(deepPath):
            os.makedirs(deepPath)
        try:
            copy2(g, deepPath)
        except TypeError:
            pass

    copyFile(tex, copypath)

    # # Copying input files
    # for ip in tex.inputFiles:
    #     print(ip)
    #     deepPath = copypath / ip
    #     if not os.path.isdir(deepPath):
    #         os.makedirs(deepPath)
    #     copy2(ip, deepPath)

    # # Copying the .tex file itself
    # copy2(tex.fPath, copypath)

except IndexError:
    pass

