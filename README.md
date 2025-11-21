# ansible-tty

open a ssh session with a defined host in an ansible inventory


#### Prerequisites

* python 3.5 or greater
* ansible 2.4 or greater
* openssh client (present in most systems)

Tested in ubuntu, debian, alpine and arch linux, but should be work on almost linux systems

## Install

clone the project and install it.
```sh
git clone https://github.com/mrmilu/ansible-tty
cd ansible-tty
sudo pip3 install .

```
Or via pip:
```
pip3 install https://github.com/mrmilu/ansible-tty/archive/master.zip
```
### Notes

* Do a pull from the devops inventory repo to get new inventories.
* To update the tty binary, do a  ```sudo pip3 install .```

## SSM Setup

For AWS environments using SSM to connect to instances, a setup script is provided to configure AWS CLI credentials, Session Manager plugin, and SSH configuration for SSM connections.

AWS credentials are mandatory to be able to connect. If you don't have credentials for specific project, request them to DevOps team.

### Features

- Configures AWS credentials and profiles
- Checks and installs AWS CLI (with guidance)
- Checks and installs AWS Session Manager plugin
- Configures SSH for SSM connections to EC2 instances
- Supports multiple operating systems (macOS, Linux, Windows)

### Usage

**First-time setup** (checks AWS CLI, SSM plugin, configures SSH):
```bash
python3 aws-credentials-setup.py --first-install
```

**Configure AWS credentials** for a profile, your profile must match the profile used in the inventory repo:
```bash
python3 aws-credentials-setup.py --profile <profile-name> --access-key <key> --secret-key <secret>
```

**Configure with custom region**:
```bash
python3 aws-credentials-setup.py --profile production --access-key <key> --secret-key <secret> --region us-east-1
```

**Complete setup** (first-time checks + credentials in one step):
```bash
python3 aws-credentials-setup.py --profile default --access-key <key> --secret-key <secret> --first-install
```

### Notes

- When using `--first-install` alone, it only checks system prerequisites
- Credentials configuration is fast and can be run separately for multiple profiles
- The script automatically detects your operating system and provides appropriate installation methods
- **Important**: The profile name you use must match the `aws_profile` value in the devops.inventory repo. For example, if `/pneumax/staging.yaml` contains `aws_profile: pneumax`, then you should save the credentials using `--profile pneumax`

## Via docker
You can use the public image of docker:
```
docker pull mrmiludevops/ansible-tty
```

you should use it binding some read-only volumes, for example you maybe want
access to your ssh keys or aws profiles and sure you will want read your ansible's inventory
```
docker run --rm -it \
-v $(pwd):/workdir:ro  \
-v $HOME/.ssh/:/root/.ssh/:ro \
-v $HOME/.aws/:/root/.aws/:ro \
mrmiludevops/ansible-tty -i [your inventory]
```

Also you can build you own image:
```
docker build -t ansible-tty .
```

## Usage
```sh
usage: ansible-tty [-h] [-i INVENTORY] [hostname]

Init an ssh interactive terminal using ansible inventories

positional arguments:
  hostname              Try to filter and connect to the unique hostname

optional arguments:
  -h, --help            show this help message and exit
  -i INVENTORY, --inventory INVENTORY
                        use a specific ansible inventory
```
- If no inventory is provided, ansible-inventory will try to load the default inventory
- If no hostname is provided, the script will scan all hosts defined in inventory and will show an interactive dialog so you can choose one of them


## TODO
- configure more connectors than ssh (sshlxd, lxc, docker...)
- use "ansible-eval" to get the real content of needed variables because the variables like "ansible_ssh_host" or "ansible_ssh_private_key_file" if have jinja syntax, ansible-inventories don't evaluate them
- add some kind of tests

## Contributing

All pull requests are welcome!

## License

This project is licensed under GPL v3 licence - see the [LICENSE](LICENSE) file for details
