import os


def read_files_from_folder(folder):
    res = {}
    for path, _, files in os.walk(folder):
        for fn in files:
            fn = os.path.normpath(os.path.join(path, fn))
            with open(fn, 'rb') as f:
                res[os.path.relpath(fn, folder)] = f.read()
    return res
