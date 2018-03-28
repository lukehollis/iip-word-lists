#!/usr/bin/env python3

import os
import sys
from collections import OrderedDict
from lxml import etree
from copy import copy
import glob
import argparse

DEBUG = True 
ns = "{http://www.tei-c.org/ns/1.0}"
xmlNs = "{http://www.w3.org/XML/1998/namespace}"

ignore = ['(', '?', ')', ',', ';', '.', ':', '"', "'", "<", ">", "+", "[", "]", "∙", "_"]
include_trailing_linebreak = [ns + "expan", ns + "choice", ns + "hi", ns + "supplied", ns + "num", ns + "div"]

output_name = "wordlist"

class iip_word:
	equivilence = ["edition_type", "language", "text", "file_name"]
	def __init__(self, edition_type, language,  text, file_name, contains_gap=False):
		# eg: diplomatic
		self.edition_type = edition_type
		# eg: grc
		self.language = language
		# eg: Πἁποϲ
		self.text = text
		# eg: jeru00001.xml
		self.file_name = file_name
		
		self.contains_gap = contains_gap
	def __hash__(self):
		new_hash = 0
		for e in iip_word.equivilence:
			new_hash += hash(getattr(self, e))
		return new_hash
	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return hash(self) == hash(other)
		else:
			return False
	def __ne__(self, other):
		return not self.__eq__(other)
	def print(self):
		print(self.text + " | " + self.language + " | " + self.edition_type + " | " + self.file_name)

def word_list_to_csv(full_list):
	if os.path.isfile(output_name + '.csv'):
		os.remove(output_name + '.csv')
	if os.path.isdir(output_name + '.csv'):
		sys.stderr.write(output_name + '.csv is a directory.')
		return
	output_file = open(output_name + ".csv", "a")
	for word in full_list:
		output_file.write(word.text + ", " + word.language + ", " + word.edition_type + ", " + word.file_name + "\n")

def word_list_to_html(full_list, num=0):	
	word_list = full_list[0:1000]
	next_list = full_list[1000:len(full_list)]
	html = etree.Element("html")
	head = etree.Element("head")
	title = etree.Element("title")
	title.text = "Word List"
	style_link = etree.Element("link")
	style_link.attrib["rel"] = "stylesheet"
	style_link.attrib["type"] = "text/css"
	style_link.attrib["href"] = "wordlist.css"
	body = etree.Element("body")
	table = etree.Element("table")
	body.append(table)
	head.append(title)
	head.append(style_link)
	html.append(head)
	html.append(body)
	table_header = etree.Element("tr")
	table_header_word = etree.Element("th")
	table_header_word.text = "Word"
	table_header_language = etree.Element("th")
	table_header_language.text = "Language"
	table_header_edition = etree.Element("th")
	table_header_edition.text = "Edition"
	table_header_file = etree.Element("th")
	table_header_file.text = "File"
	table_header.append(table_header_word)
	table_header.append(table_header_language)
	table_header.append(table_header_edition)
	table_header.append(table_header_file)
	table.append(table_header)
	for word in word_list:
		row = etree.Element("tr")
		text = etree.Element("td")
		text.text = (word.text)
		language = etree.Element("td")
		language.text = (word.language)
		edition_type = etree.Element("td")
		edition_type.text = (word.edition_type)
		file_name = etree.Element("td")
		file_name_link = etree.Element("a")
		file_name_link.text = (word.file_name)
		file_name_link.attrib["href"] = word.file_name
		file_name.append(file_name_link)
		row.append(text)
		row.append(language)
		row.append(edition_type)
		row.append(file_name)
		table.append(row)
	if num > 0:
		prev_link = etree.Element("a")
		prev_link.text = "Previous Page"
		prev_link.attrib["href"] = output_name + "-" + str(num - 1) + ".html"
		body.append(prev_link)
	if len(next_list) > 0:
		next_link = etree.Element("a")
		next_link.text = "Next Page"
		next_link.attrib["href"] = output_name + "-" + str(num + 1) + ".html"
		body.append(next_link)
	output_file = open(output_name + "-" + str(num) + ".html", "w")
	output_file.write(etree.tostring(html, pretty_print=True).decode())
	output_file.close()
	style_file = open("wordlist.css", "w")
	style_file.write("""
		table {
			border-collapse: collapse;
		}
		th {
			background-color: black;
			color: white;
			text-align: left;
			border: 1px solid black;
		}
		th, td {
			padding: 3px;
			padding-right: 3ch;
		}
		td {
			border: 1px solid grey;
		}
	""")
	style_file.close()
	if (len(next_list) > 0):
		word_list_to_table(next_list, num + 1)

def whitespace_to_space(text):
	if text == None or len(text) < 1:
		return ""
	return " ".join(text.split())

def word_list_to_str_list(word_list):
	str_list = ""
	for e in word_list:
		str_list += e.text + " "
	return str_list

# Begin a new word as the supplied word. Will often be blank, such that
# future characters will be added.
def append_to_word_list(word_list, word):
	word_list.append(word)

