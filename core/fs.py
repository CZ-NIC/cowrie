# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

import os, time

A_NAME, \
    A_TYPE, \
    A_UID, \
    A_GID, \
    A_SIZE, \
    A_MODE, \
    A_CTIME, \
    A_CONTENTS, \
    A_TARGET, \
    A_REALFILE = range(0, 10)
T_LINK, \
    T_DIR, \
    T_FILE, \
    T_BLK, \
    T_CHR, \
    T_SOCK, \
    T_FIFO = range(0, 7)

class HoneyPotFilesystem(object):
    def __init__(self, fs):
        self.fs = fs

    def resolve_path(self, path, cwd):
        pieces = path.rstrip('/').split('/')

        if path[0] == '/':
            cwd = []
        else:
            cwd = [x for x in cwd.split('/') if len(x) and x is not None]

        while 1:
            if not len(pieces):
                break
            piece = pieces.pop(0)
            if piece == '..':
                if len(cwd): cwd.pop()
                continue
            if piece in ('.', ''):
                continue
            cwd.append(piece)

        return '/%s' % '/'.join(cwd)

    def get_path(self, path):
        p = self.fs
        for i in path.split('/'):
            if not i:
                continue
            p = [x for x in p[A_CONTENTS] if x[A_NAME] == i][0]
        return p[A_CONTENTS]

    def list_files(self, path):
        return self.get_path(path)

    def exists(self, path):
        f = self.getfile(path)
        if f is not False:
            return True

    def update_realfile(self, f, realfile):
        if not f[A_REALFILE] and os.path.exists(realfile) and \
                not os.path.islink(realfile) and os.path.isfile(realfile) and \
                f[A_SIZE] < 25000000:
            print 'Updating realfile to %s' % realfile
            f[A_REALFILE] = realfile

    def realfile(self, f, path):
        self.update_realfile(f, path)
        if f[A_REALFILE]:
            return f[A_REALFILE]
        return None

    def getfile(self, path):
        pieces = path.strip('/').split('/')
        p = self.fs
        while 1:
            if not len(pieces):
                break
            piece = pieces.pop(0)
            if piece not in [x[A_NAME] for x in p[A_CONTENTS]]:
                return False
            p = [x for x in p[A_CONTENTS] \
                if x[A_NAME] == piece][0]
        return p

    def mkfile(self, path, uid, gid, size, mode, ctime = None):
        if ctime is None:
            ctime = time.time()
        dir = self.get_path(os.path.dirname(path))
        outfile = os.path.basename(path)
        if outfile in [x[A_NAME] for x in dir]:
            dir.remove([x for x in dir if x[A_NAME] == outfile][0])
        dir.append([outfile, T_FILE, uid, gid, size, mode, ctime, [],
            None, None])
        return True

    def mkdir(self, path, uid, gid, size, mode, ctime = None):
        if ctime is None:
            ctime = time.time()
        if not len(path.strip('/')):
            return False
        try:
            dir = self.get_path(os.path.dirname(path.strip('/')))
        except IndexError:
            return False
        dir.append([os.path.basename(path), T_DIR, uid, gid, size, mode,
            ctime, [], None, None])
        return True

    def is_dir(self, path):
        if path == '/':
            return True
        dir = self.get_path(os.path.dirname(path))
        l = [x for x in dir
            if x[A_NAME] == os.path.basename(path) and
            x[A_TYPE] == T_DIR]
        if l:
            return True
        return False

# vim: set sw=4 et: