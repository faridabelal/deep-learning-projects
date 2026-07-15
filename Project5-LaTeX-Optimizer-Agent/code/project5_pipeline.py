"""
Project 5: LaTeX Project Compression Pipeline with API-Based Agent Step

This script documents and automates the main steps used to optimize a LaTeX
project by reducing file size while preserving visual quality.

Pipeline structure:
1. Analysis Agent: inspect project size and identify large files.
2. Decision Agent: use file references and size data to decide what can be removed/compressed.
3. Action Agent: move unused files and compress images.
4. Verification Agent: verify final size and summarize visual-quality safeguards.
5. API Agent: use OpenRouter to review the optimization strategy and produce a short audit log.


"""

from pathlib import Path
import os
import re
import shutil
import subprocess
import zipfile
import json
import urllib.request
import urllib.error
from datetime import datetime


PROJECT_ROOT = Path.home() / "Desktop" / "Project5"
LATEX_PROJECT = PROJECT_ROOT / "optimized_latex_project"
UNUSED_DIR = PROJECT_ROOT / "unused_figures_removed"
OUTPUT_ZIP = PROJECT_ROOT / "optimized_latex_source.zip"
FINAL_PDF = PROJECT_ROOT / "final_compiled_pdf.pdf"
REPORT_DIR = PROJECT_ROOT / "report"
API_LOG = REPORT_DIR / "api_agent_log.md"


OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")


def get_size_mb(path: Path) -> float:
    """Return file or folder size in MB."""
    if not path.exists():
        return 0.0

    if path.is_file():
        return path.stat().st_size / (1024 * 1024)

    total = 0
    for root, _, files in os.walk(path):
        for file in files:
            fp = Path(root) / file
            total += fp.stat().st_size
    return total / (1024 * 1024)


def list_largest_files(folder: Path, n: int = 30):
    """List the largest files in the project."""
    files = []
    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            path = Path(root) / filename
            files.append((path, get_size_mb(path)))

    files.sort(key=lambda x: x[1], reverse=True)

    print(f"\nTop {n} largest files:")
    for path, size in files[:n]:
        print(f"{size:8.2f} MB  {path.relative_to(folder)}")

    return files[:n]


def find_used_graphics(folder: Path):
    """
    Find image files referenced by active \\includegraphics commands.
    Lines starting with % are treated as comments and ignored.
    """
    used = set()
    pattern = re.compile(r"\\includegraphics(?:\[.*?\])?\{(.+?)\}")

    for tex_file in folder.rglob("*.tex"):
        with open(tex_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                stripped = line.strip()

                if stripped.startswith("%"):
                    continue

                match = pattern.search(line)
                if match:
                    image_path = match.group(1)
                    used.add(image_path)

    return used


def move_unused_jpgs(folder: Path, unused_dir: Path):
    """
    Move JPG/PNG files that are not referenced by active includegraphics commands.
    This is safer than deleting because moved files can be restored.
    """
    unused_dir.mkdir(exist_ok=True)

    used_graphics = find_used_graphics(folder)
    print("\nUsed graphics found in active LaTeX source:")
    for item in sorted(used_graphics):
        print("  ", item)

    moved_count = 0

    for img in folder.rglob("*"):
        if img.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        rel = str(img.relative_to(folder))

        if rel not in used_graphics:
            destination = unused_dir / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(img), str(destination))
            moved_count += 1

    print(f"\nMoved {moved_count} unused image files to {unused_dir}")


