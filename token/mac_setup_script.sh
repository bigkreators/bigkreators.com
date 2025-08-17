#!/bin/bash

# KONTRIB Token Setup Script for macOS
# Compatible with Intel and Apple Silicon Macs

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_section() {
    echo -e "\n${YELLOW}==============================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}==============================================${NC}\n"
}

check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Detect Mac architecture
detect_architecture() {
    local arch=$(uname -m)
    if [[ "$arch" == "arm64" ]]; then
        echo "apple_silicon"
    elif [[ "$arch" == "x86_64" ]]; then
        echo "intel"
    else
        echo "unknown"
    fi
}

# Check and install Homebrew
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        print_info "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH based on architecture
        local arch=$(detect_architecture)
        if [[ "$arch" == "apple_silicon" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        check_success
    else
        print_success "Homebrew already installed"
    fi
}

# Check and install Python 3
install_python() {
    if ! command -v python3 &> /dev/null; then
        print_info "Installing Python 3 via Homebrew..."
        brew install python3
        check_success
    else
        local python_version=$(python3 --version | cut -d' ' -f2)
        print_success "Python 3 found: $python_version"
        
        # Check if version is 3.8+
        local major=$(echo $python_version | cut -d. -f1)
        local minor=$(echo $python_version | cut -d. -f2)
        if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 8 ]]; then
            print_error "Python 3.8+ required. Installing latest Python..."
            brew install python3
            check_success
        fi
    fi
}

# Check and install Node.js
install_nodejs() {
    if ! command -v node &> /dev/null; then
        print_info "Installing Node.js via Homebrew..."
        brew install node
        check_success
    else
        local node_version=$(node --version)
        print_success "Node.js found: $node_version"
        
        # Check if version is 16+
        local major=$(echo $node_version | sed 's/v//' | cut -d. -f1)
        if [[ $major -lt 16 ]]; then
            print_error "Node.js 16+ required. Installing latest Node.js..."
            brew install node
            check_success
        fi
    fi
}

# Install Rust and Cargo
install_rust() {
    if ! command -v cargo &> /dev/null; then
        print_info "Installing Rust via rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
        check_success
    else
        local rust_version=$(rustc --version)
        print_success "Rust found: $rust_version"
    fi
}

# Install Solana CLI
install_solana() {
    if ! command -v solana &> /dev/null; then
        print_info "Installing Solana CLI..."
        
        # Use the official Solana installer
        sh -c "$(curl -sSfL https://release.solana.com/v1.18.4/install)"
        
        # Add to PATH
        export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
        
        # Add to shell profile
        local shell_profile=""
        if [[ -f ~/.zshrc ]]; then
            shell_profile=~/.zshrc
        elif [[ -f ~/.bash_profile ]]; then
            shell_profile=~/.bash_profile
        elif [[ -f ~/.bashrc ]]; then
            shell_profile=~/.bashrc
        fi
        
        if [[ -n "$shell_profile" ]]; then
            echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> "$shell_profile"
        fi
        
        check_success
    else
        local solana_version=$(solana --version)
        print_success "Solana CLI found: $solana_version"
    fi
}

# Install SPL Token CLI
install_spl_token() {
    if ! command -v spl-token &> /dev/null; then
        print_info "Installing SPL Token CLI..."
        cargo install spl-token-cli
        check_success
    else
        local spl_version=$(spl-token --version 2>/dev/null || echo "installed")
        print_success "SPL Token CLI found: $spl_version"
    fi
}

# Check if we're in the right directory
check_project_directory() {
    if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
        print_error "This doesn't appear to be your BigKreators project directory."
        print_info "Please run this script from the directory containing main.py and requirements.txt"
        exit 1
    fi
    print_success "Found BigKreators project files"
}

# Create Python virtual environment
setup_python_env() {
    print_info "Setting up Python virtual environment..."
    
    # Use python3 explicitly on Mac
    python3 -m venv venv
    check_success
    
    # Activate virtual environment
    source venv/bin/activate
    check_success
    
    # Upgrade pip
    pip install --upgrade pip
    check_success
    
    print_success "Python virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    # Make sure we're in the virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source venv/bin/activate
    fi
    
    # Install requirements
    pip install -r requirements.txt
    check_success
    
    print_success "Python dependencies installed"
}

