#!/bin/bash

# Kryptopedia - Dependencies Installation Script v0.1
# This script installs all dependencies required for Kryptopedia, including:
# - Python and pip
# - MongoDB
# - Docker and Docker Compose
# - NodeJS and npm (for any frontend development)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}     Kryptopedia - Dependencies Installation        ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Detect operating system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    # Detect distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo -e "${RED}Unsupported operating system: $OSTYPE${NC}"
    echo "This script supports Linux and macOS."
    exit 1
fi

echo -e "${BLUE}Detected operating system: ${OS}${NC}"
if [ "$OS" = "linux" ]; then
    echo -e "${BLUE}Detected distribution: ${DISTRO}${NC}"
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to ask for confirmation
confirm() {
    read -r -p "$1 [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            true
            ;;
        *)
            false
            ;;
    esac
}

# Install Python and pip
install_python() {
    echo -e "\n${BLUE}Checking Python installation...${NC}"
    if command_exists python3 && command_exists pip3; then
        python_version=$(python3 --version)
        pip_version=$(pip3 --version)
        echo -e "${GREEN}Python is already installed: ${python_version}${NC}"
        echo -e "${GREEN}pip is already installed: ${pip_version}${NC}"
    else
        echo -e "${YELLOW}Installing Python and pip...${NC}"
        
        if [ "$OS" = "linux" ]; then
            if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
                sudo apt-get update
                sudo apt-get install -y python3 python3-pip python3-venv
            elif [ "$DISTRO" = "fedora" ]; then
                sudo dnf install -y python3 python3-pip
            elif [ "$DISTRO" = "centos" ] || [ "$DISTRO" = "rhel" ]; then
                sudo yum install -y python3 python3-pip
            else
                echo -e "${YELLOW}Please install Python 3.8+ and pip manually for your distribution.${NC}"
            fi
        elif [ "$OS" = "macos" ]; then
            if command_exists brew; then
                brew install python
            else
                echo -e "${YELLOW}Homebrew not found. Installing Homebrew...${NC}"
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                brew install python
            fi
        fi
        
        echo -e "${GREEN}Python and pip installed successfully.${NC}"
    fi
}

# Install MongoDB
install_mongodb() {
    echo -e "\n${BLUE}Checking MongoDB installation...${NC}"
    if command_exists mongod; then
        mongo_version=$(mongod --version | grep "db version")
        echo -e "${GREEN}MongoDB is already installed: ${mongo_version}${NC}"
    else
        echo -e "${YELLOW}Installing MongoDB...${NC}"
        
        if [ "$OS" = "linux" ]; then
            if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
                echo -e "${YELLOW}Adding MongoDB repository...${NC}"
                wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
                
                if [ "$DISTRO" = "ubuntu" ]; then
                    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
                else
                    echo "deb http://repo.mongodb.org/apt/debian $(lsb_release -cs)/mongodb-org/6.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
                fi
                
                sudo apt-get update
                sudo apt-get install -y mongodb-org
                
                # Start MongoDB service
                sudo systemctl enable mongod
                sudo systemctl start mongod
                
            elif [ "$DISTRO" = "fedora" ]; then
                echo -e "${YELLOW}Adding MongoDB repository...${NC}"
                cat > /etc/yum.repos.d/mongodb-org-6.0.repo << EOF
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
EOF
                sudo dnf install -y mongodb-org
                sudo systemctl enable mongod
                sudo systemctl start mongod
                
            elif [ "$DISTRO" = "centos" ] || [ "$DISTRO" = "rhel" ]; then
                echo -e "${YELLOW}Adding MongoDB repository...${NC}"
                cat > /etc/yum.repos.d/mongodb-org-6.0.repo << EOF
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
EOF
                sudo yum install -y mongodb-org
                sudo systemctl enable mongod
                sudo systemctl start mongod
            else
                echo -e "${YELLOW}Please install MongoDB manually for your distribution.${NC}"
                echo -e "${YELLOW}Visit: https://www.mongodb.com/docs/manual/administration/install-on-linux/${NC}"
            fi
        elif [ "$OS" = "macos" ]; then
            if command_exists brew; then
                brew tap mongodb/brew
                brew install mongodb-community
                brew services start mongodb-community
            else
                echo -e "${RED}Homebrew is required to install MongoDB on macOS.${NC}"
                exit 1
            fi
        fi
        
        # Verify MongoDB installation
        if command_exists mongod; then
            echo -e "${GREEN}MongoDB installed successfully.${NC}"
        else
            echo -e "${RED}MongoDB installation failed.${NC}"
            exit 1
        fi
    fi
}

# Install Docker and Docker Compose
install_docker() {
    echo -e "\n${BLUE}Checking Docker installation...${NC}"
    if command_exists docker; then
        docker_version=$(docker --version)
        echo -e "${GREEN}Docker is already installed: ${docker_version}${NC}"
    else
        echo -e "${YELLOW}Installing Docker...${NC}"
        
        if [ "$OS" = "linux" ]; then
            if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
                sudo apt-get update
                sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
                curl -fsSL https://download.docker.com/linux/${DISTRO}/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/${DISTRO} $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            elif [ "$DISTRO" = "fedora" ]; then
                sudo dnf -y install dnf-plugins-core
                sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
                sudo dnf install -y docker-ce docker-ce-cli containerd.io
            elif [ "$DISTRO" = "centos" ] || [ "$DISTRO" = "rhel" ]; then
                sudo yum install -y yum-utils
                sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                sudo yum install -y docker-ce docker-ce-cli containerd.io
            else
                echo -e "${YELLOW}Please install Docker manually for your distribution.${NC}"
                echo -e "${YELLOW}Visit: https://docs.docker.com/engine/install/${NC}"
            fi
            
            # Start Docker service
            sudo systemctl enable docker
            sudo systemctl start docker
            
            # Add current user to docker group to run without sudo
            if confirm "Do you want to add your user to the docker group to run Docker without sudo?"; then
                sudo usermod -aG docker $USER
                echo -e "${YELLOW}You may need to log out and log back in for this to take effect.${NC}"
            fi
            
        elif [ "$OS" = "macos" ]; then
            echo -e "${YELLOW}Please install Docker Desktop for Mac manually.${NC}"
            echo -e "${YELLOW}Visit: https://docs.docker.com/desktop/install/mac-install/${NC}"
            if confirm "Open the Docker Desktop download page in your browser?"; then
                open "https://docs.docker.com/desktop/install/mac-install/"
            fi
        fi
    fi
    
    # Check Docker Compose
    echo -e "\n${BLUE}Checking Docker Compose installation...${NC}"
    if command_exists docker-compose; then
        docker_compose_version=$(docker-compose --version)
        echo -e "${GREEN}Docker Compose is already installed: ${docker_compose_version}${NC}"
    else
        # Docker Compose is now included with Docker Desktop, so we only need to check for Linux
        if [ "$OS" = "linux" ]; then
            echo -e "${YELLOW}Installing Docker Compose...${NC}"
            sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            
            # Verify Docker Compose installation
            if command_exists docker-compose; then
                echo -e "${GREEN}Docker Compose installed successfully.${NC}"
            else
                echo -e "${RED}Docker Compose installation failed.${NC}"
            fi
        fi
    fi
}

# Install Node.js and npm (optional, only if needed for frontend development)
install_nodejs() {
    echo -e "\n${BLUE}Checking Node.js installation...${NC}"
    if command_exists node && command_exists npm; then
        node_version=$(node --version)
        npm_version=$(npm --version)
        echo -e "${GREEN}Node.js is already installed: ${node_version}${NC}"
        echo -e "${GREEN}npm is already installed: ${npm_version}${NC}"
    else
        if confirm "Do you want to install Node.js and npm (needed for frontend development)?"; then
            echo -e "${YELLOW}Installing Node.js and npm...${NC}"
            
            if [ "$OS" = "linux" ]; then
                if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
                    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
                    sudo apt-get install -y nodejs
                elif [ "$DISTRO" = "fedora" ]; then
                    curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
                    sudo dnf install -y nodejs
                elif [ "$DISTRO" = "centos" ] || [ "$DISTRO" = "rhel" ]; then
                    curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
                    sudo yum install -y nodejs
                else
                    echo -e "${YELLOW}Please install Node.js manually for your distribution.${NC}"
                fi
            elif [ "$OS" = "macos" ]; then
                if command_exists brew; then
                    brew install node
                else
                    echo -e "${RED}Homebrew is required to install Node.js on macOS.${NC}"
                fi
            fi
            
            # Verify Node.js installation
            if command_exists node && command_exists npm; then
                echo -e "${GREEN}Node.js and npm installed successfully.${NC}"
            else
                echo -e "${RED}Node.js installation failed.${NC}"
            fi
        else
            echo -e "${BLUE}Skipping Node.js installation.${NC}"
        fi
    fi
}

# Main installation process
main() {
    echo -e "\n${BLUE}Starting installation of dependencies for Kryptopedia...${NC}"
    
    # Install Python and pip
    install_python
    
    # Install MongoDB
    install_mongodb
    
    # Install Docker and Docker Compose
    install_docker
    
    # Install Node.js and npm (optional)
    install_nodejs
    
    # Check all installations
    echo -e "\n${BLUE}Verifying installations...${NC}"
    
    if command_exists python3 && command_exists pip3; then
        echo -e "${GREEN}✓ Python and pip are installed.${NC}"
    else
        echo -e "${RED}✗ Python or pip installation is missing.${NC}"
    fi
    
    if command_exists mongod; then
        echo -e "${GREEN}✓ MongoDB is installed.${NC}"
    else
        echo -e "${RED}✗ MongoDB installation is missing.${NC}"
    fi
    
    if command_exists docker; then
        echo -e "${GREEN}✓ Docker is installed.${NC}"
    else
        echo -e "${RED}✗ Docker installation is missing.${NC}"
    fi
    
    if command_exists docker-compose; then
        echo -e "${GREEN}✓ Docker Compose is installed.${NC}"
    else
        echo -e "${RED}✗ Docker Compose installation is missing.${NC}"
    fi
    
    echo -e "\n${BLUE}====================================================${NC}"
    echo -e "${GREEN}Kryptopedia dependencies installation complete!${NC}"
    echo -e "${BLUE}====================================================${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "1. Run setup-kryptopedia.sh to configure your Kryptopedia instance"
    echo -e "2. Start Kryptopedia using start-local.sh (for local deployment) or"
    echo -e "   start-docker.sh (for Docker-based deployment)"
    echo -e "${BLUE}====================================================${NC}"
}

# Run the main function
main
