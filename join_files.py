#!/usr/bin/env python3
# Nizar Batada nizar.batada "-at-" gmail dot com
# Tue Mar 17, 6pm. Allow filtering rows with certain prefixes (eg. __ambigous __too_low_aQual) that ht-seq will spit out
# Tue Feb 11 21:32:06 2020
# Mon May 4, Update: fix the column labeling issue (when input has more than two columns per file (need to take one usecols)

info='''Will join tables with identical keys (first column). 
Works similar to join but works for abitrary number of files, supports 
filtering and limited support for filename (column name) processing.

Limitation: input files must have only 2 columns (column 1 have keys and column 2 have values).


'''

import pandas as pd
import os,sys
from sys import argv,exit,stdin,stderr,path
import argparse
from progressbar import ProgressBar
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
def error(str):
    print('------\n%s\n----' % str) # , file=stderr,end='\n')
    exit(-1)


def chomp(s): return s.rstrip('\n\r')

def chompsplit(s): return s.rstrip('\n\r').split('\t')

def cleanup_filenames(files,sep=None):
    '''
    filenames often have sample names along with additional information (like barcode, or read 1 etc). 
    And in joining the file, we simply want to keep the sample name.
    Here, I assume that the different fields are separated by <sep> and that the prefix
    is the sample name

    ./path/to/samplename_field1.field2.field3.tsv

    it will return "samplename_field1

    (operation is dirname and then basename)

    '''
    if sep:
        return([f.split('/')[-1].split(sep)[0] for f in files])
    else:
        return(files)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=info)
    parser.add_argument('-f','--files', default=['-'],nargs='*',action='store',required=True,help='[Required] File name to read from')
    parser.add_argument('-s','--sep_in_filename',default=None,action='store',required=False,help='[Optional. Default=None] Separator in the file name to split the sample name [first element] from other parts of the file.')
    parser.add_argument('-j','--idx_to_keep',default=2,action='store',type=int,required=False,help='[Optional. Default=2 (1-indexed)] If the files have more than one column, indicate which column to take (note: if the file has more than 2 columns and this argument is not specified, join will fail.')
    parser.add_argument('-i','--ignore_keys_prefix',default=None,action='store',required=False,help='[Optional] Ignore keys (1st column) if they start with the specified prefix')
    parser.add_argument('-k','--filename_keys',default=None, action='store',required=False,help='[Optional] A file containing a list of keys (rows) to retain. Provide the keyname one per line.')
    parser.add_argument('-m','--missing_value',default='', action='store',required=False, help='[Optional] String to represent missing value')
    parser.add_argument('-wd','--working_directory',default='.',action='store',required=False, help='[Optional] Specify in which directory the files are in')
    parser.add_argument('-n','--file_name_as_header',action='store_true',required=False, help='[Optional][Default:False] Use file names as header rather than the header in the file. Note that if file_name_as_header=False, then first line will be taken as a header.')
    
    args=parser.parse_args()
    args.idx_to_keep -= 1 # make it 0-indexed
    if args.files==['-']: # Note: nargs='*' variable is a list
        all_files=[f.rstrip() for f in stdin.readlines()]
    else:
        all_files=args.files

    if args.working_directory != '.': # append the working directory
        args.working_directory=args.working_directory.rstrip('/')
        all_files=[f'{args.working_directory}/{f}' for f in all_files]
        
    #print('\n'.join(all_files))
    all_files_L=[]
    import glob
    for f in all_files:
        all_files_L.extend(glob.glob(f))

    # insure that all files exist # but after glob        
    import os    
    for f in all_files_L:
        if not os.path.isfile(f) :
            error(f'File {f} does not exist.')

    all_files=all_files_L

    HEADER=0
    if args.file_name_as_header:
        HEADER=None

    try:
        df_from_each_file=[]
        pbar=ProgressBar()
        
        for f in pbar(all_files):
            # header from file if the user specifies it or default it is the file name

            df_from_each_file.append(pd.read_csv(f, index_col=0, sep='\t', header=HEADER, usecols=[0,args.idx_to_keep]))
        #df_from_each_file=(pd.read_csv(f,index_col=0,sep='\t',header=None, usecols=[0,args.idx_to_keep]) for f in all_files)
    except ValueError:
        error('Error during file reading: check if the args.idx_to_keep is correct')

    df = pd.concat(df_from_each_file,axis=1, sort=False).fillna( args.missing_value ) ## join="inner" 
    # axis = 0 (column down/down) and axis=1 (row/right)

    if args.file_name_as_header:
        column_names=cleanup_filenames(all_files,args.sep_in_filename) # file names will be used for column headers (but only works if there is one column per file)
        df.columns=column_names # filename is used as column name. Note: this will fail if there is more than one column

    ##nrows=df.count(axis=0) # row count

    # filter the rows
    if args.filename_keys:
        rownames=[k for k in df.index]
        rownames_to_keep=[line.strip() for line in open(args.filename_keys).readlines()]
        remove_these=set(rownames)-set(rownames_to_keep)
        df.drop(index=remove_these, inplace=True)

    if args.ignore_keys_prefix:
        df = df[df.index.startswith(args.ignore_keys_prefix)==False]
        # find all keys that starts with this prefix
        ## rownames_to_discard=[]
        ## for rowname in df.index:
        ##    if rowname.startswith(args.ignore_keys_prefix):
        ##        rownames_to_discard.append(rowname)
        ## if len(rownames_to_discard)>0:
        ##    df.drop(index=rownames_to_discard, inplace=True)
    ##nrows_after=df.count(axis=0)

    df.index.name="ID" # set the header name of the rownames     
    df.sort_index(inplace=True) # sort by rownames
    df.to_csv(sys.stdout, sep='\t',index=True) 
    
    
    