# Install additional Solana dependencies
install_solana_deps() {
    print_info "Installing Solana Python dependencies..."
    
    # Make sure we're in the virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source venv/bin/activate
    fi
    
    # Install specific versions that work well on Mac
    pip install solana==0.36.7 solders==0.23.1 base58==2.1.1
    check_success
    
    print_success "Solana dependencies installed"
}

# Setup MongoDB (optional local install)
setup_mongodb() {
    print_section "MongoDB Setup"
    print_info "Do you want to install MongoDB locally? (y/n)"
    print_info "Note: You can also use MongoDB Atlas (cloud) instead"
    read -r mongodb_choice
    
    if [[ "$mongodb_choice" =~ ^[Yy]$ ]]; then
        if ! command -v mongod &> /dev/null; then
            print_info "Installing MongoDB via Homebrew..."
            brew tap mongodb/brew
            brew install mongodb-community
            check_success
            
            print_info "Starting MongoDB service..."
            brew services start mongodb/brew/mongodb-community
            check_success
        else
            print_success "MongoDB already installed"
        fi
    else
        print_info "Skipping local MongoDB installation"
        print_info "Make sure to set up MongoDB Atlas or another MongoDB instance"
    fi
}

# Configure Solana for devnet
configure_solana() {
    print_info "Configuring Solana CLI for devnet..."
    
    solana config set --url devnet
    check_success
    
    print_success "Solana configured for devnet"
}

# Create directories
create_directories() {
    print_info "Creating necessary directories..."
    
    mkdir -p services models routes static/js static/css templates/partials
    check_success
    
    print_success "Directories created"
}

# Main setup function
main() {
    print_section "KONTRIB Token Setup for macOS"
    
    local arch=$(detect_architecture)
    print_info "Detected architecture: $arch"
    
    # Check if we're in the right directory
    check_project_directory
    
    # Install system dependencies
    print_section "Installing System Dependencies"
    install_homebrew
    install_python
    install_nodejs
    install_rust
    
    # Install blockchain tools
    print_section "Installing Blockchain Tools"
    install_solana
    install_spl_token
    
    # Setup Python environment
    print_section "Setting up Python Environment"
    setup_python_env
    #install_python_deps
    #install_solana_deps
    
    # Optional MongoDB setup
    #setup_mongodb
    
    # Configure blockchain tools
    print_section "Configuring Blockchain Tools"
    configure_solana
    
    # Create project structure
    print_section "Setting up Project Structure"
    create_directories
    
    print_section "Setup Complete!"
    print_success "macOS setup completed successfully!"
    
    echo
    print_section "Next Steps"
    print_info "1. Set up your environment variables:"
    echo "   cp .env.example .env  # If you have an example file"
    echo "   # Or create .env with your MongoDB connection string"
    echo
    print_info "2. Run the database migration:"
    echo "   source venv/bin/activate"
    echo "   python migrate_database.py"
    echo
    print_info "3. Create your KONTRIB token:"
    echo "   python create_kontrib_token.py"
    echo
    print_info "4. Start your development server:"
    echo "   uvicorn main:app --reload"
    echo
    print_section "macOS-Specific Notes"
    print_info "• Virtual environment: source venv/bin/activate"
    print_info "• Architecture detected: $arch"
    print_info "• Homebrew package manager used for dependencies"
    print_info "• Solana tools installed to ~/.local/share/solana/"
    
    if [[ "$arch" == "apple_silicon" ]]; then
        print_info "• Apple Silicon detected - all tools are compatible"
        print_info "• Homebrew installed to /opt/homebrew/"
    else
        print_info "• Intel Mac detected - using standard paths"
        print_info "• Homebrew installed to /usr/local/"
    fi
    
    echo
    print_info "If you encounter any issues:"
    print_info "• Check that all tools are in your PATH"
    print_info "• Restart your terminal after installation"
    print_info "• Run 'source ~/.zshrc' or 'source ~/.bash_profile'"
}

# Run setup if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
