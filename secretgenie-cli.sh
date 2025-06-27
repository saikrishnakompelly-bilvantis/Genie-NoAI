#!/bin/bash

# SecretGenie Command Line Interface Wrapper (Shell Script)
# This script provides command-line interface for SecretGenie on Unix-like systems

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if we're on macOS and look for the .app bundle
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [[ -d "$SCRIPT_DIR/SecretGenie.app" ]]; then
        SECRETGENIE_EXE="$SCRIPT_DIR/SecretGenie.app/Contents/MacOS/SecretGenie"
    elif [[ -f "$SCRIPT_DIR/SecretGenie" ]]; then
        SECRETGENIE_EXE="$SCRIPT_DIR/SecretGenie"
    else
        echo -e "${RED}ERROR: SecretGenie.app not found in $SCRIPT_DIR${NC}"
        echo -e "${RED}Please ensure this script is in the same directory as SecretGenie.app${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi
else
    # Linux - look for executable
    if [[ -f "$SCRIPT_DIR/SecretGenie" ]]; then
        SECRETGENIE_EXE="$SCRIPT_DIR/SecretGenie"
    else
        echo -e "${RED}ERROR: SecretGenie executable not found in $SCRIPT_DIR${NC}"
        echo -e "${RED}Please ensure this script is in the same directory as the SecretGenie executable${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Show usage if no arguments provided
if [[ $# -eq 0 ]]; then
    echo -e "${CYAN}SecretGenie Command Line Interface${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  $0 /install      - Install SecretGenie hooks"
    echo -e "  $0 /uninstall    - Uninstall SecretGenie hooks"
    echo -e "  $0 --help        - Show help"
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${GRAY}To run the GUI version, double-click SecretGenie.app directly${NC}"
    else
        echo -e "${GRAY}To run the GUI version, double-click the SecretGenie executable directly${NC}"
    fi
    read -p "Press Enter to exit..."
    exit 0
fi

# Check for command-line arguments
case "$1" in
    "/install"|"--install"|"/uninstall"|"--uninstall"|"--help"|"-h")
        echo -e "${GREEN}Running SecretGenie in command-line mode...${NC}"
        echo ""
        
        # Run the executable with all arguments
        "$SECRETGENIE_EXE" "$@"
        EXIT_CODE=$?
        
        # Show completion message
        echo ""
        if [[ $EXIT_CODE -eq 0 ]]; then
            echo -e "${GREEN}Command completed successfully.${NC}"
        else
            echo -e "${RED}Command failed with exit code $EXIT_CODE.${NC}"
        fi
        
        # Pause to keep terminal open
        echo ""
        read -p "Press Enter to close this window..."
        
        exit $EXIT_CODE
        ;;
    *)
        # For other arguments or GUI mode, just start the GUI
        echo -e "${GREEN}Starting SecretGenie in GUI mode...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open -a "$SCRIPT_DIR/SecretGenie.app" --args "$@"
        else
            "$SECRETGENIE_EXE" "$@" &
        fi
        exit 0
        ;;
esac 