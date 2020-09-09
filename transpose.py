#!/usr/bin/env python

info='''transposes data frame

USAGE: cat $file | transpose.py 
'''

import pandas as pd
import os,sys
from sys import argv,exit,stdin,stderr,path
import argparse
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
def error(str):
    print('------\n%s\n----' % str) # , file=stderr,end='\n')
    exit(-1)


def chomp(s): return s.rstrip('\n\r')

def chompsplit(s): return s.rstrip('\n\r').split('\t')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=info)
    parser.add_argument('-f','--file', default='-',action='store',required=True,help='[Required] File name to read from')

    parser.add_argument('-s','--sep',default='\t',action='store',required=False, help='delimiter separating columns [Default: \t]')
    args=parser.parse_args()
    if args.sep=='\\t' or args.sep=='tab':
        sep='\t'

    if args.file=='-': 
        args.file=sys.stdin

    try:
        df = pd.read_csv(args.file, index_col=0,sep=args.sep,header=None)
    except ValueError:
        error(f'Error during file reading: check if the args.idx_to_keep is correct')

    df = df.T
    
    df.to_csv(sys.stdout, sep=args.sep,index=False) 
    
    
    

