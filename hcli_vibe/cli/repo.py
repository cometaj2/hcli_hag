import ast
import os
from git import Repo, InvalidGitRepositoryError

class Signature:
    def __init__(self):
        pass

    def get_signature(self, node):
        args = []
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                args.append(arg.arg)
            if node.args.vararg:
                args.append(f"*{node.args.vararg.arg}")
            if node.args.kwarg:
                args.append(f"**{node.args.kwarg.arg}")
        return f"({', '.join(args)})"

    def extract_structure(self, content):
        tree = ast.parse(content)
        structure = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_sig = f"class {node.name}:"
                structure.append(class_sig)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_sig = f"    def {item.name}{self.get_signature(item)}:"
                        structure.append(method_sig)
            elif isinstance(node, ast.FunctionDef):
                func_sig = f"def {node.name}{self.get_signature(node)}:"
                structure.append(func_sig)
        return structure

    def map_git_repo(self, repo_path):
        repo = Repo(repo_path)
        file_map = {}
        for item in repo.tree().traverse():
            if item.type == 'blob' and item.path.endswith('.py'):
                try:
                    content = item.data_stream.read().decode('utf-8')
                    file_map[item.path] = self.extract_structure(content)
                except Exception as e:
                    print(f"Error processing {item.path}: {str(e)}")
        return file_map

    def sig(self, repo_path):
        try:
            repo_path = repo_path.strip('"\'')
            normalized_path = os.path.abspath(os.path.normpath(repo_path))
            file_map = self.map_git_repo(normalized_path)
            project_name = repo_path

            # Build the output string instead of printing
            result = []
            result.append(f"Project: {project_name}\n")

            for path, structure in file_map.items():
                result.append(f"{path}:")
                if structure:
                    for item in structure:
                        result.append(item)
                else:
                    result.append("  (No classes or functions found)")
                result.append("")

            # Join all lines with newlines and return as a string
            return "\n".join(result)
        except InvalidGitRepositoryError:
            return None
