"""
Modified version of 
https://github.com/bastikr/boolean.py/blob/master/boolean/boolean.py#L116
To use different sets of logic symbols
It's just a copy paste of the defualt tokenize implementation with the TOKENS
dictionary moved out of the body of the function so that it can be changed.

Since this is used for parsing combinations of tags, there is some need to
restrict the set of operator strings to minimize risk of confusion with
legitimate tag names.

edit: mostly rewrote the tokenize function because it wasn't working with my new
tokens, and i didn't know why

edit2: okay I just went ahead and made it handle all of the checking for of tags

Copyright (c) 2009-2020 Sebastian Kraemer, basti.kr@gmail.com and others
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from boolean.boolean import *


class TagAlgebra(BooleanAlgebra):

    TOKENS = {
        '&&': TOKEN_AND,
        '||': TOKEN_OR,
        '~~': TOKEN_NOT,
        '{': TOKEN_LPAR, '}': TOKEN_RPAR,
    }

    def __init__(self, tagslist):
        self.tagslist = tagslist
        super().__init__()

    def tokenize(self, expr):
        
        if not isinstance(expr, basestring):
            raise TypeError('expr must be string but it is %s.' % type(expr))

        TOKENS=self.TOKENS
        tagslist = self.tagslist

        base_expr = str(expr)

        position = 0
        length = len(expr)

        while len(expr) > 0:
            next_symbols = [(k,expr.find(k)) for k,v in TOKENS.items()]
            next_symbols = list(filter(lambda x: x[1] >= 0, next_symbols))
            position = base_expr.find(expr)
            if len(next_symbols) == 0:
                tok = expr.strip()
                if tok in tagslist:
                    result = TOKEN_TRUE
                else:
                    result = TOKEN_FALSE
                yield result, tok, position
                break
            next_sym, pos = min(next_symbols, key=lambda x: x[1])
            if pos != 0:
                tok = expr[:pos].strip()
                if tok in tagslist:
                    result = TOKEN_TRUE
                else:
                    result = TOKEN_FALSE
                yield result, tok, position
                expr = expr[pos:].strip()
            else:
                yield TOKENS[next_sym], next_sym, position
                expr = expr[len(next_sym):].strip()


