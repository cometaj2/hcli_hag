import git
from git import Repo
import os

def show_git_diff(repo_path='.', compare_with_head=True, commit_range=None, file_path=None, recursive=True):
    """
    Show git diff using GitPython, with option for recursive diffing across entire repo.
    
    Args:
        repo_path (str): Path to the git repository
        compare_with_head (bool): If True, compare working directory with HEAD
        commit_range (str, optional): Commit range like 'HEAD~1..HEAD' (ignored if compare_with_head is True)
        file_path (str, optional): Specific file to diff (ignored if recursive is True)
        recursive (bool): Whether to show diffs for all changed files in the repo
    
    Returns:
        str: The git diff output
    """
    try:
        # Initialize repo
        repo = Repo(repo_path)
        
        # Check if the repo is valid
        if not repo.bare:
            # Set up diff options for the entire repository
            diff_options = ['--stat', '--color', '-p']
            
            # Set default value for recursive option
            if recursive:
                # When recursive, file_path is ignored and we include all changes
                file_path = None
            
            if compare_with_head:
                # Compare working directory with HEAD (unstaged + staged changes)
                diff_output = repo.git.diff(*diff_options, file_path)
            elif commit_range:
                # Parse the commit range
                if '..' in commit_range:
                    old, new = commit_range.split('..')
                    diff_output = repo.git.diff(*diff_options, old, new, file_path)
                else:
                    # Single commit comparison (with its parent)
                    diff_output = repo.git.diff(*diff_options, commit_range + '^', commit_range, file_path)
            else:
                # Default: diff between working directory and HEAD
                diff_output = repo.git.diff(*diff_options, file_path)
            
            return diff_output
        else:
            return "Could not generate diff: Repository is bare."
    except git.exc.InvalidGitRepositoryError:
        return f"Error: {repo_path} is not a valid Git repository."
    except git.exc.NoSuchPathError:
        return f"Error: Path {repo_path} does not exist."
    except Exception as e:
        return f"Error: {str(e)}"

def get_repo_diffs(repo_path='.', compare_with_head=True, commit_range=None):
    """
    Get detailed information about all changes in the repository.
    
    Args:
        repo_path (str): Path to the git repository
        compare_with_head (bool): If True, compare working directory with HEAD
        commit_range (str, optional): Commit range to inspect (ignored if compare_with_head is True)
    
    Returns:
        dict: Dictionary of file paths and their corresponding diffs
    """
    try:
        repo = Repo(repo_path)
        
        if compare_with_head:
            # Get list of changed files between working directory and HEAD
            diffs = repo.git.diff('--name-only').split('\n')
            
            # Create a dictionary to store file paths and their diffs
            file_diffs = {}
            
            # Get diff for each file
            for file_path in diffs:
                if file_path.strip():  # Skip empty entries
                    file_diff = repo.git.diff(file_path)
                    file_diffs[file_path] = file_diff
        else:
            if commit_range:
                if '..' in commit_range:
                    old, new = commit_range.split('..')
                else:
                    old = commit_range + '^'
                    new = commit_range
                
                # Get the diff between commits
                diffs = repo.git.diff(old, new, name_only=True).split('\n')
                
                # Create a dictionary to store file paths and their diffs
                file_diffs = {}
                
                # Get diff for each file
                for file_path in diffs:
                    if file_path.strip():  # Skip empty entries
                        file_diff = repo.git.diff(old, new, file_path)
                        file_diffs[file_path] = file_diff
        
        return file_diffs
    except Exception as e:
        return {f"Error": str(e)}

# Example usage
if __name__ == "__main__":
    # Option 1: Simple recursive diff (entire repo at once)
    print("OPTION 1: FULL REPOSITORY DIFF")
    print(show_git_diff(repo_path="/Users/jeff/Documents/workspace/hcli/hcli_hai", 
                        compare_with_head=True,  # Changed from commit_range to working dir vs HEAD
                        recursive=True))
    
#     # Option 2: Get file-by-file diffs for more control
#     print("\n\nOPTION 2: FILE-BY-FILE DIFFS")
#     file_diffs = get_repo_diffs(repo_path="/Users/jeff/Documents/workspace/hcli/hcli_hai", 
#                                compare_with_head=True)  # Working dir vs HEAD
#     for file_path, diff in file_diffs.items():
#         print(f"\n{'='*80}\nFILE: {file_path}\n{'='*80}")
#         print(diff)
