import argparse
import sys
import json
import hashlib
import zlib
from pathlib import Path 

class GitObject:
    def __init__(self, obj_type: str, content: bytes):
        self.type = obj_type
        self.content = content

    def hash(self) -> str:
        # f(<type> <size>\0<content>)
        header = f"{self.type} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()

    def serialize(self) -> bytes:
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)

    @classmethod
    def deserialize(cls, data: bytes) -> GitObject:
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx].decode()
        content = decompressed[null_idx + 1 :]

        obj_type, _ = header.split(" ")

        return cls(obj_type, content)
        

class Blob(GitObject):
    def __init__(self, content: bytes):
        super().__init__("blob", content)


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

        self.save_index({})
        # self.index_file.write_text(json.dumps({}, indent=2))

        print(f"Initialized empty mygit repository in {self.git_dir}")

        return True


    def store_object(self, obj: GitObject):
        obj_hash = obj.hash()
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]

        if not obj_file.exists():
            obj_dir.mkdir(exist_ok=True)
            obj_file.write_bytes(obj.serialize())

        return obj_hash

    def load_index(self) -> dict[str, str]:
        if not self.index_file.exists():
            return {}

        try:
            return json.loads(self.index_file.read_text())
        except:
            return {}

    def save_index(self, index: dict[str, str]):
        self.index_file.write_text(json.dumps(index, indent=2))

    def add_file(self, path: str):
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        # Read the file content
        content = full_path.read_bytes()
        # Create BLOB object from the content
        blob = Blob(content)
        # store the blob object in database (.git/objects)
        blob_hash = self.store_object(blob)
        # Update index to include the file
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)

        print(f"Added {path}")




    def add_directory(self, path: str):
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Directory {path} not found")
        if not full_path.is_dir():
            raise ValueError(f"{path} is not a directory")

        index = self.load_index()
        added_count = 0
        # recursively traverse the directory
        for file_path in full_path.rglob("*"):
            if file_path.is_file():
                if ".mygit" in file_path.parts:
                    continue

                # create & store blob object
                content = file_path.read_bytes()
                blob = Blob(content)
                blob_hash = self.store_object(blob)
                # update index
                rel_path = str(file_path.relative_to(self.path))
                index[rel_path] = blob_hash
                added_count += 1

        self.save_index(index)

        if added_count > 0:
            print(f"Added {added_count} files from directory {path}")
        else:
            print(f"Directory {path} already up to date")



    def add_path(self, path:str) -> None:
        full_path = self.path / path 

        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")

        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directory(path)
        else:
            raise ValueError(f"{path} is neither a file nor a directory")


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


    #init command
    add_parser = subparsers.add_parser("add", help="Add files and Directories to the staging area")

    add_parser.add_argument("paths", nargs="+", help="Files and Directories to add")
    
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
        elif args.command == "add":
            if not repo.git_dir.exists():
                print("Not a git directory")
                return
            for path in args.paths:
                repo.add_path(path)
    except Exception as e:
        print(f"Error: {e}") 
        sys.exit(1)

main()
