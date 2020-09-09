#
These are scripts I use often when working in the terminal often for 
data frames (tab/comma delimited text files).
Use it as you would awk sed and grep and other command line tools
with pipe

Note that majority of these scripts will work only with python3 and 
require pandas library

# INSTALL
* create a bin file (`mkdir ~/bin`) and add these scripts in that folder
* add this folder to the path in your .bashrc (i.e. `export PATH=$PATH:~/bin`)

| Script name | Description |
| --- | --- |
| `field_merge.py` | To merge *any* two columns in a file |
| `field_move.py` | To move column order|
| `transpose.py`  | To transpose a data matrix (i.e. move columns to rows) |
| `join_files.py` | Merge rows of arbitrary number of files. Keys is expected to be in the first column. In the current version only a single (user specified) column can be used |
| `regex_capture.py | To capture arbitrary regular expressions from each line. String to be captured must be in "(..)" within the pattern. The captured word will be put in the first column. If more than one string matches the pattern, they will be joined by ";" |


