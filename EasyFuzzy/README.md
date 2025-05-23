# 🔎 EasyFuzzy: Hacker-Friendly Smart Wrapper for FFUF

**EasyFuzzy** is a hacker-friendly, semi-automated wrapper for [`ffuf`](https://github.com/ffuf/ffuf) designed to make fuzzing more intuitive, adaptive, and efficient. 
Whether you're into directory busting, file extension fuzzing, or parameter discovery, this tool helps you reduce noise and focus on valuable results — all while staying in your terminal.

---

## ✨ Features

- 🔥 **Smart pre-fuzzing analysis** to recommend HTTP code, size, or word count filters
- ⚙️ **Auto-download of wordlists** from [SecLists](https://github.com/danielmiessler/SecLists)
- 🧠 **Interactive suggestions** when too many uniform responses are detected
- 💾 **Results organized** into timestamped directories
- 🧰 **Supports multiple fuzzing modes**:
  - `dir` — Directory and file discovery (`/FUZZ`)
  - `ext` — Extension brute-forcing (`page.FUZZ`)
  - `param` — Parameter fuzzing (`page.php?FUZZ=value`)

---

## 🧑‍💻 Usage

```bash
python3 EasyFuzzy.py --mode <dir|ext|param> --url <target_url>
```
---
## 🔍 Examples

- Directory discovery:    python3 EasyFuzzy.py --mode dir --url http://target.com/
- File extension fuzzing: python3 EasyFuzzy.py --mode ext --url http://target.com/index 
- Parameter fuzzing:      python3 EasyFuzzy.py --mode param --url http://target.com/page.php

---

## 📦 Wordlist Handling

The tool will prompt you to:
- Use an existing wordlist (found using locate) or
- Automatically download the appropriate SecLists wordlist.
All wordlists are cached locally in results/wordlists/.

---
## 🧠 Smart Filtering Suggestions

During the pre-fuzzing stage (first 300 entries), if uniform responses (e.g., all HTTP 200) are detected, the tool will offer to apply one or more filters:

    --fc (Filter by status code)

    --fs (Filter by response size)

    --fw (Filter by word count)

This helps reduce noise and uncover more meaningful results faster.

---
## 📁 Output

All results are saved in timestamped folders under the results/ directory:
- sample_result.json → Pre-analysis
- final_result.json → Full fuzzing output
