#!/usr/bin/python
# updated (corrected) it on 10 March 2020
# Sun Aug 16 20:49:58 2015 has a bug
from __future__ import print_function # this is for print of v3 in v2.7
import os,sys
from sys import argv,exit,stdin,stderr,path
import argparse

def error(str):
    print('------\n%s\n----' % str, file=stderr, end="\n")
    exit(-1)
    
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='This program ...')
    parser.add_argument('-f','--file',default=None,action='store',nargs=1,required=False,help='File name to read from')
    parser.add_argument('-i','--idx_from',type=int,required=True,help='index of the column to move')
    parser.add_argument('-j','--idx_to',type=int,required=True,help='index of the column to move to')
    args=parser.parse_args()
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
