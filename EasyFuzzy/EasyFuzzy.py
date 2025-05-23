import argparse
import subprocess
import os
import json
from datetime import datetime
import urllib.request

WORDLISTS = {
    "dir": {
        "filename": "directory-list-lowercase-2.3-medium.txt",
        "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/directory-list-lowercase-2.3-medium.txt",
        "example_url": "http://target/FUZZ"
    },
    "ext": {
        "filename": "web-extensions.txt",
        "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/web-extensions.txt",
        "example_url": "http://target/page.FUZZ"
    },
    "param": {
        "filename": "burp-parameter-names.txt",
        "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/burp-parameter-names.txt",
        "example_url": "http://target/page.php?FUZZ=value"
    }
}

def create_results_dir():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_dir = os.path.join("results", now)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def analyze_sample_and_prompt_filter(sample_json, mode):
    if mode != "dir":
        return []

    try:
        with open(sample_json, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Erreur lecture JSON de l'échantillon : {e}")
        return []

    results = data.get("results", [])
    if not results:
        return []

    status_list = [r["status"] for r in results[:300]]
    if len(set(status_list)) == 1:
        print("\n[!] Beaucoup de réponses identiques détectées parmi les 300 premiers résultats.")
        print("Souhaitez-vous appliquer un filtre ?")
        print("  [1] Filtrer par code HTTP (--fc)")
        print("  [2] Filtrer par taille (--fs)")
        print("  [3] Filtrer par nombre de mots (--fw)")
        print("  [0] Continuer sans filtrer")

        filters = []
        while True:
            choice = input("> ").strip()
            if choice == "1":
                val = input("Code(s) HTTP à exclure (ex: 200,403):\n> ").strip()
                filters.append(("--fc", val))
                break
            elif choice == "2":
                val = input("Taille(s) à exclure (--fs) :\n> ").strip()
                filters.append(("--fs", val))
                break
            elif choice == "3":
                val = input("Nombre de mots à exclure (--fw) :\n> ").strip()
                filters.append(("--fw", val))
                break
            elif choice == "0":
                break
            else:
                print("[!] Choix invalide.")
        return filters
    return []

def build_ffuf_cmd(url, wordlist, output, mode):
    if mode == "dir":
        ffuf_url = f"{url.rstrip('/')}/FUZZ"
    elif mode == "ext":
        if url.endswith('.'):
            ffuf_url = f"{url}FUZZ"
        elif url.endswith('/'):
            ffuf_url = f"{url}indexFUZZ"
        else:
            ffuf_url = f"{url}FUZZ"
    elif mode == "param":
        ffuf_url = f"{url}?FUZZ"
    else:
        raise ValueError(f"Mode inconnu : {mode}")

    cmd = [
        "ffuf",
        "-u", ffuf_url,
        "-w", wordlist,
        "-o", output,
        "-of", "json"
    ]
    return cmd

def get_wordlist_path(mode):
    wl = WORDLISTS[mode]
    expected_filename = wl["filename"]
    print(f"\n[?] Possédez-vous déjà la wordlist '{expected_filename}' ? (o/n)")
    choice = input("> ").strip().lower()

    if choice == 'o':
        found_paths = []
        try:
            locate_output = subprocess.check_output(["locate", expected_filename], text=True)
            found_paths = [line.strip() for line in locate_output.splitlines() if line.strip()]
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        if found_paths:
            for i, path in enumerate(found_paths, 1):
                print(f"  [{i}] {path}")
            print("  [0] Entrer un chemin manuellement")
            try:
                idx = int(input("\nChoisissez une option :\n> "))
                if idx == 0:
                    path = input("Chemin complet : ").strip()
                elif 1 <= idx <= len(found_paths):
                    path = found_paths[idx - 1]
                else:
                    print("[!] Choix invalide.")
                    return None
            except ValueError:
                return None
        else:
            path = input("Chemin complet de votre wordlist : ").strip()

        if not os.path.isfile(path):
            return None
        return path

    wl_dir = os.path.join("results", "wordlists")
    os.makedirs(wl_dir, exist_ok=True)
    local_path = os.path.join(wl_dir, expected_filename)
    if not os.path.exists(local_path):
        print(f"[*] Téléchargement de {expected_filename}...")
        try:
            urllib.request.urlretrieve(wl["url"], local_path)
        except Exception as e:
            print(f"[!] Erreur téléchargement : {e}")
            return None
    return local_path

def run_ffuf(cmd):
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print("[!] Erreur ffuf.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Wrapper Python pour ffuf")
    parser.add_argument("--mode", choices=["dir", "ext", "param"], required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    result_dir = create_results_dir()
    wordlist_path = get_wordlist_path(args.mode)
    if not wordlist_path:
        return

    sample_path = os.path.join(result_dir, "sample_wordlist.txt")
    with open(wordlist_path, "r") as full, open(sample_path, "w") as sample:
        for _, line in zip(range(300), full):
            sample.write(line)

    sample_json = os.path.join(result_dir, "sample_result.json")
    sample_cmd = build_ffuf_cmd(args.url, sample_path, sample_json, args.mode)
    print(f"[*] Pré-analyse avec les 100 premières entrées : {' '.join(sample_cmd)}")
    if not run_ffuf(sample_cmd):
        return

    filters = analyze_sample_and_prompt_filter(sample_json, args.mode)
    final_json = os.path.join(result_dir, "final_result.json")
    final_cmd = build_ffuf_cmd(args.url, wordlist_path, final_json, args.mode)
    for flag, val in filters:
        final_cmd.extend([flag, val])

    print("[*] Lancement final avec{} filtre{}.".format("" if not filters else " les", "" if len(filters) <= 1 else "s"))
    print(f"[*] Lancement de ffuf : {' '.join(final_cmd)}")
    run_ffuf(final_cmd)

if __name__ == "__main__":
    main()
