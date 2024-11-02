import click
from pathlib import Path
from importlib.resources import as_file, files


@click.command(help="Generate a script to run the conduit with default settings")
@click.argument("filepath", type=click.Path(writable=True))
def generate_script(filepath: str):
    path = Path(filepath)
    script_context = as_file(files("attpc_conduit").joinpath("run_conduit.py"))
    if script_context is None:
        print("Could not retrieve the script to generate!")
        return
    with script_context as script_path:
        with open(script_path, "r") as script_file:
            with open(path, "w") as file:
                script_lines = script_file.readlines()[1:]
                file.writelines(["from attpc_conduit import (\n"])
                file.writelines(script_lines)


if __name__ == "__main__":
    generate_script()
