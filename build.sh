#!/bin/bash
echo "Building Genie application..."

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Install requirements if not already installed
pip install -r requirements.txt

# Check if user wants an HSBC build
HSBC_BUILD=false
if [ "$1" = "hsbc" ]; then
    echo "Building special HSBC environment version..."
    HSBC_BUILD=true
    
    # Generate the HSBC spec file using Python (same as Windows)
    python generate_spec.py
    
    # Build the HSBC version
    pyinstaller --clean genie-hsbc.spec
else
    # Build the regular executable
    pyinstaller --clean genie.spec
fi

# For Mac, create a proper .app bundle if it's not already done
if [ "$(uname)" = "Darwin" ]; then
    # Check if we need to sign the app
    if [ -n "$APPLE_DEVELOPER_ID" ]; then
        echo "Signing the application with Developer ID: $APPLE_DEVELOPER_ID"
        if [ "$HSBC_BUILD" = true ]; then
            codesign --force --options runtime --sign "$APPLE_DEVELOPER_ID" "dist/Genie-HSBC.app"
        else
            codesign --force --options runtime --sign "$APPLE_DEVELOPER_ID" "dist/Genie.app"
        fi
    fi
    
    # Create a DMG if the create_dmg tool is available
    if command -v create-dmg &> /dev/null; then
        echo "Creating DMG package..."
        if [ "$HSBC_BUILD" = true ]; then
            create-dmg --volname "Genie-HSBC" --volicon "src/assets/logo.icns" \
                       --window-pos 200 120 --window-size 600 400 \
                       --icon-size 100 --icon "Genie-HSBC.app" 175 190 \
                       --hide-extension "Genie-HSBC.app" --app-drop-link 425 190 \
                       "dist/Genie-HSBC.dmg" "dist/Genie-HSBC.app"
        else
            create-dmg --volname "Genie" --volicon "src/assets/logo.icns" \
                       --window-pos 200 120 --window-size 600 400 \
                       --icon-size 100 --icon "Genie.app" 175 190 \
                       --hide-extension "Genie.app" --app-drop-link 425 190 \
                       "dist/Genie.dmg" "dist/Genie.app"
        fi
    fi
fi

# Copy CLI wrapper script to dist folder
echo "Copying CLI wrapper script..."
cp secretgenie-cli.sh dist/secretgenie-cli.sh 2>/dev/null || true
chmod +x dist/secretgenie-cli.sh 2>/dev/null || true
echo "CLI wrapper script copied to dist folder."

echo "Build complete!"
if [ "$HSBC_BUILD" = true ]; then
    if [ "$(uname)" = "Darwin" ]; then
        echo "The HSBC version application can be found at dist/SecretGenie-HSBC.app"
        if [ -f "dist/SecretGenie-HSBC.dmg" ]; then
            echo "DMG installer created at dist/SecretGenie-HSBC.dmg"
        fi
    else
        echo "The HSBC version executable can be found at dist/SecretGenie-HSBC"
    fi
    echo "CLI wrapper: dist/secretgenie-cli.sh"
else
    if [ "$(uname)" = "Darwin" ]; then
        echo "The application can be found at dist/SecretGenie.app"
        if [ -f "dist/SecretGenie.dmg" ]; then
            echo "DMG installer created at dist/SecretGenie.dmg"
        fi
    else
        echo "The executable can be found in the dist folder."
    fi
    echo "CLI wrapper: dist/secretgenie-cli.sh"
fi 