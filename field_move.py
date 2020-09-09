#!/usr/bin/python
#  10 March 2020
# Nizar Batada nizar.batada "_at_" gmail.com

from __future__ import print_function # this is for print of v3 in v2.7

'''
USAGE:
To move column 1 to column 4, do

cat myfile.tsv | field_move.py -i 1 -j 4


'''
import os,sys
from sys import argv,exit,stdin,stderr,path
import argparse

def error(str):
    print('------\n%s\n----' % str, file=stderr, end="\n")
    exit(-1)
    
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='This program allows you to move around specific columns in a tab delimited file')
    parser.add_argument('-f','--file',default=None,action='store',nargs=1,required=False,help='File name to read from [Default: stdin]')
    parser.add_argument('-i','--idx_from',type=int,required=True,help='index of the column to move. 1-based index.')
    parser.add_argument('-j','--idx_to',type=int,required=True,help='index of the column to move to'. 1-based index.)
    parser.add_argumen('-s','--sep',default='\t',action='store',required=False, help='delimiter separating columns [Default: \t]')
    args=parser.parse_args()
    if args.sep=='\\t' or args.sep=='tab':
        sep='\t'
    if args.idx_from <=0 or args.idx_to<=0:
        error("Error: idx_from and idx_to must be greater than 0.")
    src=args.idx_from
    dest=args.idx_to
    if src==dest:
        error("Error: idx_from and idx_to must be different")
    if args.file==None:
        fp=sys.stdin
    FIRSTLINE=True
    for x in fp:
        v=x.rstrip('\n\r').split(sep)
        v.insert(0,'0')          # so can use the 1-based indexing        
        
        if FIRSTLINE:
            FIRSTLINE=False
            if args.idx_from >len(v) or args.idx_to >len(v):
                # note: this is len after adding empty value to the first index
                error ("idx_from and idx_to must be no greater than the number of fields (%s)" % len(v))

        if src < dest:
            temp=v.pop(src)
            v.insert(dest,temp)
        elif src > dest:
            temp=v.pop(src)
            v.insert(dest,temp)
        print("%s" % sep.join(v[1:]))
