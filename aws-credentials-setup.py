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
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


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
        logger.info(f"Created AWS configuration directory: {aws_dir}")
    else:
        logger.info(f"Using existing AWS configuration directory: {aws_dir}")


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
            logger.warning("Please answer 'y' or 'n'.")


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
    logger.info(f"✓ Credentials for profile '{profile}' saved to {credentials_file}")


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
    logger.info(f"✓ Region '{region}' for profile '{profile}' saved to {config_file}")


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

    logger.error("AWS CLI is not installed.")
    logger.info("")
    logger.info("Installation instructions:")
    logger.info("")

    if system == "Darwin":  # macOS
        logger.info("Option 1 - Using Homebrew (recommended):")
        logger.info("  brew install awscli")
        logger.info("")
        logger.info("Option 2 - Using the official installer:")
        logger.info("  curl 'https://awscli.amazonaws.com/AWSCLIV2.pkg' -o 'AWSCLIV2.pkg'")
        logger.info("  sudo installer -pkg AWSCLIV2.pkg -target /")

    elif system == "Linux":
        logger.info("Using the official installer:")
        logger.info(
            "  curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
        )
        logger.info("  unzip awscliv2.zip")
        logger.info("  sudo ./aws/install")

    elif system == "Windows":
        logger.info("Download and run the MSI installer from:")
        logger.info("  https://awscli.amazonaws.com/AWSCLIV2.msi")

    else:
        logger.info(f"For {system}, visit:")
        logger.info(
            "  https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        )

    logger.info("")


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

    logger.error(f"AWS Session Manager plugin is not installed.")
    logger.info("")

    if system == "Darwin":  # macOS
        logger.info("Installing AWS Session Manager plugin for macOS...")
        logger.info("")

        # Check if Homebrew is available
        if shutil.which("brew"):
            logger.info("Using Homebrew to install session-manager-plugin...")
            try:
                subprocess.run(
                    ["brew", "install", "--cask", "session-manager-plugin"], check=True
                )
                logger.info("✓ Session Manager plugin installed successfully via Homebrew")
                return True
            except subprocess.CalledProcessError:
                logger.error("Failed to install via Homebrew")
                logger.info("")

        # Fallback to manual installation instructions
        logger.info("Manual installation steps:")
        logger.info("1. Download the bundled installer:")
        if machine == "arm64":
            logger.info(
                "   curl 'https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac_arm64/sessionmanager-bundle.zip' -o 'sessionmanager-bundle.zip'"
            )
        else:
            logger.info(
                "   curl 'https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip' -o 'sessionmanager-bundle.zip'"
            )
        logger.info("2. Unzip the package:")
        logger.info("   unzip sessionmanager-bundle.zip")
        logger.info("3. Run the install script:")
        logger.info(
            "   sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin"
        )
        logger.info("")

    elif system == "Linux":
        logger.info("Installing AWS Session Manager plugin for Linux...")
        logger.info("")

        # Detect package manager and architecture
        if shutil.which("dpkg"):  # Debian/Ubuntu
            logger.info("Detected Debian/Ubuntu system")
            try:
                arch = "64bit" if machine in ["x86_64", "amd64"] else "arm64"
                url = f"https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_{arch}/session-manager-plugin.deb"

                logger.info(f"Downloading from {url}...")
                subprocess.run(
                    ["curl", url, "-o", "session-manager-plugin.deb"], check=True
                )

                logger.info("Installing package...")
                subprocess.run(
                    ["sudo", "dpkg", "-i", "session-manager-plugin.deb"], check=True
                )

                # Clean up
                os.remove("session-manager-plugin.deb")
                logger.info("✓ Session Manager plugin installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install: {e}")
                logger.info("")

        elif shutil.which("rpm"):  # RedHat/CentOS/Amazon Linux
            logger.info("Detected RPM-based system")
            try:
                arch = "64bit" if machine in ["x86_64", "amd64"] else "arm64"
                url = f"https://s3.amazonaws.com/session-manager-downloads/plugin/latest/linux_{arch}/session-manager-plugin.rpm"

                logger.info(f"Downloading from {url}...")
                subprocess.run(
                    ["curl", url, "-o", "session-manager-plugin.rpm"], check=True
                )

                logger.info("Installing package...")
                subprocess.run(
                    ["sudo", "yum", "install", "-y", "session-manager-plugin.rpm"],
                    check=True,
                )

                # Clean up
                os.remove("session-manager-plugin.rpm")
                logger.info("✓ Session Manager plugin installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install: {e}")
                logger.info("")

        logger.info("Manual installation steps:")
        logger.info("For detailed instructions, visit:")
        logger.info(
            "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
        )
        logger.info("")

    elif system == "Windows":
        logger.info("Manual installation required for Windows:")
        logger.info("1. Download the installer from:")
        logger.info(
            "   https://s3.amazonaws.com/session-manager-downloads/plugin/latest/windows/SessionManagerPluginSetup.exe"
        )
        logger.info("2. Run the installer")
        logger.info("3. Restart your terminal/PowerShell")
        logger.info("")

    else:
        logger.info(f"Unsupported operating system: {system}")
        logger.info("Please visit the AWS documentation for manual installation:")
        logger.info(
            "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
        )
        logger.info("")

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
        logger.info(f"✓ SSM SSH configuration already exists in {ssh_config_file}")
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
    logger.info(f"✓ SSM SSH configuration added to {ssh_config_file}")
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
        logger.error(
            "When configuring credentials, you must provide --profile, --access-key, and --secret-key"
        )
        logger.info("")
        logger.info("Usage:")
        logger.info("  # Configure credentials only:")
        logger.info(
            "    python3 aws-credentials-setup.py --profile <name> --access-key <key> --secret-key <secret>"
        )
        logger.info("")
        logger.info("  # First-time setup only:")
        logger.info("    python3 aws-credentials-setup.py --first-install")
        logger.info("")
        logger.info("  # Both:")
        logger.info(
            "    python3 aws-credentials-setup.py --profile <name> --access-key <key> --secret-key <secret> --first-install"
        )
        sys.exit(1)

    logger.info(f"AWS Credentials Setup")
    logger.info(f"=" * 50)
    logger.info(f"Operating System: {platform.system()}")
    if configure_credentials:
        logger.info(f"Profile: {args.profile}")
        logger.info(f"Region: {args.region}")
        logger.info(
            f"Access Key: {args.access_key[:8]}..."
            if len(args.access_key) > 8
            else args.access_key
        )
    if args.first_install:
        logger.info(f"Mode: First-time installation checks")
    if configure_credentials and not args.first_install:
        logger.info(f"Mode: Profile configuration only")
    logger.info(f"=" * 50)
    logger.info("")

    # Check AWS CLI if first install
    if args.first_install:
        logger.info("Checking AWS CLI installation...")
        if check_aws_cli_installed():
            # Get version info
            result = subprocess.run(
                ["aws", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            version_output = result.stdout or result.stderr
            logger.info(f"✓ AWS CLI is installed: {version_output.strip()}")
        else:
            install_aws_cli()
            logger.warning("Please install AWS CLI and run this script again")
            sys.exit(1)
        logger.info("")

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
                logger.info(f"Operation cancelled. Profile '{args.profile}' was not modified.")
                sys.exit(0)
            logger.info("")

        # Update credentials file
        update_credentials_file(
            credentials_file, args.profile, args.access_key, args.secret_key
        )

        # Update config file
        update_config_file(config_file, args.profile, args.region)

    # Only check and install SSM plugin if first install
    if args.first_install:
        # Check and install SSM plugin if needed
        logger.info("")
        logger.info("Checking AWS Session Manager plugin...")
        if check_ssm_plugin_installed():
            logger.info("✓ AWS Session Manager plugin is already installed")
        else:
            install_ssm_plugin()
            # Verify installation
            if check_ssm_plugin_installed():
                logger.info("✓ AWS Session Manager plugin is now installed")
            else:
                logger.warning("AWS Session Manager plugin installation incomplete")
                logger.warning("Please follow the manual installation steps above")

        # Update SSH config for SSM
        logger.info("")
        ssh_dir = Path.home() / ".ssh"
        if not ssh_dir.exists():
            ssh_dir.mkdir(mode=0o700, parents=True)
            logger.info(f"Created SSH directory: {ssh_dir}")

        ssh_config_file = ssh_dir / "config"
        update_ssh_config_for_ssm(ssh_config_file)

    logger.info("")
    logger.info("✓ Setup completed successfully!")
    logger.info("")

    if configure_credentials:
        logger.info("AWS credentials configured:")
        if args.profile == "default":
            logger.info("  aws s3 ls")
        else:
            logger.info(f"  aws s3 ls --profile {args.profile}")
        logger.info("")
        logger.info("To use this profile with ansible-tty:")
        logger.info(f"  Add 'aws_profile: {args.profile}' to your inventory host variables")
        logger.info("")

    if args.first_install and configure_credentials:
        if check_ssm_plugin_installed():
            logger.info(
                "SSH config for SSM has been configured. You can now use SSH with EC2 instance IDs:"
            )
            logger.info("  ssh ec2-user@i-1234567890abcdef0")
        else:
            logger.info(
                "Note: Install the AWS Session Manager plugin to use SSH with EC2 instance IDs"
            )
        logger.info("")

    if not configure_credentials and args.first_install:
        logger.info("Next steps:")
        logger.info("  Configure your AWS credentials with:")
        logger.info(
            "  python3 aws-credentials-setup.py --profile <name> --access-key <key> --secret-key <secret>"
        )
        logger.info("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Error: {e}")
        sys.exit(1)
