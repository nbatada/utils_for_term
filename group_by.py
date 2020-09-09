#!/usr/bin/env python3
# Thu May 21 20:53:49 2020
# Nizar Batada 

'''
Input:
a1 b1
a1 b2
a2 b3
a2 b4

Output:
a1 b1;b2
a2 b3;b4

'''
from __future__ import print_function

import os,sys
from sys import argv,exit,stdin,stderr,path
import argparse
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
def error(str):
    print('------\n%s\n----' % str)
    exit(-1)


def chomp(s): return s.rstrip('\n\r')

def chompsplit(s): return s.rstrip('\n\r').split('\t')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='This program will collapse rows by string in the first column.')
    parser.add_argument('-f','--file',default='-',action='store',required=False,help='File name to read from')
    parser.add_argument('-d','--keep_duplicates',action='store_true',required=False,help='Whether duplicates shold be retained')
    parser.add_argument('-H','--header',action='store_true',required=False,help='Whether to ignore the header')
    args=parser.parse_args()
    if args.file=='-':
        fp=sys.stdin
    else:
        fp=open(args.file)
    d={}
    if args.header:
        header=fp.readline()
        print(chomp(header))
    for x in fp:
        xc=chompsplit(x)
        k=xc[0]
        v=','.join(xc[1:])
        if args.keep_duplicates:
            d.setdefault(k,[]).append(v)
        else:
            d.setdefault(k,set()).add(v) # will get rid of duplicates
    for k in d:
        val = d[k]
        n = len(val)
        val = ';'.join(val)
        print(f'{k}\t{n}\t{val}')
        
