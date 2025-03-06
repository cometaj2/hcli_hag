import os
import ast
from git import Repo

def get_signature(node):
    args = []
    if isinstance(node, ast.FunctionDef):
        for arg in node.args.args:
            args.append(arg.arg)
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
    return f"({', '.join(args)})"

def extract_structure(content):
    tree = ast.parse(content)
    structure = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            class_sig = f"class {node.name}:"
            structure.append(class_sig)
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_sig = f"    def {item.name}{get_signature(item)}:"
                    structure.append(method_sig)
        elif isinstance(node, ast.FunctionDef):
            func_sig = f"def {node.name}{get_signature(node)}:"
            structure.append(func_sig)
    return structure

def map_git_repo(repo_path):
    repo = Repo(repo_path)
    file_map = {}
    for item in repo.tree().traverse():
        if item.type == 'blob' and item.path.endswith('.py'):
            try:
                content = item.data_stream.read().decode('utf-8')
                file_map[item.path] = extract_structure(content)
            except Exception as e:
                print(f"Error processing {item.path}: {str(e)}")
    return file_map

if __name__ == '__main__':
    repo_path = '.'  # Use the current directory as the repository path
    file_map = map_git_repo(repo_path)
    for path, structure in file_map.items():
        print(f"{path}:")
        if structure:
            for item in structure:
                print(item)
        else:
            print("  (No classes or functions found)")
        print()
