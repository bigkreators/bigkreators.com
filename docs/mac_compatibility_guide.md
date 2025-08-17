# Mac Compatibility Guide for KONTRIB Token Setup

## Quick Answer: Yes! ✅

The KONTRIB token setup scripts **can run on Mac**, but there are some Mac-specific considerations. I've created an optimized version for macOS.

## Mac-Specific Differences

### 1. Package Manager
**Linux:** Uses `apt-get` or `yum`
**Mac:** Uses **Homebrew** (which the script will install automatically)

### 2. Python Installation
**Linux:** Usually comes with Python
**Mac:** May need Python 3.8+ installation via Homebrew

### 3. Architecture Support
- ✅ **Intel Macs (x86_64)**: Fully supported
- ✅ **Apple Silicon (M1/M2/M3)**: Fully supported
- ✅ **Automatic detection**: Script detects your architecture

### 4. Shell Differences
**Linux:** Usually bash
**Mac:** Default is zsh (macOS Catalina+), script handles both

## What the Mac Script Does

### Automatic Installation
1. **Homebrew** - Mac package manager
2. **Python 3.8+** - Required for FastAPI
3. **Node.js 16+** - For CLI tools
4. **Rust/Cargo** - For Solana tools
5. **Solana CLI** - Blockchain tools
6. **SPL Token CLI** - Token management

### Architecture Detection
```bash
# Detects your Mac type
Intel Mac: /usr/local/bin/brew
Apple Silicon: /opt/homebrew/bin/brew
```

### Shell Configuration
```bash
# Adds tools to your PATH in the right profile
~/.zshrc (default on newer Macs)
~/.bash_profile (if using bash)
```

## How to Use on Mac

### Option 1: Use the Mac-Optimized Script
```bash
# Download and run the Mac version
curl -o setup-mac.sh [script-url]
chmod +x setup-mac.sh
./setup-mac.sh
```

### Option 2: Adapt Existing Scripts
If you have the Linux scripts, make these changes:

**Replace package manager commands:**
```bash
# Change from:
sudo apt-get install python3-pip

# To:
brew install python3
```

**Use correct Python command:**
```bash
# Change from:
python -m venv venv

# To:
python3 -m venv venv
```

**Update PATH correctly:**
```bash
# Add to ~/.zshrc instead of ~/.bashrc
echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.zshrc
```

## Manual Mac Setup (if needed)

### Step 1: Install Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Dependencies
```bash
# Essential tools
brew install python3 node rust

# Optional: MongoDB (or use Atlas)
brew tap mongodb/brew
brew install mongodb-community
```

### Step 3: Install Solana Tools
```bash
# Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/v1.18.4/install)"

# SPL Token CLI
cargo install spl-token-cli
```

### Step 4: Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Common Mac Issues & Solutions

### Issue 1: Command Not Found
**Problem:** `command not found: solana`
**Solution:**
```bash
# Add to PATH manually
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

# Make permanent
echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Issue 2: Python Version
**Problem:** Using system Python (often 2.7)
**Solution:**
```bash
# Always use python3 explicitly
python3 --version  # Should be 3.8+
python3 -m venv venv
```

### Issue 3: Homebrew Not in PATH (Apple Silicon)
**Problem:** Homebrew commands not found on M1/M2 Macs
**Solution:**
```bash
# Add Homebrew to PATH
eval "$(/opt/homebrew/bin/brew shellenv)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
```

### Issue 4: Rust/Cargo Not Found
**Problem:** `cargo: command not found`
**Solution:**
```bash
# Add Rust to PATH
source ~/.cargo/env
echo 'source ~/.cargo/env' >> ~/.zshrc
```

### Issue 5: Permission Issues
**Problem:** Permission denied errors
**Solution:**
```bash
# Don't use sudo with Homebrew
brew install package_name

# For npm packages, use prefix
npm config set prefix ~/.npm-global
export PATH=~/.npm-global/bin:$PATH
```

## Mac Performance Notes

### Apple Silicon Advantages
- ✅ **Faster compilation** - Rust/Solana tools build quickly
- ✅ **Better battery life** - Development doesn't drain battery
- ✅ **Native ARM binaries** - Most tools now have ARM versions

### Intel Mac Considerations
- ✅ **Rosetta compatibility** - ARM binaries work via translation
- ⚠️ **Slightly slower** - Some tools may run via emulation
- ✅ **Full compatibility** - All Solana tools work perfectly

## Recommended Mac Workflow

### Development Setup
```bash
# 1. Run the Mac setup script
./setup-mac.sh

# 2. Activate Python environment
source venv/bin/activate

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your MongoDB Atlas connection

# 4. Run database migration
python migrate_database.py

# 5. Create KONTRIB token
python create_kontrib_token.py

# 6. Start development server
uvicorn main:app --reload
```

### Daily Development
```bash
# Always activate the virtual environment first
cd your-project-directory
source venv/bin/activate

# Then run your development commands
python migrate_database.py
uvicorn main:app --reload
```

## MongoDB on Mac

### Option 1: Use MongoDB Atlas (Recommended)
- ✅ **No local installation needed**
- ✅ **Works perfectly with Mac**
- ✅ **Same as production environment**

### Option 2: Local MongoDB
```bash
# Install via Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb/brew/mongodb-community

# Stop MongoDB
brew services stop mongodb/brew/mongodb-community
```

## Testing on Mac

```bash
# Test Solana tools
solana --version
spl-token --version

# Test Python environment
python3 --version
pip --version

# Test your KONTRIB setup
python test_kontrib_integration.py
```

## Summary

✅ **Yes, everything works on Mac!**
- Intel and Apple Silicon both supported
- Mac-optimized script handles all differences
- Same functionality as Linux version
- Often performs better than Linux equivalents

The main differences are just using Homebrew instead of apt-get and ensuring correct Python/shell configurations. The Mac script handles all of this automatically!