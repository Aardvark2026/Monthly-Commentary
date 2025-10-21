import json, subprocess, sys, tempfile, os

def run_llama(system, user, model_path, max_tokens=600, temp=0.7):
    exe = os.path.abspath("commentary/llama.cpp/main")
    if not os.path.exists(exe):
        raise SystemExit("llama.cpp not built. Run: make setup")

    cmd = [
        exe,
        "-m", os.path.abspath(model_path),
        "-n", str(max_tokens),
        "--temp", str(temp),
        "-p", user,
        "--in-prefix", "",
        "--in-suffix", "",
        "-s", system
    ]
    return subprocess.check_output(cmd, text=True)

if __name__ == "__main__":
    system = sys.argv[1]
    user = sys.argv[2]
    model = sys.argv[3]
    print(run_llama(system, user, model))