#/usr/bin/env python3

from string import whitespace

block_tokens = {}
inline_tokens = {}

def parse_into(file, store, minelems=2):
    msg = 'error: invalid line: {}\nnote: in file "{}"'
    
    gen = (line.rstrip('\n') for line in file)
    for line in gen:
        if not line.strip():
            continue

        parts = [part.strip() for part in line.split('\t')]
        nparts = len(parts)
        if nparts < minelems or nparts > 4:
            raise Exception(msg.format(line, file.name))

        toklen = len(parts[0])
        if toklen not in store:
            store[toklen] = {}

        if parts[0] in store[toklen]:
            raise Exception(msg.format(line, file.name))

        if nparts == 4:
            if parts[-1] == "yes":
                parts[-1] = True
            elif parts[-1] == "no":
                parts[-1] = False
            else:
                raise Exception(msg.format(line, file.name))

        elif nparts == 3:
            parts.append(True)

        store[toklen][parts[0]] = tuple(parts[1:])

def parse_block_config(fname):
    with open(fname, 'r') as f:
        parse_into(f, block_tokens, 3)

def parse_inline_config(fname):
    with open(fname, 'r') as f:
        parse_into(f, inline_tokens)

def block_step_length():
    return max(key for key in block_tokens)

def inline_step_length():
    return max(key for key in inline_tokens)

file_sheader = '''<!DOCTYPE html>
<html lang="{}">
  <head>
    <meta charset="utf-8">
    <title>{}</title>'''
file_stylesheet = '''    <link rel="stylesheet" type="text/css" href="{}">'''
file_eheader = '''  </head>
  <body class="{}">'''
file_footer = '''  </body>
</html>'''

class InlineParser:
    def __init__(self, outf):
        self._outf = outf
        self._tmax = inline_step_length()
        self._tokstate = []
        self._noadmit = False

    def _print(self, text):
        return print(text, file=self._outf, end='')

    def _translate_token(self, token, token_rep):
        if self._noadmit:
            if token == self._tokstate[-1]:
                self._noadmit = False
            else:
                return token

        if len(token_rep) == 1:
            return token_rep[0]
        elif token not in self._tokstate:
            self._tokstate.append(token)
            if not token_rep[2]: self._noadmit = True
            return token_rep[0]
        elif token == self._tokstate[-1]:
            self._tokstate.pop()
            return token_rep[1]
        else:
            msg = "error: encountered unexpected token: {}"
            raise Exception(msg.format(token))
    
    def _emit_token(self, buf):
        for i in range(self._tmax, 0, -1):
            bufpart = str().join(buf[0:i])
            if bufpart in inline_tokens[i]:
                token_rep = inline_tokens[i][bufpart]
                output = self._translate_token(bufpart, token_rep)

                self._print(output)
                del buf[0:i]
                return

        self._print(buf.pop(0))

    def reset(self, indent=6):
        if len(self._tokstate) > 0:
            self._print(' ' * indent)

            for token in reversed(self._tokstate):
                output = inline_tokens[len(token)][token][1]
                self._print(output)

            self._print('\n')
            self._tokstate.clear()
    
    def parse(self, line, indent=6):
        if not line.strip():
            return

        self._print(' ' * indent)

        buf = []
        for letter in line:
            buf.append(letter)
            if len(buf) >= self._tmax:
                self._emit_token(buf)

        while len(buf) > 0:
            self._emit_token(buf)

        self._print('\n')


