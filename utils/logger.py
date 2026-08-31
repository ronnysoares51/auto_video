"""
Logger and Console UI Module.
Built using Python Standard Library with ANSI colors and Unicode box styling.
Zero external dependencies required (No import errors).
"""
import sys
import datetime
from typing import List, Dict, Any

# ANSI Color and Style codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

def _get_timestamp() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")

def log_info(message: str):
    """Logs an informational message in blue."""
    print(f"{BOLD}{BLUE}[{_get_timestamp()}] ℹ️  {message}{RESET}")

def log_success(message: str):
    """Logs a success message in green."""
    print(f"{BOLD}{GREEN}[{_get_timestamp()}] ✅ {message}{RESET}")

def log_warning(message: str):
    """Logs a warning message in yellow."""
    print(f"{BOLD}{YELLOW}[{_get_timestamp()}] ⚠️  {message}{RESET}")

def log_error(message: str):
    """Logs an error message in red."""
    print(f"{BOLD}{RED}[{_get_timestamp()}] ❌ {message}{RESET}")

def print_banner(title: str, subtitle: str = ""):
    """Displays a stylized header banner with Unicode borders."""
    width = 68
    print()
    print(f"{CYAN}╭{'─' * (width - 2)}╮{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}{CYAN}{title.center(width - 4)}{RESET} {CYAN}│{RESET}")
    if subtitle:
        print(f"{CYAN}│{RESET} {DIM}{subtitle.center(width - 4)}{RESET} {CYAN}│{RESET}")
    print(f"{CYAN}╰{'─' * (width - 2)}╯{RESET}")
    print()

def log_pause_alert(platform_name: str, login_url: str):
    """Displays a prominent red alert box when manual login is required."""
    timestamp = _get_timestamp()
    width = 72
    
    print()
    print(f"{RED}{BOLD}╭─ 🚨 ACTION REQUIRED [{timestamp}] {'─' * (width - 29)}╮{RESET}")
    print(f"{RED}│{RESET} {BOLD}{RED}SESSION LOST / LOGIN REQUIRED FOR: {platform_name.upper()}{RESET}")
    print(f"{RED}│{RESET} {CYAN}URL: {login_url}{RESET}")
    print(f"{RED}│{RESET}")
    print(f"{RED}│{RESET} {YELLOW}1. Switch to the opened browser window.{RESET}")
    print(f"{RED}│{RESET} {YELLOW}2. Complete the login / verification manually.{RESET}")
    print(f"{RED}│{RESET} {BOLD}{GREEN}3. Once logged in, return to this terminal and press [ENTER].{RESET}")
    print(f"{RED}╰{'─' * (width - 2)}╯{RESET}")
    print()

def print_summary_table(rows: List[Dict[str, Any]] = None, results: List[Dict[str, Any]] = None, **kwargs):
    """Renders a formatted execution summary table."""
    data = rows if rows is not None else results
    if not data:
        return

    print()
    print(f"{BOLD}{GREEN}📊 EXECUTION SUMMARY{RESET}")
    print("┌──────────┬─────────────────────────────────────┬────────────┬────────────┬────────────┐")
    print(f"│ {BOLD}Task ID{RESET}  │ {BOLD}Prompt{RESET}                              │ {BOLD}Generation{RESET} │ {BOLD}Upload{RESET}     │ {BOLD}Status{RESET}     │")
    print("├──────────┼─────────────────────────────────────┼────────────┼────────────┼────────────┤")

    for r in data:
        task_id = str(r.get("task_id", ""))[:8].center(8)
        raw_prompt = str(r.get("prompt", ""))
        prompt_snip = (raw_prompt[:32] + "...") if len(raw_prompt) > 35 else raw_prompt
        prompt_padded = f"{prompt_snip:<35}"
        
        gen = str(r.get("gen_status", ""))[:10].center(10)
        upload = str(r.get("upload_status", ""))[:10].center(10)
        
        status_val = str(r.get("final_status", ""))
        if "SUCCESS" in status_val or "Done" in status_val:
            status_str = f"{GREEN}{status_val[:10].center(10)}{RESET}"
        elif "FAIL" in status_val:
            status_str = f"{RED}{status_val[:10].center(10)}{RESET}"
        else:
            status_str = f"{YELLOW}{status_val[:10].center(10)}{RESET}"

        print(f"│ {task_id} │ {prompt_padded} │ {gen} │ {upload} │ {status_str} │")

    print("└──────────┴─────────────────────────────────────┴────────────┴────────────┴────────────┘")
    print()
