#!/usr/bin/env python
#need to add ebcdic
import re

from urllib2 import quote as urlquote
from urllib2 import unquote as urlunquote
from xml.sax.saxutils import escape as entityquote
from xml.sax.saxutils import unescape as entityunquote
from codecs import register, CodecInfo

from struct import pack, unpack

###############################################################################
# Morse Codec Defs
###############################################################################
MORSE = (
    ('A', ".-"),
    ('B', "-.."),
    ('C', "-.-."),
    ('D', "-.."),
    ('E', "."),
    ('F', "..-."),
    ('G', "--."),
    ('H', "...."),
    ('I', ".."),
    ('J', ".---"),
    ('K', "-.-"),
    ('L', ".-.."),
    ('M', "--"),
    ('N', "-."),
    ('O', "---"),
    ('P', ".--."),
    ('Q', "--.-"),
    ('R', ".-."),
    ('S', "..."),
    ('T', "-"),
    ('U', "..-"),
    ('V', "...-"),
    ('W', ".--"),
    ('X', "-..-"),
    ('Y', "-.--"),
    ('Z', "--.."),
    ('0', "-----"),
    ('1', ".----"),
    ('2', "..---"),
    ('3', "...--"),
    ('4', "....-"),
    ('5', "....."),
    ('6', "-...."),
    ('7', "--..."),
    ('8', "---.."),
    ('9', "----."),
    (' ', "/"),
    ('.', ".-.-.-"),
    (',', "--..--"),
    ('?', "..--.."),
    ('', '')
    )


###############################################################################
# ascii85 defs
###############################################################################

ascii85_charset = re.compile('([!-u]*)')


###############################################################################
# helper functions
###############################################################################

def blocks(data, size):
    assert (len(data) % size) == 0, \
           "Cannot divide into blocks of size %s" % size
    for i in xrange(0, len(data), size):
        yield data[i:i + size]


###############################################################################
# actual encoders and encoding wrappers
###############################################################################


def morse_encode(input, errors='strict'):
    morse_map = dict(MORSE)
    input = input.upper()
    for c in input:
        assert c in morse_map, "Unencodable character '%s' found. Failing" % c
    output = ' '.join(morse_map[c] for c in input)
    return (output, len(input))


def morse_decode(input, errors='strict'):
    morse_map = dict((c, m) for m, c in MORSE)
    input = input.replace('  ', '/').replace('/', ' / ')
    splinput = input.split()
    for c in splinput:
        assert c in morse_map, "Could not decode '%s' to ascii. Failing" % c
    output = ''.join(morse_map[c] for c in splinput)
    return (output, len(input))


def bin_encode(input, errors='strict'):
    """print 8 bits of whatever int goes in"""
    output = ""
    for c in input:
        l = '{0:0>8b}'.format(ord(c))
        output += ''.join(l)
    return (output, len(input))


def bin_decode(input, errors='strict'):
    """print 8 bits of whatever int goes in"""
    output = ""
    assert (len(input) % 8) == 0, \
           "Wrong number of bits, %s is not divisible by 8" % len(input)
    output = ''.join(chr(int(c, 2)) for c in blocks(input, 8))
    return (output, len(input))


def url_decode(input, errors='strict'):
    output = urlunquote(input)
    return (output, len(input))


def url_encode(input, errors='strict'):
    output = urlquote(input)
    return (output, len(input))


def entity_decode(input, errors='strict'):
    output = entityunquote(input)
    return (output, len(input))


def entity_encode(input, errors='strict'):
    output = entityquote(input)
    return (output, len(input))


def ascii85_encode(input, errors='strict'):
    #encoding is adobe not btoa
    bs = 4
    padding = bs - ((len(input) % bs) or bs)
    input += '\0' * padding
    output = ""
    for block in blocks(input, bs):
        start = unpack(">I", block)[0]
        if not start:
            output += "z"
            continue
        quot, rem = divmod(start, 85)
        chr_block = chr(rem + 33)
        for i in xrange(bs):
            quot, rem = divmod(quot, 85)
            chr_block += chr(rem + 33)
        output += ''.join(reversed(chr_block))
    if padding:
        output = output[:-padding]
    return output, len(input)


def ascii85_decode(input, errors='strict'):
    bs = 5
    for i in ('y', 'z'):
        for block in input.split(i)[:-1]:
            assert not len(block) % bs, "'%s' found within a block" % i
    # supports decoding as adobe or btoa 4.2
    input = input.replace('z', '!!!!!')  # adobe & btoa 4.2
    # "z" in the middle of a block should be an error... this will not
    # be correctly handled.
    input = input.replace('y', '+<VdL')  # btoa replace block of ' '
    input = ''.join(re.findall(ascii85_charset, input))
    # silently drop all non-ascii85 chars....
    padding = bs - ((len(input) % bs) or bs)
    input += 'u' * padding
    output = ""
    for block in blocks(input, bs):
        data = 0
        for idx in xrange(len(block)):
            place = (bs - 1) - idx
            place_val = ord(block[idx]) - 33
            if place:
                place_val = place_val * (85 ** place)
            data += place_val
        assert 0 <= data <= 4294967295, "invalid block '%s'" % block
        output += pack(">I", data)
    if padding:
        output = output[:-padding]
    return output, len(input)


###############################################################################
# Codec Registration
###############################################################################

CODECS_IN_FILE = {"morse": CodecInfo(name='morse',
                                     encode=morse_encode,
                                     decode=morse_decode),
                  "bin": CodecInfo(name='bin',
                                   encode=bin_encode,
                                   decode=bin_decode),
                  "url": CodecInfo(name='url',
                                   encode=url_encode,
                                   decode=url_decode),
                  "entity": CodecInfo(name='entity',
                                   encode=entity_encode,
                                   decode=entity_decode),
                  "ascii85": CodecInfo(name='ascii85',
                                       encode=ascii85_encode,
                                       decode=ascii85_decode),
                }


register(lambda name: CODECS_IN_FILE[name])

# Local variables:
# eval: (add-hook 'after-save-hook '(lambda ()
#           (shell-command "pep8 hackercodecs.py > lint")) nil t)
# end: