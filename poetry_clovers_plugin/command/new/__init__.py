import sys
import subprocess
from pathlib import Path
from cleo.helpers import argument, option
from poetry.console.commands.command import Command
from poetry.pyproject.toml import PyProjectTOML

TEMPLATE_DIR = Path(__file__).parent / "template"
TEMPLATE_PLUGIN_DIR = TEMPLATE_DIR / "plugin"
TEMPLATE_ADAPTER_DIR = TEMPLATE_DIR / "adapter"
TEMPLATE_CLIENT_DIR = TEMPLATE_DIR / "client"


class CloversNewCommand(Command):
    name = "clovers new"
    description = "Create a new clovers project"
    arguments = [
        argument("type", optional=False, description="Type of template, can be one of [plugin,adapter,client] or not"),
        argument("name", optional=True, description="Add packages to the project"),
    ]
    options = [
        option("namespace", None, "create a namespace package project", flag=False),
        option("flat", None, "use flat layout"),
        option("pydantic", None, "use pydantic to validate config"),
    ]

    def arg_name(self) -> str:
        name: str = self.argument("name") or self.argument("type")
        name = name.replace("_", "-")
        if not name.startswith("clovers-"):
            name = f"clovers-{name}"
        return name

    def new_project(self, path: str) -> int:
        args = f"args {path} --python >=3.12,<4.0.0"
        if namespace := self.option("namespace"):
            args += f" --name {namespace}"
        if self.option("flat"):
            args = "--flat " + args
        return_code = self.call(f"new", args)
        if return_code != 0:
            return return_code
        pyproject = PyProjectTOML(Path.cwd() / path / "pyproject.toml")
        pyproject.data.setdefault("project", {})["name"] = path
        pyproject.save()
        self.line(f"Adding dependencies to the {path}...", style="info")
        command = [sys.executable, "-m", "poetry", "add", "clovers>=0.4.6"]
        if self.option("pydantic"):
            command.append("pydantic>=2.0")
        else:
            self.line("If you don't need `pydantic`, please modify the config.py later", style="comment")
        try:
            subprocess.run(command, cwd=path, check=True)
        except subprocess.CalledProcessError as e:
            self.line(f"Return code: {e.returncode}", "error")
            self.line(f"Error Output:\n{e.stderr}", "error")
            return e.returncode
        return 0

    def copy_template(self, path: str, template_path: Path) -> int:
        src_path = Path(path)
        if (check_src_path := src_path.joinpath("src")).exists():
            src_path = check_src_path
        src_path = src_path / path.replace("-", "_")
        import shutil

        try:
            shutil.copytree(template_path, src_path, dirs_exist_ok=True)
        except Exception as e:
            self.line(f"copy template failed: {e}", "error")
            return 1
        return 0

    def handle(self) -> int:
        template_type: str = self.argument("type")
        if template_type == "plugin":
            return self.plugin_handle()
        elif template_type == "adapter":
            return self.adapter_handle()
        elif template_type == "client":
            return self.client_handle()
        elif self.argument("name") is None:
            return self.none_handle()
        self.line(f'Invalid type "{template_type}"', style="error")
        return 1

    def none_handle(self) -> int:
        name = self.arg_name()
        return self.new_project(name)

    def client_handle(self) -> int:
        name = self.arg_name()
        path = Path(name)
        if path.exists():
            self.line(f'"{name}" already exists', style="error")
            return 1
        path.mkdir(parents=True)
        import shutil

        try:
            shutil.copytree(TEMPLATE_CLIENT_DIR, path, dirs_exist_ok=True)
        except Exception as e:
            self.line(f"copy template failed: {e}", "error")
            return 1

        choices = ["onebot", "console", "qq"]
        client = self.ask(f"please choose a client {choices}", default="onebot")
        row = choices.index(client)
        file = path / "bot.py"
        with file.open("r") as f:
            lines = f.readlines()
        lines[row] = lines[row][2:]
        with file.open("w") as f:
            f.writelines(lines)
        try:
            subprocess.run([sys.executable, "-m", "poetry", "init", "--python", ">=3.12,<4.0.0"], cwd=name, check=True)
            pyproject = PyProjectTOML(Path.cwd() / path / "pyproject.toml")
            pyproject.data.setdefault("tool", {}).setdefault("poetry", {})["package-mode"] = False
            pyproject.save()
            subprocess.run([sys.executable, "-m", "poetry", "add", f"clovers_client[{client}]"], cwd=name, check=True)
        except subprocess.CalledProcessError as e:
            self.line(f"Return code: {e.returncode}", "error")
            self.line(f"Error Output:\n{e.stderr}", "error")
            return e.returncode
        except Exception as e:
            self.line(f"Error: {e}", "error")
            return 1
        return 0

    def plugin_handle(self) -> int:
        name = self.arg_name()
        return_code = self.new_project(name)
        if return_code != 0:
            return return_code
        return self.copy_template(name, TEMPLATE_PLUGIN_DIR)

    def adapter_handle(self) -> int:
        name = self.arg_name()
        return_code = self.new_project(name)
        if return_code != 0:
            return return_code
        return self.copy_template(name, TEMPLATE_ADAPTER_DIR)
