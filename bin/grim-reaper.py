#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os, fnmatch, time, sys, os.path, yaml

class tee(object):
    def __init__(self, _fd1, _fd2) :
        self.fd1 = _fd1
        self.fd2 = _fd2

    def __del__(self) :
        if self.fd1 != sys.stdout and self.fd1 != sys.stderr:
            self.fd1.close()
        if self.fd2 != sys.stdout and self.fd2 != sys.stderr:
            self.fd2.close()

    def write(self, text) :
        self.fd1.write(text)
        self.fd2.write(text)

    def flush(self) :
        self.fd1.flush()
        self.fd2.flush()

def _match(file_path, patterns):
    matches = set()
    for pattern in patterns:
        matches.update([path for file, path in file_path
                        if fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(path, pattern)])
    return matches

def locate(root, include, exclude):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        if ".protect.me.from.the.reaper" in files:
            print(f"{path}/.protect.me.from.the.reaper exists, will not look under this directory or lowe")
            dirs[:] = []
            continue
        file_path = [(file, os.path.join(path, file)) for file in files]
        matches = _match(file_path, include) - _match(file_path, exclude)
        for filename in sorted(matches):
            yield filename

CONFIG_FILE = os.path.expanduser("~/.config/grim-reaper.yml")

if __name__ == "__main__":
    # load default config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "rt") as conf:
            config = yaml.safe_load(conf)
            print(f"Reading default config from {CONFIG_FILE}")
    else:
        config = dict(output="reap.sh",
                      size=0.1, age=30,
                      include="*.fits *.tmp *.npz *.img".split(),
                      exclude="*.ms/* *.MS/* *.flagversions/*".split(),
        )
        yaml.dump(config, open(CONFIG_FILE, "wt"))
        print(f"Writing default config file to {CONFIG_FILE}")

    # parser
    from argparse import ArgumentParser
    parser = ArgumentParser(usage="""%(prog)s: [options] basedir [include]""",
      description="""Locates files whose atime is <= their mtime (i.e. written but never accessed since)""")

    parser.add_argument("-s","--size",metavar="GB",type=float,
                      help="only files over this size will be considered. Default is %(default)s.")
    parser.add_argument("-a", "--age", metavar="DAYS", type=int,
                      help="only files over this age will be considered.  Default is %(default)s.")
    parser.add_argument("-l", "--list", action="store_true",
                      help="list each individual file")
    parser.add_argument("-o", "--output", type=str,
                      help="name of output file, default is %(default)s")
    parser.add_argument("-f", "--force", action="store_true",
                      help="overwrite reap.sh if it exists")
    parser.add_argument("-x", "--exclude", type=str, action="append",
                        help="add an explicit exclude pattern")
    parser.add_argument("dir", type=str, help="Base directory to look under")
    parser.add_argument("include", nargs="*", type=str, help="Additional include patterns")

    parser.set_defaults(size=config['size'],
                        age=config['age'],
                        output=config['output'],
                        include=[], exclude=[])

    options = parser.parse_args()

    if os.path.exists(options.output):
        if not options.force:
            parser.error(f"output file {options.output} exists and -f is not set")

    include = [inc for inc in config['include'] + options.include if inc not in options.exclude]
    exclude = [exc for exc in config['exclude'] + options.exclude if exc not in options.include]

    if not include:
        parser.error("no include patterns")
    with open(options.output, "wt") as of:
        tee_out = tee(of, sys.stdout)
        minsize = options.size*2**30
        curtime = time.time()
        maxtime = curtime - options.age*(24*3600)

        print(f"## searching from {options.dir}", file=tee_out)
        print("## include: {}".format(",".join(include)), file=tee_out)
        print("## exclude: {}".format(",".join(exclude)), file=tee_out)
        print("## min size %.2f Gb, min age %.1f days"%(options.size, options.age), file=tee_out)


        files = set()
        sizes = 0
        counts = 0
        usersizes = {}
        dir_sizes = {}
        dir_counts = {}
        pattern_sizes = {patt:0. for patt in include}
        pattern_counts = {patt:0 for patt in include}

        # look through files
        for path in locate(options.dir, include, exclude):
            try:
                st = os.stat(path)
            except:
                continue
            mtime, atime = st.st_mtime, st.st_atime
            match = st.st_size < minsize or st.st_mtime > maxtime or st.st_atime > st.st_mtime
            if match:
                continue
            if options.list:
                print("# %-80s%10.1f days old %10.2f Gb"%(path, (curtime-mtime)/(24.*3600), st.st_size/2.**30))
            files.add(path)
            basename = os.path.basename(path)
            for patt in include:
                if fnmatch.fnmatch(basename, patt):
                    pattern_sizes[patt] += st.st_size
                    pattern_counts[patt] += 1
            sizes += st.st_size
            counts += 1
            usersizes[st.st_uid] = usersizes.get(st.st_uid,0) + st.st_size
            while not os.path.samefile(path, options.dir) and path != "/":
                path = os.path.dirname(path)
                dir_sizes[path] = dir_sizes.get(path,0) + st.st_size
                dir_counts[path] = dir_counts.get(path,0) + 1

        print("# Located %d stale files, total size %.2f Gb"%(len(files), sizes/2.**30), file=tee_out)
        print("# Total sizes by pattern:", file=tee_out)
        for patt, size in sorted(pattern_sizes.items()):
            print("#   {0}: {1} files, {2:.2f} Gb".format(patt, pattern_counts[patt], size/2.**30), file=tee_out)
        print("# Total sizes by subdirectory:", file=tee_out)
        for path, size in sorted(dir_sizes.items()):
            print("#   {0}: {1} files, {2:.2f} Gb".format(path, dir_counts[path], size/2.**30), file=tee_out)
        for path in sorted(files):
            print(f"rm '{path}'", file=of)
        print(f"# wrote remove script to {options.output}")
        print(f"# run '/bin/sh {options.output}' to effect the remove")

    # if options.output:
    #     file(options.output,"w").write("\n".join(sorted(files)))
    #     print "List of stale files written to", options.output

