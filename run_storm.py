#!/usr/bin/env python3
"""
Standalone script to run Storm without installation
"""

import sys
import os
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Print a nice banner
print(rf"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║ {Fore.YELLOW}  _____ _______ ____  _____  __  __ {Fore.CYAN}                      ║
║ {Fore.YELLOW} / ____|__   __/ __ \|  __ \|  \/  |{Fore.CYAN}                      ║
║ {Fore.YELLOW}| (___    | | | |  | | |__) | \  / |{Fore.CYAN}                      ║
║ {Fore.YELLOW} \___ \   | | | |  | |  _  /| |\/| |{Fore.CYAN}                      ║
║ {Fore.YELLOW} ____) |  | | | |__| | | \ \| |  | |{Fore.CYAN}                      ║
║ {Fore.YELLOW}|_____/   |_|  \____/|_|  \_\_|  |_|{Fore.CYAN}                      ║
║                                                           ║
║ {Fore.GREEN}RPC Flood Testing Tool{Fore.CYAN}                                    ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the main function from the storm package
from storm.__main__ import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Storm testing stopped by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1) 
