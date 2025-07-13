import sys
import subprocess


def main():
    cmd = [sys.executable, "-m", "poetry", "clovers"] + sys.argv[1:]
    try:
        subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr, check=True)
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败 (退出码 {e.returncode})", file=sys.stderr)
        return e.returncode
    except FileNotFoundError:
        print("错误: 未找到 poetry 命令，请确保已安装 poetry", file=sys.stderr)
        return 127
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return 1
