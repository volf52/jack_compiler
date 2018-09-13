import os
import sys
import argparse
from engine import CompilationEngine
from tokenizer import Tokenizer


def get_names(path):
    """Returns the names and paths of Jack classes.
    
    Args:
        path (str): Input paths (Jack file or dir of jack files)
    
    Returns:
        tuple: A tuple of lists of class names and their paths.
    """

    paths = []
    out_names = []
    if os.path.isfile(path):
        paths.append(path)
        path, tmp_name = os.path.split(path)
        name, ext = os.path.splitext(tmp_name)
        out_names.append(os.path.join(path, name + '.vm'))
        if ext != '.jack':
            print("Provided file is not a jack file.")
            sys.exit(1)
       
    elif os.path.isdir(path):
        paths = [x for x in os.listdir(path) 
                 if os.path.splitext(x)[1] == '.jack']
        names = [os.path.splitext(x)[0] for x in paths]
        paths = [os.path.join(path, x) for x in paths]
        out_names = [os.path.join(path, x + '.vm') for x in names]
    else:
        print('{} doesn\'t exist.'.format(path))
        sys.exit(1)
    return paths, out_names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inp_path', action="store")

    args = parser.parse_args()
    file_paths, outnames = get_names(args.inp_path)

    for pth, out_pth in zip(file_paths, outnames):
        with open(pth, 'r') as f:
            tk = Tokenizer(f.readlines())
        engine = CompilationEngine(tk, out_pth)
        engine.compile_class()
    
    print("Finished compilation...")


if __name__ == '__main__':
    main()
