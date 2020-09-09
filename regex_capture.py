#!/usr/bin/env python3
# Wed Apr 22 14:22:07 2020
# Nizar Batada nizar.batada "_at_" gmail dot com


from __future__ import print_function

'''
Usage:
cat myfile.txt | regex_capture.py -p 'gene_id=(ENSG[^;]+)' 
will return all the words with ENSG... in the first column. If there
are more than one then they would be printed as comma separated.

'''

import os,sys
from sys import argv,exit,stdin,stderr,path
import argparse
import re
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
def error(str):
    print('------\n%s\n----' % str)
    exit(-1)


def chomp(s): return s.rstrip('\n\r')

def chompsplit(s,sep='\t'): return s.rstrip('\n\r').split(sep)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='This program will grab a region defined by the user provided regular expression (the pattern within "(..)" will be returned on the 1st column')
    parser.add_argument('-f','--file',action='store', default='-',required=False,help='File name to read from. [Default: "-" (for stdin)]')
    parser.add_argument('-p','--pattern',action='store',required=True,help='Which index to restrict the search to')

    parser.add_argument('-s','--sep',default='\t',action='store',required=False,help='If lines need to be separated. This parameter will be used only if args.idx is provided. [Default: \t]')
    parser.add_argument('-i','--idx',default=None,type=int,action='store',required=False,help='Which index to restrict the search to. [Default: -i False i.e. anywhere on the line]')
    parser.add_argument('-xc','--skip_comments',action='store_true',required=False,help='Should skip lines starting with "#". Default = False ')
    parser.add_argument('-xh','--skip_header',action='store_true',required=False,help='Skip the processing (and print in the output) the first line. Default= False')
    
    args=parser.parse_args()
    # make sure that if idx is specified then so is sep
    #if (args.idx and not args.sep) or (not args.idx and args.sep):
    #    error('If args.idx is specified, so sould args.sep and vice versa')
    if args.idx:
        if args.idx <=0: 
            error ('Incorrect value for args.idx. It be 1-based')
        else:
            args.idx -= 1 # to make it 0 indexed
    if args.sep=='\\t' or args.sep=='tab':
        args.sep='\t'
    PATTERN=re.compile(args.pattern)

    if args.file=='-':
        fp=sys.stdin
    else:
        fp=open(args.file)
    header=None
    if args.skip_header: 
        header=chomp(fp.readline()) # sep
    for x in fp:
        if args.skip_comments:
            if x.startswith('#'): continue
        
        # run the search on a field or on 

        if args.idx:
            xc = chompsplit(x,sep=args.sep)
            if len(xc)==1 or args.idx >=len(xc):
                sys.stderr.write(f'[Warning] args.sep ({args.sep}) did not split the line ({chomp(x)}). Using full line.\n')
                search_str=chomp(x)
            else:
                search_str=chompsplit(x,sep=args.sep)[args.idx]
            # make sure that arg.index is <= num_fields
        else:
            search_str=chomp(x)
        match=PATTERN.findall(search_str)
        print('%s\t%s' % (';'.join(match), chomp(x)))



