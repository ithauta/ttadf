import re
from functools import reduce



def mitLicense():

    l = '''
/*
This file is part of TTADF framework.

MIT License

Copyright (c) 2018 Ilkka Hautala, CMVS, University of Oulu, Finland

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

'''

    return l


def ptFile():

    f = '''
/*
Portions of the source code is published under following license:

MIT License

Copyright (c) 2016 Serge Zaitsev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/


#ifndef __PT_H__
#define __PT_H__

struct pt {
  void *label;
};

#define _pt_line3(name, line) _pt_##name##line
#define _pt_line2(name, line) _pt_line3(name, line)
#define _pt_line(name) _pt_line2(name, __LINE__)

#define PT_WAITING 0
#define PT_YIELDED 1
#define PT_EXITED  2
#define PT_ENDED   3

#ifndef NULL
#define NULL 0
#endif


#define PT_INIT(pt)   (pt)->label = NULL;


#define PT_THREAD(name_args) char name_args



#define pt_label(pt)\
  do {                                                                         \\
    _pt_line(label) : (pt)->label = &&_pt_line(label);                         \\
  } while (0)


#define PT_BEGIN(pt)    char PT_YIELD_FLAG = 1;                                \\
    do {                                                                       \\
    if ((pt)->label != NULL) {                                                 \\
      goto *(pt)->label;                                                       \\
    }                                                                          \\
  } while (0)



#define PT_END(pt) pt_label(pt); PT_YIELD_FLAG = 0;                            \\
                   PT_INIT(pt); return PT_ENDED;



#define PT_WAIT_UNTIL(pt, condition)	                                       \\
  do {						                                                   \\
    pt_label(pt);				                                               \\
    if(!(condition)) {				                                           \\
      return PT_WAITING;			                                           \\
    }						                                                   \\
  } while(0)



#define PT_WAIT_WHILE(pt, cond)  PT_WAIT_UNTIL((pt), !(cond))


#define PT_WAIT_THREAD(pt, thread) PT_WAIT_WHILE((pt), PT_SCHEDULE(thread))


#define PT_SPAWN(pt, child, thread)		                                        \\
  do {						                                                    \\
    PT_INIT((child));				                                            \\
    PT_WAIT_THREAD((pt), (thread));		                                        \\
  } while(0)


#define PT_RESTART(pt)				                                            \\
  do {						                                                    \\
    PT_INIT(pt);				                                                \\
    return PT_WAITING;			                                                \\
  } while(0)


#define PT_EXIT(pt)				                                                \\
  do {						                                                    \\
    PT_INIT(pt);				                                                \\
    return PT_EXITED;			                                                \\
  } while(0)


#define PT_SCHEDULE(f) ((f) < PT_EXITED)


#define PT_YIELD(pt)				                                            \\
  do {						                                                    \\
    PT_YIELD_FLAG = 0;				                                            \\
    pt_label(pt);				                                                \\
    if(PT_YIELD_FLAG == 0) {			                                        \\
      return PT_YIELDED;			                                            \\
    }						                                                    \\
  } while(0)


#define PT_YIELD_UNTIL(pt, cond)		                                        \\
  do {						                                                    \\
    PT_YIELD_FLAG = 0;				                                            \\
    pt_label(pt);				                                                \\
    if((PT_YIELD_FLAG == 0) || !(cond)) {	                                    \\
      return PT_YIELDED;			                                            \\
    }						                                                    \\
  } while(0)



#endif /* __PT_H__ */
'''


    return f


def strIsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def addTab(string, nbtabs):
    string = '\t' + string
    return string.replace("\n", "\n"+"\t"*nbtabs)

def addTempString(string):
    tempString = 'ttadf_temp'





#https://stackoverflow.com/questions/241327/python-snippet-to-remove-c-and-c-comments
def comment_remover(text):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " " # note: a space and not an empty string
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)


def GCD(a, b):
    # Gives greatest common divisor using Euclid's Algorithm.
    while b:
        a, b = b, a % b
    return a


def LCM( a, b):
    # gives lowest common multiple of two numbers
    return a * b // GCD(a, b)


def LCMM(*args):
    # gives LCM of a list of numbers passed as argument
    return reduce(LCM, args)


def GCDM(*args):
    return reduce(GCD, args)


def isPowerOf2( x):
    return (x != 0) & ((x & (~x + 1)) == x)