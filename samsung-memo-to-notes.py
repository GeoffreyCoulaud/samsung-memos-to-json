#!/bin/python3

from glob import glob
from os import path, mkdir
from zipfile import ZipFile
from datetime import datetime
from shutil import rmtree
from math import floor
from bs4 import BeautifulSoup
from tempfile import mkdtemp
import xml.etree.ElementTree as ET
import sys
import json
import time
import argparse

noteDict = {
	"type": 0,
	"title": "",
	"content": "",
	"metadata": "{\"type\":\"blank\"}",
	"added": "2022-01-16T14:36:51.283Z",
	"modified": "2022-01-16T14:37:11.871Z",
	"status": 0,
	"pinned": 1
}

def memoXmlToNote(tree, fallbackTitle):
	
	# Text contents
	textElem = tree.find("./contents/content")
	if (textElem is None): 
		print("\t[WARN] No text contents, using placeholder")
		text = ""
	else: 
		text = textElem.text
	soup = BeautifulSoup(text, features="lxml")
	text = soup.get_text("\n").replace("\n", "\n\n")
	
	# Title
	titleElem = tree.find("./header/meta[@title]")
	if (titleElem is None):
		print("\t[WARN] No title elem, using placeholder")
		title = None
	else: 
		title = titleElem.get("title", None)
	if title is None == "":
		title = fallbackTitle
	
	# Creation time
	createdElem = tree.find("./header/meta[@createdTime]")
	if (createdElem is None): 
		print("\t[WARN] No creation date, using now")
		created = datetime.now()
	else :
		createdTimestamp = createdElem.get("createdTime", None)
		if (createdTimestamp is None):
			print("\t[WARN] Creation date is none, using now")
			createdTimestamp = time.time()
		else:
			createdTimestamp = floor(int(createdTimestamp) / 1000)
	created = datetime.fromtimestamp(createdTimestamp)
	createdMs = format(floor(created.microsecond / 1000), "0>3d")
	created = created.strftime("%Y-%m-%dT%H:%M:%S.") + createdMs + "Z"

	# Modification time
	modified = datetime.now()
	modifiedMs = format(floor(modified.microsecond / 1000), "0>3d")
	modified = modified.strftime("%Y-%m-%dT%H:%M:%S.") + modifiedMs + "Z"

	# Create json note
	note = noteDict.copy()
	note.update({
		"title": title,
		"content": text,
		"added": created,
		"modified": modified
	})

	return note

def convert(inDir, outFile, fallbackTitle="No title"):

	# Get memo paths
	print("Reading memos dir")
	memoGlob = path.join(inDir,"*.memo")
	memoPaths = glob(memoGlob)

	# Create extractDir
	extractDir = mkdtemp()

	# Convert memos
	print("Converting memos to notes")
	notes = []
	for memoPath in memoPaths:

		(basename, ext) = path.splitext(path.basename(memoPath))
		print(f"Memo \"{basename}\"")
		
		# Extract zip
		print("* Extracting")
		memoExtractDir = path.join(extractDir, basename)
		mkdir(memoExtractDir)
		z = ZipFile(memoPath)
		z.extractall(memoExtractDir)
		
		# Get note data
		print("* Parsing")
		xmlPath = path.join(memoExtractDir, "memo_content.xml")
		tree = ET.parse(xmlPath)
		
		# Remove extract dir
		rmtree(memoExtractDir)

		# Create note
		print("* Creating note")
		note = memoXmlToNote(tree, fallbackTitle)
		notes.append(note)

		print("* Done")

	# Remove outdir
	rmtree(extractDir)

	# Build final dict
	final = {
		"version": 4,
		"notes": {}
	}
	print("Exporting notes as JSON")
	for i, value in enumerate(notes):
		final["notes"][str(i)] = value

	# Export as JSON
	with open(outFile, "w") as f:
		json.dump(final, f, indent="\t")
	print("Done")

def main():
	
	# Handle arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("input", help="Directory where your memos are stored")
	parser.add_argument("output", help="Destination file for your JSON backup")
	parser.add_argument("-f", "--fallbackTitle", default="No title", help="Title used when none is found for a memo")
	args = parser.parse_args()
	
	# Convert
	convert(
		args.input, 
		args.output, 
		args.fallbackTitle
	)

# ------------------------------------------------------------------------------

if __name__ == '__main__':
	main()