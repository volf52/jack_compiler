import os
import sys
import argparse
from engine import CompilationEngine


def get_names(path):
    """Returns the names and paths of Jack classes.
    
    Args:
        path (str): Input paths (Jack file or dir of jack files)
    
    Returns:
        tuple: A tuple of lists of class names and their paths.
    """

    paths = []
    names = []
    out_names = []
    if os.path.isfile(path):
        paths.append(path)
        path, tmp_name = os.path.split(path)
        name, ext = os.path.splitext(tmp_name)
        out_names.append(os.path.join(path, name + '_local.xml'))
        if path:
                names = [os.path.splitext(x)[0] for x in os.listdir(path)
                         if os.path.splitext(x)[1] == '.jack']
        if ext != '.jack':
            print("Provided file is not a jack file.")
            sys.exit(1)
       
    elif os.path.isdir(path):
        paths = [x for x in os.listdir(path) 
                 if os.path.splitext(x)[1] == '.jack']
        names = [os.path.splitext(x)[0] for x in paths]
        paths = [os.path.join(path, x) for x in paths]
        out_names = [os.path.join(path, x + '_local.xml') for x in names]
    else:
        print('{} doesn\'t exist.'.format(path))
        sys.exit(1)
    return names, paths, out_names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inp_path', action="store")

    args = parser.parse_args()
    classes_in_dir, file_paths, outnames = get_names(args.inp_path)
    for pth, out_pth in zip(file_paths, outnames):
        engine = CompilationEngine(pth, out_pth, classes_in_dir)
        engine.compile_class()
        engine.generate_output()


if __name__ == '__main__':
    main()
