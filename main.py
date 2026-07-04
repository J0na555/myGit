import argparse
import sys
import json
from pathlib import Path 


class Repository:
    def __init__(self, path="."):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".mygit"

        # .mygit/objects
        self.objects_dir = self.git_dir / "objects"

        # .mygit/refs
        self.ref_dir = self.git_dir / "refs"
        self.heads_dir = self.ref_dir / "heads"

        # HEAD file
        self.head_file = self.git_dir / "HEAD"

        # .mygit/index
        self.index_file = self.git_dir / "index"



    def init(self) -> bool:
        if self.git_dir.exists():
            return False

        # create directories
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.ref_dir.mkdir()
        self.heads_dir.mkdir()


        # create initial HEAD pointing to a branch which is called sensei or master 
        self.head_file.write_text("ref: refs/heads/sensei\n")

        self.index_file.write_text(json.dumps({}, indent=2))

        print(f"Initialized empty mygit repository in {self.git_dir}")

        return True


def main():
    parser = argparse.ArgumentParser(
            description= "MyGit"
            )
    subparsers = parser.add_subparsers(
            # commands list like init, commit, ...
            dest="command",

            # help to see what are the commands
            help="Available commands"
            )

    #init command
    init_parser = subparsers.add_parser("init", help="Initialize a new repository")

    
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return
    repo = Repository()

    try:
        if args.command == "init":
            if not repo.init():
                print("Repository already exists")
                return
    except Exception as e:
        print(f"Error: {e}") 
        sys.exit(1)

main()
