#!/usr/bin/env python3

"""
AWS Credentials Setup Script

This script helps you configure AWS credentials for use with AWS CLI.
It saves the credentials to the appropriate location based on your operating system.

Usage:
    # Configure a new AWS profile (credentials only)
    python3 aws-credentials-setup.py --profile <profile-name> --access-key <key> --secret-key <secret>

    # Configure with custom region
    python3 aws-credentials-setup.py --profile <profile-name> --access-key <key> --secret-key <secret> --region <region>

    # First-time setup only (checks AWS CLI, SSM plugin, and configures SSH)
    python3 aws-credentials-setup.py --first-install

License: GNU General Public License v3 or later (GPLv3+)
"""

import argparse
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def get_aws_config_directory() -> Path:
    """
    Get the AWS configuration directory based on the operating system.

    Returns:
        Path: The AWS configuration directory path
    """
    system = platform.system()

    if system == "Windows":
        # Windows: %USERPROFILE%\.aws\
        home = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    else:
        # Linux, macOS, and other Unix-like systems: ~/.aws/
        home = os.path.expanduser("~")

    aws_dir = Path(home) / ".aws"
    return aws_dir


def ensure_aws_directory_exists(aws_dir: Path) -> None:
    """
    Ensure the AWS configuration directory exists.

    Args:
        aws_dir: Path to the AWS configuration directory
    """
    ## 0o700 is 700 in octal permissions in python
    if not aws_dir.exists():
        aws_dir.mkdir(mode=0o700, parents=True)
        print(f"Created AWS configuration directory: {aws_dir}")
    else:
        print(f"Using existing AWS configuration directory: {aws_dir}")


def read_file_safely(file_path: Path) -> str:
    """
    Safely read a file's contents, returning empty string if it doesn't exist.

    Args:
        file_path: Path to the file to read

    Returns:
        str: File contents or empty string
    """
    if file_path.exists():
        return file_path.read_text()
    return ""


def profile_exists(credentials_file: Path, config_file: Path, profile: str) -> bool:
    """
    Check if a profile already exists in credentials or config files.

    Args:
        credentials_file: Path to the credentials file
        config_file: Path to the config file
        profile: AWS profile name

    Returns:
        bool: True if profile exists, False otherwise
    """
    # Check credentials file
    credentials_content = read_file_safely(credentials_file)
    profile_section = f"[{profile}]"
    if profile_section in credentials_content:
        return True

    # Check config file
    config_content = read_file_safely(config_file)
    if profile == "default":
        config_profile_section = "[default]"
    else:
        config_profile_section = f"[profile {profile}]"

    if config_profile_section in config_content:
        return True

    return False


def prompt_user_override(profile: str) -> bool:
    """
    Prompt the user to confirm if they want to override an existing profile.

    Args:
        profile: AWS profile name

    Returns:
        bool: True if user wants to override, False otherwise
    """
    while True:
        response = input(
            f"⚠ Profile '{profile}' already exists. Do you want to override it? (y/n): "
        ).strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please answer 'y' or 'n'.")


def update_credentials_file(
    credentials_file: Path, profile: str, access_key: str, secret_key: str
) -> None:
    """
    Update or add credentials to the AWS credentials file.

    Args:
        credentials_file: Path to the credentials file
        profile: AWS profile name
        access_key: AWS access key ID
        secret_key: AWS secret access key
    """
    content = read_file_safely(credentials_file)
    lines = content.splitlines() if content else []

    profile_section = f"[{profile}]"
    profile_found = False
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line == profile_section:
            profile_found = True
            new_lines.append(lines[i])
            i += 1

            # Skip existing keys for this profile
            while (
                i < len(lines)
                and lines[i].strip()
                and not lines[i].strip().startswith("[")
            ):
                i += 1

            # Add new credentials
            new_lines.append(f"aws_access_key_id = {access_key}")
            new_lines.append(f"aws_secret_access_key = {secret_key}")
            continue

        new_lines.append(lines[i])
        i += 1

    # If profile wasn't found, add it at the end
    if not profile_found:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(profile_section)
        new_lines.append(f"aws_access_key_id = {access_key}")
        new_lines.append(f"aws_secret_access_key = {secret_key}")

    credentials_file.write_text("\n".join(new_lines) + "\n")
    credentials_file.chmod(
        0o600
    )  # Set file permissions to read/write for owner only in octal
    print(f"✓ Credentials for profile '{profile}' saved to {credentials_file}")


