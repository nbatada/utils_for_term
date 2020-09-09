
# Description
Bunch of scripts that I use most often when working in the terminal.  

Use it as you would awk sed and grep and other command line tools
with pipes

Note that majority of these scripts will work only with `python3` and 
require `pandas` library


| Script name | Description |
| --- | --- |
| `field_merge.py` | To merge *any* two columns in a file |
| `field_move.py` | To move a single column |
| `transpose.py`  | To transpose a data matrix (i.e. move columns to rows) |
| `join_files.py` | Merge rows of arbitrary number of files. Keys is expected to be in the first column. In the current version only a single (user specified) column can be used |
| `regex_capture.py` | To capture arbitrary regular expressions from each line. String to be captured must be in "(..)" within the pattern. The captured word will be put in the first column. If more than one string matches the pattern, they will be joined by ";" |

# Usage
Each script takes a "-h" argument and will print the list of accepted arguments.
For example, `join_files.py -h` will print the following
```
$ join_files.py -h
usage: join_files.py [-h] -f [FILES [FILES ...]] [-s SEP_IN_FILENAME]
                     [-j IDX_TO_KEEP] [-i IGNORE_KEYS_PREFIX]
                     [-k FILENAME_KEYS] [-m MISSING_VALUE]

Will join tables with identical keys (first column). Works similar to join but
works for abitrary number of files, supports filtering and limited support for
filename (column name) processing. Limitation: input files must have only 2
columns (column 1 have keys and column 2 have values).

optional arguments:
  -h, --help            show this help message and exit
  -f [FILES [FILES ...]], --files [FILES [FILES ...]]
                        [Required] File name to read from
  -s SEP_IN_FILENAME, --sep_in_filename SEP_IN_FILENAME
                        [Optional. Default=None] Separator in the file name to
                        split the sample name [first element] from other parts
                        of the file.
  -j IDX_TO_KEEP, --idx_to_keep IDX_TO_KEEP
                        [Optional. Default=2 (1-indexed)] If the files have
                        more than one column, indicate which column to take
                        (note: if the file has more than 2 columns and this
                        argument is not specified, join will fail.
  -i IGNORE_KEYS_PREFIX, --ignore_keys_prefix IGNORE_KEYS_PREFIX
                        [Optional] Ignore keys (1st column) if they start with
                        the specified prefix
  -k FILENAME_KEYS, --filename_keys FILENAME_KEYS
                        [Optional] A file containing a list of keys (rows) to
                        retain. Provide the keyname one per line.
  -m MISSING_VALUE, --missing_value MISSING_VALUE
                        [Optional] String to represent missing value
```

# Installation
* create a bin file (`mkdir ~/bin`) and add these scripts in that folder
* add this folder to the path in your .bashrc (i.e. `export PATH=$PATH:~/bin`)

