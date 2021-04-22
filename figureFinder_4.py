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
        self.fPath = self.cwd / path
        #print(f'.tex file located at {self.fPath}')
        self.allLines = []
        self.gPaths = []
        self.included = []
        self.inputFiles = []
        self.readFile()
        self.graphicList = []
        print(self.included)
        self.graphicList = [self.findFile(im) for im in self.included]

    def readFile(self):
        '''Reads a LaTeX file in the path given on initialization. Returns lists
           of lines containing the preamble and body, respectively.'''
        with open(self.fPath) as f:
            for line in f:
                self.allLines += line
                line = line.strip('\n')
                if not line.startswith('%'):
                    self.getGraphixpaths(line)
                    self.getIncluded(line)
                    self.readInput(line)

    def getGraphixpaths(self, l):
        '''Collects all paths defined by \graphicspaths into a python list'''

        if 'graphicspath' in l:
            self.gPaths = []  # Overwrites old graphicspaths to mimick LaTeX behavior
            l = l[l.find('{')+1:-1]  # Removing outer parentheses
            for path in l.split(','):
                newGraphicsPath = Path(path.strip('{} '))
                self.gPaths.append(Path(newGraphicsPath))

    def getIncluded(self, l):
        '''Collects names of all figures included into the document
           via \includegraphics'''
        match = self.includefinder.search(l)
        if match:
            # Extracts the filename argument, strips the
            # parentheses and selects the text before the file extension
            picname = self.namefinder.search(match.group()).group().strip('{}').split('.')[0]
            self.included.append(picname)

    def findFile(self, fileP):
        '''Returns a DirEntry object corresponding to the name that is input'''
        for n, Gpath in enumerate(self.gPaths):
            fileP = Path(fileP)
            fileName = fileP.stem
            subPath = fileP.parents[0]
            try:
                if not Gpath.is_absolute():
                    Gpath = self.fPath.parents[0] / Gpath
                Gpath = Gpath / subPath
                print('new Path', Gpath)
                for file in os.scandir(Gpath):
                    print('file', file.path)
                    if file.name.startswith(fileName) and file.is_file():
                        print('found it!')
                        return Path(file.path)
            except FileNotFoundError:
                print('fail')
                pass

    def readInput(self, l):
        if l.lower().startswith('\input'):
            subPath = l[l.find('{')+1:-1]
            if not subPath.endswith('.tex'):
                subPath += '.tex'
            subPath = self.fPath.parents[0] / subPath
            subfile = TEXfile(subPath)
            if len(subfile.gPaths) > 0:
                self.gPaths = subfile.gPaths
            self.included += subfile.included
            self.allLines += subfile.allLines
            self.inputFiles.append(subPath)


if sys.argv[1]:
    fname = sys.argv[1]
else:
    print('First argument (filename) required')
    exit()

if not fname.endswith('.tex'):
    fname += '.tex'

tex = TEXfile(fname)

print(
    f'\n These files are included as figures into the TeX document {fname} \n (in order of appearance): \n'


)
print(tex.included)
for g in tex.graphicList:
    print(g)
print()

# Copies files to directory if second argument is given
try:
    copypath = Path(sys.argv[2])
    # Making Copy Directory
    if not os.path.isdir(copypath):
        os.mkdir(copypath)

    # Copying graphic files
    for g, relPath in zip(tex.graphicList, tex.included):
        deepPath = copypath / relPath
        if not os.path.isdir(deepPath):
            os.makedirs(deepPath)
        copy2(g, deepPath)

    # Copying input files
    for ip in tex.inputFiles:
        print(ip)
        deepPath = copypath / ip
        if not os.path.isdir(deepPath):
            os.makedirs(deepPath)
        copy2(ip, deepPath)

    # Copying the .tex file itself
    copy2(tex.fPath.fullPath, copypath)
except IndexError:
    pass