# Add to the supplied word list text that is either within a tag and 
# preceding all child elements or following a tag but before any sibling
# elements. In lxml terms, element.text() and element.tail()
def add_trailing_text(word_list, trailing_text, edition_type, lang, path, include_initial_line_break):
	trailing_text_list = trailing_text.split() 
	if len(word_list) == 0 or trailing_text[0] == ' ' or (trailing_text[0] == '\n' and include_initial_line_break):
		if word_list[-1].text != "":
			append_to_word_list(word_list, iip_word(edition_type, lang, "", path))
	if len(trailing_text_list) < 1:
		return
	word_list[-1].text += trailing_text_list[0]
	if len(word_list) > 1:
		for i in range(1, len(trailing_text_list)):
			new_word = iip_word(edition_type, lang, trailing_text_list[i], path)
			append_to_word_list(word_list, new_word)
	if (trailing_text[-1] == ' ' or trailing_text[-1] == '\n'):
		if word_list[-1].text != "":
			append_to_word_list(word_list, iip_word(edition_type, lang, "", path))
	
def add_element_to_word_list(e, new_words, edition, mainLang, path):	
	# Get the language of the element
	editionLang = mainLang
	if (xmlNs+'lang' in edition.keys()):
		editionLang = edition.attrib[xmlNs+'lang']
	wordLang = editionLang
	
	# The last word in the list _at the time of calling the function_.
	prev_word = copy(new_words[-1])
	
	if e.tag == ns + "gap":
		new_words[-1].contains_gap = True
	
	# Start a new word if the tag is a linebreak without break="no"
	if e.tag == ns + "lb" and not ('break' in e.attrib and e.attrib['break'] == "no"):
		append_to_word_list(new_words, iip_word(edition.attrib['subtype'], editionLang, "", path))
	
	# Add the text within the elemnt not inside any child element
	if (e.text != None):
		add_trailing_text(new_words, e.text, edition.attrib['subtype'], wordLang, path, True)
	
	# Add each child element
	children = e.getchildren()
	for i in range(0, len(children)):
		# When adding children of a <choice> element, the preceding word
		# is added between children so that each possible version of the
		# word will appear in the final word list.
		if (e.tag == ns + "choice" and i > 0):
			append_to_word_list(new_words, prev_word)
		add_element_to_word_list(children[i], new_words, edition, mainLang, path)
	
	# Add the words following the element which are not in any sibling
	if (e.tail != None):
		add_trailing_text(new_words, e.tail, edition.attrib['subtype'], wordLang, path, (e.tag in include_trailing_linebreak))

def get_words_from_file(path):
	root = etree.parse(path).getroot()
	words = []
	nsmap = {'tei': "http://www.tei-c.org/ns/1.0"}
	bodies = root.findall('.//' + ns + 'body')
	textLang = root.find('.//' + ns + 'textLang')
	mainLang = ""
	if (textLang != None):
		mainLang = textLang.attrib['mainLang']
	for edition in root.findall(".//tei:div[@type='edition']", namespaces=nsmap): 	
		new_words = [iip_word(edition.attrib['subtype'], mainLang, "", path)]
		add_element_to_word_list(edition, new_words, edition, mainLang, path)
		words += new_words	
	null_words = []
	for word in words:
		word.text = str(word.text)
		for pattern in ignore:
			word.text = word.text.replace(pattern, "")
		if (len(word.text) < 1 or word.text == "" or word.text == '\n' or word.text == '\t' or word.text.isspace()):
			null_words.append(word)	
	words = [x for x in words if x not in null_words]
	return words

def print_usage():
	print("wordlist.py [file1] [file2] ... \n"
		   + "\t Create a list of words from the specified files")

def print_debug(string):
	if (DEBUG):
		print(string)

def flatten_list(word_list):
	flat_list = []
	for word in word_list:
		flat_list.append(word.text)
	return flat_list

def remove_duplicates(items):
	return list(OrderedDict.fromkeys(items))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Produce word list from files.')
	parser.add_argument('files', type=str, nargs='+', help='The epidoc xml files to process')
	parser.add_argument("--html", help="Output list as html file(s)", action="store_true")
	parser.add_argument("--csv", help="Output list as csv file", action="store_true")
	parser.add_argument("--silent", help="Don't print the word list to the console", action="store_true")
	parser.add_argument("--duplicates", help="Include each instance of every word in the word list", action="store_true")
	parser.add_argument("--alphabetical", help="Sort the list alphabetically", action="store_true")
	parser.add_argument("--fileexception", help="Print exceptions for files which could not be read", action="store_true")
	args = parser.parse_args()

	words = []

	# Extract words from each file 
	for file in args.files: #sys.argv[1:len(sys.argv)]:
		if args.fileexception:
			words += get_words_from_file(file)
		else:
			try:
				words += get_words_from_file(file)
			except:
				sys.stderr.write("Cannot read " + file + "\n")

	if not args.duplicates:
		words = remove_duplicates(words)

	if args.alphabetical:
		words = sorted(words, key=lambda word: word.text)

	# Print each extracted word on a new line
	if not args.silent:
		for word in words:		
			word.print()
	# Output words to files
	if args.html:
		word_list_to_html(words)
	if args.csv:
		word_list_to_csv(words)
	sys.exit(0)