def compress_jpgs_with_sips(folder: Path, max_dimension: int = 1800, quality: int = 75):
    """
    Compress JPG images using macOS sips.

    max_dimension limits the largest image side.
    quality controls JPEG quality.

    These settings were chosen to reduce file size while keeping figures readable.
    """
    jpgs = list(folder.rglob("*.jpg")) + list(folder.rglob("*.jpeg"))

    print(f"\nCompressing {len(jpgs)} JPG images...")

    for img in jpgs:
        cmd = [
            "sips",
            "--resampleHeightWidthMax",
            str(max_dimension),
            "-s",
            "format",
            "jpeg",
            "-s",
            "formatOptions",
            str(quality),
            str(img),
            "--out",
            str(img),
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("Image compression complete.")


def create_zip(source_folder: Path, output_zip: Path):
    """Create a zip file from the optimized LaTeX project."""
    if output_zip.exists():
        output_zip.unlink()

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for path in source_folder.rglob("*"):
            if path.is_file():
                zipf.write(path, path.relative_to(source_folder))

    print(f"\nCreated zip: {output_zip}")
    print(f"Zip size: {get_size_mb(output_zip):.2f} MB")


def collect_project_summary():
    """Collect a compact project summary to send to the API agent."""
    used_graphics = sorted(find_used_graphics(LATEX_PROJECT))
    largest_files = list_largest_files(LATEX_PROJECT, n=15)

    summary = {
        "project_goal": "Optimize a LaTeX project to reduce size while preserving visual quality.",
        "requirements": {
            "final_submission_zip": "< 50 MB",
            "compiled_pdf": "< 30 MB",
            "quality_constraint": "Do not minimize size at all costs; figures must remain visually acceptable.",
        },
        "measured_results": {
            "optimized_latex_project_mb": round(get_size_mb(LATEX_PROJECT), 2),
            "final_pdf_mb": round(get_size_mb(FINAL_PDF), 2),
            "optimized_source_zip_mb": round(get_size_mb(OUTPUT_ZIP), 2),
        },
        "used_graphics_count": len(used_graphics),
        "used_graphics": used_graphics,
        "largest_files": [
            {
                "file": str(path.relative_to(LATEX_PROJECT)),
                "size_mb": round(size, 2),
            }
            for path, size in largest_files
        ],
        "actions_taken": [
            "Removed accidental nested duplicate project folder.",
            "Removed backup folder from optimized LaTeX source.",
            "Moved unused figure versions outside the optimized source project.",
            "Compressed remaining JPG images using macOS sips.",
            "Compiled the optimized project on Overleaf.",
            "Manually inspected the PDF for missing figures, layout corruption, and obvious blur.",
        ],
    }

    return summary


def call_openrouter_decision_agent(summary: dict):
    """
    Call OpenRouter to get a short agent-style review of the compression strategy.
    The API key must be stored in the OPENROUTER_API_KEY environment variable.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("\nOPENROUTER_API_KEY is not set. Skipping API agent step.")
        return None

    prompt = f"""
You are an AI verification agent for a LaTeX compression project.

Review the following project summary and provide:
1. A short assessment of whether the optimization satisfies the requirements.
2. A judgment on whether the strategy balances compression and visual quality.
3. Any risks or limitations.
4. A concise recommendation for the final report.

Project summary:
{json.dumps(summary, indent=2)}
"""

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a careful AI agent that audits document optimization pipelines.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "max_tokens": 700,
    }

    request = urllib.request.Request(
        url="https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "Project 5 LaTeX Compression Pipeline",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        agent_message = result["choices"][0]["message"]["content"]
        return agent_message

    except urllib.error.HTTPError as e:
        error_text = e.read().decode("utf-8", errors="ignore")
        print(f"\nOpenRouter HTTP error: {e.code}")
        print(error_text)
        return None

    except Exception as e:
        print(f"\nOpenRouter API call failed: {e}")
        return None


def save_api_log(summary: dict, agent_response: str):
    """Save the API agent response as a small markdown log for the report folder."""
    REPORT_DIR.mkdir(exist_ok=True)

    with open(API_LOG, "w", encoding="utf-8") as f:
        f.write("# API Agent Log\n\n")
        f.write(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n\n")
        f.write(f"Model: `{OPENROUTER_MODEL}`\n\n")

        f.write("## Project Summary Sent to API Agent\n\n")
        f.write("```json\n")
        f.write(json.dumps(summary, indent=2))
        f.write("\n```\n\n")

        f.write("## API Agent Response\n\n")
        f.write(agent_response)

    print(f"\nSaved API agent log to: {API_LOG}")


def main():
    print("Project 5 LaTeX Compression Pipeline")
    print("------------------------------------")

    print(f"Project folder: {LATEX_PROJECT}")
    print(f"Optimized LaTeX project size: {get_size_mb(LATEX_PROJECT):.2f} MB")
    print(f"Final compiled PDF size: {get_size_mb(FINAL_PDF):.2f} MB")
    print(f"Optimized source zip size: {get_size_mb(OUTPUT_ZIP):.2f} MB")

    used_graphics = find_used_graphics(LATEX_PROJECT)
    print("\nActive LaTeX image references:")
    for graphic in sorted(used_graphics):
        print("  ", graphic)

    summary = collect_project_summary()

    print("\nRunning API-based decision/verification agent...")
    agent_response = call_openrouter_decision_agent(summary)

    if agent_response:
        print("\nAPI Agent Response:")
        print("-------------------")
        print(agent_response)
        save_api_log(summary, agent_response)
    else:
        print("\nNo API agent response was saved.")

    print(f"\nFinal optimized project size: {get_size_mb(LATEX_PROJECT):.2f} MB")


if __name__ == "__main__":
    main()