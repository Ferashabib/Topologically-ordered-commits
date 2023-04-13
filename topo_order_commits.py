#!/usr/local/cs/bin/python3

#strace -f -o topo-test.tr pytest
#grep execve topo-test.tr
#Running those two commands should output only one line, corresponding to executing pytest/python.

import os 
import sys
import zlib

def topo_order_commits():
#Get git directory (can be helper function)
    git_dir = get_git_dir()

#Get list of local branch names (can be helper function)
    local_branches = get_local_branches(git_dir + "/refs/heads")

#Build the commit graph (can be helper function)
    root_commits, commits = get_commit_graph(git_dir, local_branches)

#Topologically sort the commit graph (can be helper fnction)
    topo_ordered = get_topo_order(root_commits, commits)

#Print the sorted order (can be helper function)
    print_commits(topo_ordered)

#Now helper functions!
#Discover the .git directory.
def get_git_dir():
    x = os.getcwd()
    while (True):
        if (os.path.isdir(os.path.join(x, '.git'))):
            return (x + "/.git")
        if (x == '/'):
            print ('Not inside a Git repository', file = sys.stderr)
            exit(1)
        x = os.path.dirname(x)

#Get the list of local branch names.
def get_local_branches(git_branch):
    #x = git_branch + "/.git" Add this to get_git_dir
    #y = os.listdir(x + "/refs/heads") add this when calling the 
    #function. This is because they ruin recursion.
    branch_list = []
    branches = {}
    lenpath = len(git_branch)
    branches_helper(branch_list, git_branch, lenpath)
    for branch in branch_list:
        path = os.path.join(git_branch, branch)
        branch_hash = open(path, "rb").read().decode("utf-8").strip()
        branches.setdefault(branch_hash, []).append(branch)
    return branches

#Recursive helper function
def branches_helper(branch, git_branch, lenpath):
    y = os.listdir(git_branch)
    for i in y:
        if os.path.isdir(os.path.join(git_branch, i)):
            branches_helper(branch, os.path.join(git_branch, i), lenpath)
        else:
            branch.append(os.path.join(git_branch[lenpath + 1: ], i))

#CommitNode class
class CommitNode:
    def __init__(self, commit_hash, local_branches: list[str] =[]):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()
        self.local_branches = local_branches

    def __lt__(self, other):
        return isinstance(other, CommitNode) and self.commit_hash < other.commit_hash
    
    def __hash__(self):
        return hash(self.commit_hash)

#Build the commit graph. 
def get_commit_graph(git_branch, local_branches):
    root_commits = []
    commits = {}
    stack = []
    for hash in local_branches:
        branch = CommitNode(hash)
        stack.append(branch)
        commits[hash] = branch
    while True:
        if not (len(stack) > 0):
            break
        current_node = stack.pop()
        current_node.local_branches = local_branches.get(current_node.commit_hash, [])
        commits[current_node.commit_hash] = current_node
        parent_hashes = get_parent(git_branch, current_node.commit_hash)
        if len(parent_hashes) == 0:
            root_commits.append(current_node)
        else:
            parents = []
            for parent_hash in parent_hashes:
                if parent_hash in commits:
                    parent = commits[parent_hash]
                else:
                    parent = CommitNode(parent_hash)
                    parents.append(parent)
                parent.children.add(current_node)
                current_node.parents.add(parent)
            stack.extend(parents)
    return root_commits, commits

#helper function for building the graph
def get_parent(git_branch, commit):
    path = os.path.join(git_branch + "/objects", commit[0:2], commit[2:])
    if (os.path.isfile(path)):
        result = open(path, "rb").read()
        decomp = zlib.decompress(result).decode("utf-8")
        parents = []
        for line in decomp.split("\n"):
            words = line.split(" ")
            if words[0] == "parent":
                parents.append(words[1])
        return parents
    else:
        return []

#Generate a topological ordering of the commits in the graph
def get_topo_order (root_commits, commits):
    topo_orders = []
    stack = root_commits
    visited_edges = {}
    while True:
        if not len(stack) > 0:
            break
        current_node = stack.pop()
        topo_orders.append(current_node)
        for child in sorted(current_node.children):
            visited_edges.setdefault(current_node.commit_hash, []).append(child)
            incoming_edges = sum (1
                for commit in commits.values()
                if (child in commit.children)
                and (child not in
                visited_edges.get(commit.commit_hash, []))
            )
            if incoming_edges == 0:
                stack.append(child)
    return topo_orders[::-1]

#Print the commit hashes in the order generated by the previous step, from the least to the greatest.
def print_commits(topo_ordered):
    sticky_start = False
    for x, commit in enumerate(topo_ordered):
        if sticky_start:
            start = " ".join([c.commit_hash for c in commit.children])
            print ("=" + start)
            sticky_start = False
        branch = " ".join([str(b) for b in commit.local_branches])
        print(f"{commit.commit_hash} {branch}", end="")
        end = ""
        if x != len(topo_ordered) -1 and topo_ordered[x+1] not in commit.parents:
            end = " ".join([c.commit_hash for c in commit.parents])
            end = "\n" + end + "=\n"
            sticky_start = True
        print (end)

if __name__ == "__main__":
    topo_order_commits()



