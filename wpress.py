#!/usr/bin/env python3

import os
import os.path
import sys

# header structure
filename_size = 255
content_size = 14
mtime_size = 12
prefix_size = 4096
header_size = filename_size + content_size + mtime_size + prefix_size

nul = b'\x00'
eof_block = header_size * nul

def decode_header(block):
    offset = 0
    path = block[offset:filename_size].rstrip(nul).decode('utf8')

    offset += filename_size
    size = int(block[offset:offset + content_size].rstrip(nul))

    offset += content_size
    mtime = int(block[offset:offset + mtime_size].rstrip(nul))

    offset += mtime_size
    prefix = block[offset:offset + prefix_size].rstrip(nul).decode('utf8')
    
    if prefix != '.':
        path = prefix + '/' + path

    return path, size, mtime

def encode_header(path):
    st = os.stat(path)
    size = str(st.st_size).encode('utf8')
    mtime = str(int(st.st_mtime)).encode('utf8')
    prefix = os.path.dirname(path).encode('utf8') or b'.'
    fname = os.path.basename(path).encode('utf8')

    header = fname + (filename_size - len(fname)) * nul
    header += size + (content_size - len(size)) * nul
    header += mtime + (mtime_size - len(mtime)) * nul
    header += prefix + (prefix_size - len(prefix)) * nul
    assert len(header) == header_size
    return header

def decode(archive):
    with open(archive, 'rb') as f:
        while 1:
            block = f.read(header_size)
            assert len(block) == header_size, 'Error, short read, file possibly truncated'
            if block == eof_block:
                break

            path, size, mtime = decode_header(block)

            dname = os.path.dirname(path)
            if dname:
                os.makedirs(dname, mode=0o755, exist_ok=True)

            with open(path, 'wb') as out:
                data = f.read(size)
                assert len(data) == size, 'Error, short read, file possibly truncated'
                out.write(data)

            os.chmod(path, 0o644)
            os.utime(path, (mtime, mtime))

def encode(archive, files):
    with open(archive, 'wb') as f:
        for fname in files:
            if os.path.isfile(fname):
                header = encode_header(fname)
                f.write(header)
                with open(fname, 'rb') as fi:
                    f.write(fi.read())
            else:
                for base, dirs, files in os.walk(fname):
                    for fn in files:
                        path = base + '/' + fn
                        header = encode_header(path)
                        f.write(header)
                        with open(path, 'rb') as fi:
                            f.write(fi.read())

        f.write(eof_block)
    
def main(argv):
    if not argv or argv[0] not in ('-a', '-e'):
        print('./wpress.py -a|-e <archive> [files...]')
        return

    if argv[0] == '-a':
        encode(argv[1], argv[2:])
    else:
        decode(argv[1])

if __name__ == '__main__':
    main(sys.argv[1:])
