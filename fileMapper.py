import re
# import os
import sys
import glob


sys.setrecursionlimit(10**6)

# going to go through every file in ABSOLUTE DIRECTORY that matches:
	# *.hpp
	# *.h
	# *.cpp
	# *.c
	# *.cc

# in each file just grab the includes

# myPath = input("Input the direct path\n")

ERROR_ENUM = {
	"ERROR: RECURSIVE INCLUSION":-1,
	"ERROR: FILE NOT FOUND":-2
}

sourceFiles = []
headerFiles = []
files = []

filePatterns = ["*.hpp","*.h","*.cpp","*.c","*.cc","*.ipp"] # some weird include format

# "/home/matt/Desktop/Work/UHD/uhd/"
dirPath = "/home/matt/Desktop/Work/UHD/uhd/"

for filePattern in filePatterns:
	# print("{}: {}".format(loop,len(glob.glob(dirPath+"**/"+filePattern,recursive=True))))
	files.extend(glob.glob(dirPath+"**/"+filePattern,recursive=True))
	if("*.h" in filePattern or filePattern == "*.ipp"):
		headerFiles.extend(glob.glob(dirPath+"**/"+filePattern,recursive=True))
	else:
		sourceFiles.extend(glob.glob(dirPath+"**/"+filePattern,recursive=True))

# print(headerFiles)
# for file in headerFiles:
# 	if("mpm/exception.hpp" in file):
# 		print(file)

outputStructure = {} # file : {include0 : {include0_0 : {}, include0_1 : {..},..}, include1 : {...},...}

# includePattern = "#\s*include\s+(\".+\"|<.+>)"
includePattern = "#\s*include\s+(\".+\..+\"|<.+\..+>)"
relPathPattern = "(?<=\.\.\/)(?=\w).*$" # after finding a #include <> or "", there may be a string of /../../'s, want to remove all of them
											# also, if found, remove the / as well since we add it anyway

# safetyCheck represents parent path of recursion, used to prevent forever loops in checking
def recursiveSearch(fileIn,safetyCheck=None):
	# print(fileIn)
	global includePattern
	global ERROR_ENUM
	retDict = {}
	if(not safetyCheck): # entry vector
		safetyCheck = [fileIn]
	else:
		if(fileIn in safetyCheck):
			retDict[fileIn] = ERROR_ENUM["ERROR: RECURSIVE INCLUSION"]
			# print("RECURSIVE INCLUSION")
			# sys.exit(0)
			return retDict
			# the included fileIn is already in parent dictionary path!
		else:
			safetyCheck.append(fileIn)
	with open(fileIn,'r') as file:
		# print("recursiveSearch fileIn:\n{}\n".format(fileIn))
		lines = file.readlines()
	for line in lines:
		M = re.findall(includePattern,line)
		if(M): # found the #includ stuff
			# print(line)
			for match in M:
				relM = re.findall(relPathPattern,match)
				if(relM):
					match = relM[0][:-1]
				else:
					match = match[1:-1]
				if(len(relM)>1):
					print("FATAL ERROR")
					sys.exit(0)
				retDict[match] = ERROR_ENUM["ERROR: FILE NOT FOUND"]
				foundFlag = False
				for fileCheck in headerFiles:
					# prepend '/' so that files like boost/config doesn't include config
					if("/"+match in fileCheck): # lets look for the match once..
						try:
							retDict.pop(match) # found file, so error no longer valid
						except:
							if(match == "stdint.h"):
								# print("wtf\n{}\n{}".format(retDict,match))
								sys.exit(0)
						foundFlag = True
						retDict[fileCheck] = recursiveSearch(fileCheck,safetyCheck)
						break # only looking for match once.. for now
				if(not foundFlag):
					if(match == "ns.h"):
						sys.exit(0)
		# M = re.search()
	return retDict

# attack vector for recursion is the source files

loop = 0
for sourceFile in sourceFiles:
	loop += 1
	print("({}/{}) checking sourcefile: {}".format(loop,len(sourceFiles),sourceFile))
	outputStructure[sourceFile] = {} # recursive
	# associating sourceFile with a nested number of header files
	# header files will have relative pathings... so will need to resolve these relative paths
	with open(sourceFile,'r') as file: # read only
		lines = file.readlines()
		# do regex pattern search
	for line in lines:
		M = re.findall(includePattern,line) # not including STL includes ie #include <memory>
		if(M):
			for match in M: # in case there's multiple includes in one line (C/C++ use whitespace, including \n's, as separation between tokens)
				# print(match[1:-1])
				relM = re.findall(relPathPattern,match)
				if(relM):
					match = relM[0][:-1]
				else:
					match = match[1:-1]
				if(len(relM)>1):
					print("FATAL ERROR")
					sys.exit(0)
				outputStructure[sourceFile][match] = ERROR_ENUM["ERROR: FILE NOT FOUND"]
				# what happens if a pattern matches but the file isn't found?
				foundFlag = False
				for fileCheck in headerFiles:
					# make sure it's prepended by a directory!
					if("/"+match in fileCheck):
						try:
							outputStructure[sourceFile].pop(match) # found the file, so this dict element is no longer valid
						except:
							if(match == "stdio.h"):
								# print("ERROR")
								# print("{}\n{}\n".format(outputStructure[sourceFile].keys(),match))
								sys.exit(0)
						outputStructure[sourceFile][fileCheck] = recursiveSearch(fileCheck) # returns a dictionary'
						# break # ??? Should there only be one copied version per?
						# break and check first recursion
				# if(not foundFlag):
				# 	if(match[1:-1])

import nested_lookup
import networkx as nx
import matplotlib.pyplot as plt
# nested_lookup might not be it chief

# alter keys:
def keyCallback(key):
	if("/home/matt/Desktop/Work/UHD/" in key):
		return key[28:]
	else:
		return key # remove the /home/matt/Desktop/Work/UHD/ --> look for uhd/

def recursiveCallback(dictIn):
	dictOut = {}

	for key in dictIn:
		if(type(dictIn[key]) == dict):
			dictOut[keyCallback(key)] = recursiveCallback(dictIn[key])
		else:
			# change the key to uhd/ relative path
			dictOut[keyCallback(key)] = dictIn[key]

	return dictOut

# def recursiveCallback():
# 	return retDict;

# set(nested_lookup.get_all_keys(outputStructure)) --> only gets unique set of keys

# unique keys > number of files in our list
def uniquify(allFiles,setIn):
	out = setIn.copy()
	for x in allFiles:
		if x in uniqueKeys:
			out.remove(x)
	return out

def recursiveFilterNodes(dictIn):
	dictOut = {}
	queryList = list(dictIn.items())
	for pair in queryList:
		if(type(pair[1]) != dict):
			dictOut[pair[0]] = {} # make the -1, -2 value key pairs become a key : {} pair
		else: # this is 
			dictOut[pair[0]] = recursiveFilterNodes(dictIn[pair[0]]) # this inputs the key : DICT value for key pair[0]
	return dictOut

electricBoogalu = recursiveCallback(outputStructure)
# every key is filtered for uniqueness ( a set )
uniqueKeys = list(set(nested_lookup.get_all_keys(electricBoogalu)))

# Just want to be stuck with the list of unique header keys
# will also include header files that arent found
sF = []
for x in sourceFiles:
	sF.append(x[28:])
queryKeys = uniquify(sF,uniqueKeys)
# --> want to get the total number of header nodes to look at 

# get_occurrences_and_values returns a data type like:
# {"occurrences":# of times,"values":{}} --> everything inside is values

# terminal node, just like {} nodes (empty nodes)
notFound = nested_lookup.get_occurrences_and_values([electricBoogalu],value=ERROR_ENUM["ERROR: FILE NOT FOUND"])

# recursive includes will have an edge going back up!... eh
# for now recursive includes will just be removed from the set --> need to remove everything that has the value recursive inclusion
recursiveInclude = nested_lookup.get_occurrences_and_values([electricBoogalu],value=ERROR_ENUM["ERROR: RECURSIVE INCLUSION"])

# everything ends with {} now
filteredStructure = recursiveFilterNodes(electricBoogalu)

# i think at some point I want to switch terminating from {} to None or 0..
	# otherwise, nested_lookup.get_occurrences_and_values won't be useful!

# same layered NODES -- unconnected
# calling layer NODE -- connected to each nested node below

def NXFormat(parentNode,childNodes):
	return [(parentNode,x) for x in childNodes]

def recursiveNX(dictIn,nxGraph):
	# return a list of nodes
	childNodes = []
	for key in dictIn:
		childNodes.append(key) # every key is a node in this layer
		if(dictIn[key]): # more children node layers
			# connect all of the children nodes to this node that owns them
			nxGraph.add_edges_from(
				NXFormat(
					parentNode  = key,
					childNodes  = recursiveNX( # Recursion --------------
						dictIn  = dictIn[key],
						nxGraph = nxGraph
						)
					)
				)
		else: # empty dictionary --> terminating node
			pass # already appended this node, don't need to worry about children nodes
	return childNodes # returns the list of this layer's nodes

nxList = []

for entryVec in sF: # every source file
	G = nx.Graph()
	# dont need to add nodes, can just add edges as a list of tuples:
		# each tuple simply connects 2 nodes
	G.add_edges_from(
		NXFormat(
			parentNode  = entryVec,
			childNodes  = recursiveNX(
				dictIn  = filteredStructure[entryVec],
				nxGraph = G
				) # recursiveNX returns a list of child nodes
			) # returns a list of tuple pairs (parent node, childNode[n])
		) # connects everything to the main source/parent node
	nxList.append(G)

for graph in nxList:
	nx.draw(graph)
	plt.draw()
	plt.show()
	break # there will be hundreds of these, will add a way to store png's but for now just break after 1

# nodes --> dots
# edges --> connections

# when recursive returns, draw edge from calling node to list of returning nodes
# entry vector of 760 nodes (source files)
# simplest case:
