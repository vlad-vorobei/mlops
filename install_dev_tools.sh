#!/bin/bash

REQUIRED_PYTHON_VERSION="3.9"
REQUIRED_PYTHON_PACKAGES=("torch" "torchvision" "pillow" "Django")

INSTALL_LOG_FILE="install.log"

PRINT() {
    local level="$1"
    local message="$2"

    local color_print

    local datetime
    datetime=$(date '+%Y-%m-%dT%H:%M:%S')

    case $level in
        "INFO")
            color_print="\033[32m[$level]\033[0m $message"
            ;;
        "WARNING")
            color_print="\033[33m[$level]\033[0m $message"
            ;;
        "ERROR")
            color_print="\033[31m[$level]\033[0m $message"
            ;;
        *)
            color_print="[$level] $message"
            ;;
    esac

    echo -e "$datetime $color_print"
}

source /etc/os-release

if [ "$EUID" -ne 0 ]; then
    PRINT ERROR "Please run this script with root permissions (for example: sudo ./install_dev_tools.sh)"
    exit 1
fi

OS=$ID

case $OS in
    "fedora")
        PACKAGE_MANAGER="dnf"
        UPDATE_CMD="dnf update -y"
        INSTALL_CMD="dnf install -y"
        $UPDATE_CMD
        ;;
    "ubuntu"|"debian")
        PACKAGE_MANAGER="apt"
        UPDATE_CMD="apt update -y"
        INSTALL_CMD="apt install -y"
        $UPDATE_CMD
        ;;
    *)
        PRINT ERROR "Curren OS '$OS' do not support!"
        exit 1
        ;;
esac

get_is_installed() {
    command -v "$1" &> /dev/null
}

install_docker() {
    if get_is_installed docker; then
        local docker_version=$(docker --version)
        PRINT INFO "Docker already installed. Current version: $docker_version"
    else
        PRINT INFO "Docker installing..."

        case $OS in
            "fedora")
                $PACKAGE_MANAGER install -y dnf-plugins-core
                $PACKAGE_MANAGER config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
                $INSTALL_CMD docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                ;;
            "ubuntu"|"debian")
                $INSTALL_CMD ca-certificates curl
                install -m 0755 -d /etc/apt/keyrings
                curl -fsSL "https://download.docker.com/linux/$OS/gpg" -o /etc/apt/keyrings/docker.asc
                chmod a+r /etc/apt/keyrings/docker.asc

                echo \
                  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$OS \
                  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
                  tee /etc/apt/sources.list.d/docker.list > /dev/null

                $UPDATE_CMD
                $INSTALL_CMD docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                ;;
        esac

        if get_is_installed docker; then
            local docker_version=$(docker --version)
            PRINT INFO "Docker successfully installed. Current version: $docker_version"
            echo "docker: $docker_version" >> "$INSTALL_LOG_FILE"
        else
            PRINT ERROR "Failed to install Docker!"
            return 1
        fi
    fi
}

check_python_version() {
    if ! get_is_installed python3; then
        return 1
    fi

    python3 -c "
import sys
required = tuple(map(int, '$REQUIRED_PYTHON_VERSION'.split('.')))
sys.exit(0 if sys.version_info[:2] >= required else 1)
"
}

get_python_version() {
    if get_is_installed python3; then
        python3 --version | awk '{print $2}'
    fi
}

install_python() {
    if check_python_version; then
        local python_version=$(get_python_version)
        PRINT INFO "Python already installed. Current version: $python_version"
    else
        PRINT INFO "Python installing..."
        case $OS in
            "fedora")
                $INSTALL_CMD python3 python3-pip python3-devel python3-venv
                ;;
            "ubuntu"|"debian")
                $INSTALL_CMD python3 python3-pip python3-dev python3-venv
                ;;
        esac

        if get_is_installed python3; then
            local python_version=$(get_python_version)
            PRINT INFO "Python successfully installed. Current version: $python_version"
            echo "python3: $python_version" >> "$INSTALL_LOG_FILE"
        else
            PRINT ERROR "Failed to install Python!"
            return 1
        fi
    fi
}

install_python_packages() {
    PRINT INFO "Checking virtual environment..."
    if [ ! -d ".venv" ]; then
        PRINT INFO "Creating virtual environment .venv..."
        python3 -m venv .venv
    fi

    for package in "${REQUIRED_PYTHON_PACKAGES[@]}"; do
        if .venv/bin/pip show "$package" &> /dev/null; then
            PRINT INFO "Package $package is already installed!"
        else
            PRINT INFO "Installing $package..."
            .venv/bin/pip install "$package"

            if .venv/bin/pip show "$package" &> /dev/null; then
                local pkg_version=$(.venv/bin/pip show "$package" | grep Version | awk '{print $2}')
                PRINT INFO "$package successfully installed (Version: $pkg_version)."
                echo "pip_$package: $pkg_version" >> "$INSTALL_LOG_FILE"
            else
                PRINT ERROR "Failed to install $package!"
                return 1
            fi
        fi
    done
}

main() {
    PRINT INFO "Starting ML/MLOps tools installation..."

    install_docker
    install_python
    install_python_packages

    PRINT INFO "Script successfully finished!"
}

main