class BlockParser:
    ACCEPTING = 1
    INBLOCK = 2

    def __init__(self, outf, iparser):
        self._outf = outf
        self._iparser = iparser
        self._tmax = block_step_length()
        self._bstate = []
        self._ilevel = 0
        self._gstate = BlockParser.ACCEPTING
        self._pclasses = ""
        self._noadmit = False

    def _print(self, text):
        print(' ' * self._level(), file=self._outf, end='')
        print(text, file=self._outf)
    
    def _next_token(self, line, pos):
        start = min(self._tmax, len(line) - pos)
        for i in range(start, 0, -1):
            bufpart = str().join(line[pos:pos + i])
            if bufpart in block_tokens[i]:
                return (True, bufpart)

        return (False, line[pos:].rstrip())

    def _tokenize(self, line):
        toklist = []
        linepos = 0

        cont = True
        while cont:
            while linepos < len(line) and line[linepos] in whitespace:
                linepos += 1

            cont, tok = self._next_token(line, linepos)
            linepos += len(tok)
            toklist.append(tok)

        return toklist

    def _emit_para_start(self):
        self._print('<p class="{}">'.format(self._pclasses))
        self._ilevel += 1

    def _emit_para_end(self):
        self._ilevel -= 1
        self._print('</p>')

    def _emit_block_start(self, blist):
        msg = "error: expected same or greater indentation"
        msg += "\nnote: have {}, got {}".format(str(self._bstate), str(blist))

        if len(blist) >= self._ilevel:
            for x, y in zip(blist, self._bstate):
                if x != y: raise Exception(msg)

            additional = blist[self._ilevel:]
            for block in additional:
                block_info = block_tokens[len(block)][block]
                self._print(block_info[0])

                self._bstate.append(block)
                self._ilevel += 1

                if len(block_info) == 3 and not block_info[-1]:
                    self._noadmit = True
                    break

            if not self._noadmit:
                self._emit_para_start()

        else:
            print(blist, self._ilevel)
            raise Exception(msg)

    def _emit_block_end(self, blist):
        self._iparser.reset(self._level())
        msg = "error: expected same or lesser indentation"
        msg += "\nnote: have {}, got {}".format(str(self._bstate), str(blist))

        if len(blist) <= self._ilevel:
            for x, y in zip(blist, self._bstate):
                if x != y: raise Exception(msg)

            if not self._noadmit:
                self._emit_para_end()

            blen = len(blist)

            if self._ilevel > len(blist):
                self._noadmit = False

                while self._ilevel > len(blist):
                    currblock = self._bstate.pop()
                    output = block_tokens[len(currblock)][currblock][1]
                    self._ilevel -= 1
                    self._print(output)

        else: raise Exception(msg)
    
    def _level(self):
        return 6 + (2 * self._ilevel)
    
    def parse(self, line):
        toklist = self._tokenize(line)
        del line

        blocks = toklist[:-1]
        text = toklist[-1]
        del toklist

        if self._gstate == BlockParser.ACCEPTING:
            if text != '':
                self._emit_block_start(blocks)
                self._gstate = BlockParser.INBLOCK
            elif blocks != self._bstate:
                msg = "error: expected same indentation"
                msg += "\nnote: expected {}, got {}"
                raise Exception(msg.format(str(self._bstate), str(blocks)))

        else:
            if text == '':
                self._emit_block_end(blocks)
                self._gstate = BlockParser.ACCEPTING
            elif len(blocks) > 0:
                msg = "error: didn't expect an indentation spec"
                raise Exception(msg)

        self._iparser.parse(text, self._level())

    def end(self):
        self.parse('')

    def set_paragraphing(self, gap, drop):
        classes = []
        if gap: classes.append("gap")
        if drop: classes.append("drop")
        self._pclasses = " ".join(classes)


def set_config(bconf="block.cfg", iconf="inline.cfg"):
    parse_block_config(bconf)
    parse_inline_config(iconf)

def parse_file(inname, outname,
               title="Document", stylesheets=["rules.css"],
               invert=False, gap=True, drop=False, lang="en"):
    with open(inname, 'r') as inf, open(outname, 'w') as outf:
        parser = BlockParser(outf, InlineParser(outf))
        parser.set_paragraphing(gap, drop)

        print(file_sheader.format(lang, title), file=outf)
        for sheet in stylesheets:
            print(file_stylesheet.format(sheet), file=outf)
        print(file_eheader.format("invert" if invert else ''), file=outf)

        gen = (line.rstrip('\n') for line in inf)
        for line in gen:
            try:
                parser.parse(line)
            except Exception as e:
                msg = e.args[0] + "\non line: {}"
                e.args = (msg.format(line),)
                raise

        parser.end()
        print(file_footer, file=outf)

import getopt
from sys import argv, exit

if __name__ == "__main__":
    shortopts = "b:l:t:s:i"
    opts, args = getopt.getopt(argv[1:], shortopts)

    blockconf = "~/.mwp/block.cfg"
    inlineconf = "~/.mwp/inline.cfg"
    title = "Document"
    stylesheets = []
    invert = False

    for o, a in opts:
        if o == "-b":
            blockconf = a
        elif o == "-l":
            inlineconf = a
        elif o == "-t":
            title = a
        elif o == "-s":
            stylesheets.append(a)
        elif o == "-i":
            invert = True

    set_config(blockconf, inlineconf)

    for arg in args:
        parse_file(arg, arg + ".html", title, stylesheets, invert)