def update_config_file(config_file: Path, profile: str, region: str) -> None:
    """
    Update or add region configuration to the AWS config file.

    Args:
        config_file: Path to the config file
        profile: AWS profile name
        region: AWS region
    """
    content = read_file_safely(config_file)
    lines = content.splitlines() if content else []

    # For default profile, section is [default], for others it's [profile name]
    if profile == "default":
        profile_section = "[default]"
    else:
        profile_section = f"[profile {profile}]"

    profile_found = False
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line == profile_section:
            profile_found = True
            new_lines.append(lines[i])
            i += 1

            # Skip existing settings for this profile
            while (
                i < len(lines)
                and lines[i].strip()
                and not lines[i].strip().startswith("[")
            ):
                i += 1

            new_lines.append(f"region = {region}")
            continue

        new_lines.append(lines[i])
        i += 1

    # If profile wasn't found, add it at the end
    if not profile_found:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(profile_section)
        new_lines.append(f"region = {region}")

    # Write the updated content
    config_file.write_text("\n".join(new_lines) + "\n")
    config_file.chmod(
        0o600
    )  # Set file permissions to read/write for owner only in octal
    print(f"✓ Region '{region}' for profile '{profile}' saved to {config_file}")


def check_aws_cli_installed() -> bool:
    """
    Check if AWS CLI is installed.

    Returns:
        bool: True if installed, False otherwise
    """
    try:
        subprocess.run(
            ["aws", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=True,
        )
        return True
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        return False


def install_aws_cli() -> None:
    """
    Provide instructions to install AWS CLI based on the operating system.
    """
    system = platform.system()

    print("AWS CLI is not installed.")
    print()
    print("Installation instructions:")
    print()

    if system == "Darwin":  # macOS
        print("Option 1 - Using Homebrew (recommended):")
        print("  brew install awscli")
        print()
        print("Option 2 - Using the official installer:")
        print("  curl 'https://awscli.amazonaws.com/AWSCLIV2.pkg' -o 'AWSCLIV2.pkg'")
        print("  sudo installer -pkg AWSCLIV2.pkg -target /")

    elif system == "Linux":
        print("Using the official installer:")
        print(
            "  curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
        )
        print("  unzip awscliv2.zip")
        print("  sudo ./aws/install")

    elif system == "Windows":
        print("Download and run the MSI installer from:")
        print("  https://awscli.amazonaws.com/AWSCLIV2.msi")

    else:
        print(f"For {system}, visit:")
        print(
            "  https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        )

    print()


def check_ssm_plugin_installed() -> bool:
    """
    Check if the AWS Session Manager plugin is installed.

    Returns:
        bool: True if installed, False otherwise
    """
    try:
        subprocess.run(
            ["session-manager-plugin"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        # The plugin returns a specific message when run without arguments
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_ssm_plugin() -> bool:
    """
    Install the AWS Session Manager plugin based on the operating system.

    Returns:
        bool: True if installation succeeded or user chose to install manually, False otherwise
    """
    system = platform.system()
    machine = platform.machine().lower()

    print(f"AWS Session Manager plugin is not installed.")
    print()

    if system == "Darwin":  # macOS
        print("Installing AWS Session Manager plugin for macOS...")
        print()

        # Check if Homebrew is available
        if shutil.which("brew"):
            print("Using Homebrew to install session-manager-plugin...")
            try:
                subprocess.run(
                    ["brew", "install", "--cask", "session-manager-plugin"], check=True
                )
                print("✓ Session Manager plugin installed successfully via Homebrew")
                return True
            except subprocess.CalledProcessError:
                print("✗ Failed to install via Homebrew")
                print()

        # Fallback to manual installation instructions
        print("Manual installation steps:")
        print("1. Download the bundled installer:")
        if machine == "arm64":
            print(
                "   curl 'https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac_arm64/sessionmanager-bundle.zip' -o 'sessionmanager-bundle.zip'"
            )
        else:
            print(
                "   curl 'https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip' -o 'sessionmanager-bundle.zip'"
            )
        print("2. Unzip the package:")
        print("   unzip sessionmanager-bundle.zip")
        print("3. Run the install script:")
        print(
            "   sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin"
        )
        print()

    elif system == "Linux":
        print("Installing AWS Session Manager plugin for Linux...")
        print()

        # Detect package manager and architecture
        if shutil.which("dpkg"):  # Debian/Ubuntu
            print("Detected Debian/Ubuntu system")
            try:
                arch = "64bit" if machine in ["x86_64", "amd64"] else "arm64"
                url = f"https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_{arch}/session-manager-plugin.deb"

                print(f"Downloading from {url}...")
                subprocess.run(
                    ["curl", url, "-o", "session-manager-plugin.deb"], check=True
                )

                print("Installing package...")
                subprocess.run(
                    ["sudo", "dpkg", "-i", "session-manager-plugin.deb"], check=True
                )

                # Clean up
                os.remove("session-manager-plugin.deb")
                print("✓ Session Manager plugin installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install: {e}")
                print()

        elif shutil.which("rpm"):  # RedHat/CentOS/Amazon Linux
            print("Detected RPM-based system")
            try:
                arch = "64bit" if machine in ["x86_64", "amd64"] else "arm64"
                url = f"https://s3.amazonaws.com/session-manager-downloads/plugin/latest/linux_{arch}/session-manager-plugin.rpm"

                print(f"Downloading from {url}...")
                subprocess.run(
                    ["curl", url, "-o", "session-manager-plugin.rpm"], check=True
                )

                print("Installing package...")
                subprocess.run(
                    ["sudo", "yum", "install", "-y", "session-manager-plugin.rpm"],
                    check=True,
                )

                # Clean up
                os.remove("session-manager-plugin.rpm")
                print("✓ Session Manager plugin installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install: {e}")
                print()

        print("Manual installation steps:")
        print("For detailed instructions, visit:")
        print(
            "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
        )
        print()

    elif system == "Windows":
        print("Manual installation required for Windows:")
        print("1. Download the installer from:")
        print(
            "   https://s3.amazonaws.com/session-manager-downloads/plugin/latest/windows/SessionManagerPluginSetup.exe"
        )
        print("2. Run the installer")
        print("3. Restart your terminal/PowerShell")
        print()

    else:
        print(f"Unsupported operating system: {system}")
        print("Please visit the AWS documentation for manual installation:")
        print(
            "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
        )
        print()

    return False


def update_ssh_config_for_ssm(ssh_config_file: Path) -> bool:
    """
    Check if SSM proxy configuration exists in SSH config, and add it if missing.

    Args:
        ssh_config_file: Path to the SSH config file

    Returns:
        bool: True if configuration was added, False if it already existed
    """
    SSM_CONFIG = """# AWS SSM Session Manager Configuration
host i-* mi-*
    ProxyCommand sh -c "aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"
"""

    content = read_file_safely(ssh_config_file)

    # Check if the SSM proxy config already exists
    if "aws ssm start-session" in content and "AWS-StartSSHSession" in content:
        print(f"✓ SSM SSH configuration already exists in {ssh_config_file}")
        return False

    # Append the configuration
    if content and not content.endswith("\n"):
        content += "\n"

    if content:
        content += "\n"  # Add blank line before new config

    content += SSM_CONFIG

    # Write the updated content
    ssh_config_file.write_text(content)
    ssh_config_file.chmod(0o600)  # Set file permissions to read/write for owner only
    print(f"✓ SSM SSH configuration added to {ssh_config_file}")
    return True


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Configure AWS credentials for AWS CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # First-time setup only (checks AWS CLI, SSM plugin, configures SSH)
  %(prog)s --first-install

  # Configure credentials for a profile
  %(prog)s --profile default --access-key AKIAIOSFODNN7EXAMPLE --secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

  # Configure profile with custom region
  %(prog)s --profile production --access-key AKIAIOSFODNN7EXAMPLE --secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY --region us-east-1

  # First-time setup + configure credentials in one step
  %(prog)s --profile default --access-key AKIAIOSFODNN7EXAMPLE --secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY --first-install
        """,
    )

    parser.add_argument(
        "-p",
        "--profile",
        help="AWS profile name (e.g., 'default', 'production', 'staging')",
    )

    parser.add_argument("-a", "--access-key", help="AWS Access Key ID")

    parser.add_argument("-s", "--secret-key", help="AWS Secret Access Key")

    parser.add_argument(
        "-r",
        "--region",
        default="eu-central-1",
        help="AWS region (default: eu-central-1)",
    )

    parser.add_argument(
        "--first-install",
        action="store_true",
        help="Perform first-time setup: check AWS CLI, SSM plugin, and configure SSH",
    )

    return parser.parse_args()


def main() -> None:
    """Run the main program logic."""
    args = parse_args()

    # Validate arguments
    if args.first_install and not (args.profile or args.access_key or args.secret_key):
        # First install mode only - no credentials needed
        configure_credentials = False
    elif args.profile and args.access_key and args.secret_key:
        # Normal mode or first install with credentials
        configure_credentials = True
    else:
        # Invalid combination
        print(
            "✗ Error: When configuring credentials, you must provide --profile, --access-key, and --secret-key"
        )
        print()
        print("Usage:")
        print("  # Configure credentials only:")
        print(
            "    python3 aws-credentials-setup.py --profile <name> --access-key <key> --secret-key <secret>"
        )
        print()
        print("  # First-time setup only:")
        print("    python3 aws-credentials-setup.py --first-install")
        print()
        print("  # Both:")
        print(
            "    python3 aws-credentials-setup.py --profile <name> --access-key <key> --secret-key <secret> --first-install"
        )
        sys.exit(1)

    print(f"AWS Credentials Setup")
    print(f"=" * 50)
    print(f"Operating System: {platform.system()}")
    if configure_credentials:
        print(f"Profile: {args.profile}")
        print(f"Region: {args.region}")
        print(
            f"Access Key: {args.access_key[:8]}..."
            if len(args.access_key) > 8
            else args.access_key
        )
    if args.first_install:
        print(f"Mode: First-time installation checks")
    if configure_credentials and not args.first_install:
        print(f"Mode: Profile configuration only")
    print(f"=" * 50)
    print()

    # Check AWS CLI if first install
    if args.first_install:
        print("Checking AWS CLI installation...")
        if check_aws_cli_installed():
            # Get version info
            result = subprocess.run(
                ["aws", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            version_output = result.stdout or result.stderr
            print(f"✓ AWS CLI is installed: {version_output.strip()}")
        else:
            install_aws_cli()
            print("⚠ Please install AWS CLI and run this script again")
            sys.exit(1)
        print()

    # Configure credentials if provided
    if configure_credentials:
        # Get AWS configuration directory
        aws_dir = get_aws_config_directory()
        ensure_aws_directory_exists(aws_dir)

        # File paths
        credentials_file = aws_dir / "credentials"
        config_file = aws_dir / "config"

        # Check if profile exists and prompt for override
        if profile_exists(credentials_file, config_file, args.profile):
            if not prompt_user_override(args.profile):
                print(f"Operation cancelled. Profile '{args.profile}' was not modified.")
                sys.exit(0)
            print()

        # Update credentials file
        update_credentials_file(
            credentials_file, args.profile, args.access_key, args.secret_key
        )

        # Update config file
        update_config_file(config_file, args.profile, args.region)

    # Only check and install SSM plugin if first install
    if args.first_install:
        # Check and install SSM plugin if needed
        print()
        print("Checking AWS Session Manager plugin...")
        if check_ssm_plugin_installed():
            print("✓ AWS Session Manager plugin is already installed")
        else:
            install_ssm_plugin()
            # Verify installation
            if check_ssm_plugin_installed():
                print("✓ AWS Session Manager plugin is now installed")
            else:
                print("⚠ AWS Session Manager plugin installation incomplete")
                print("  Please follow the manual installation steps above")

        # Update SSH config for SSM
        print()
        ssh_dir = Path.home() / ".ssh"
        if not ssh_dir.exists():
            ssh_dir.mkdir(mode=0o700, parents=True)
            print(f"Created SSH directory: {ssh_dir}")

        ssh_config_file = ssh_dir / "config"
        update_ssh_config_for_ssm(ssh_config_file)

    print()
    print("✓ Setup completed successfully!")
    print()

    if configure_credentials:
        print("AWS credentials configured:")
        if args.profile == "default":
            print("  aws s3 ls")
        else:
            print(f"  aws s3 ls --profile {args.profile}")
        print()
        print("To use this profile with ansible-tty:")
        print(f"  Add 'aws_profile: {args.profile}' to your inventory host variables")
        print()

    if args.first_install and configure_credentials:
        if check_ssm_plugin_installed():
            print(
                "SSH config for SSM has been configured. You can now use SSH with EC2 instance IDs:"
            )
            print("  ssh ec2-user@i-1234567890abcdef0")
        else:
            print(
                "Note: Install the AWS Session Manager plugin to use SSH with EC2 instance IDs"
            )
        print()

    if not configure_credentials and args.first_install:
        print("Next steps:")
        print("  Configure your AWS credentials with:")
        print(
            "  python3 aws-credentials-setup.py --profile <name> --access-key <key> --secret-key <secret>"
        )
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
