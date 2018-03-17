# ansible-tty

open a ssh session with a defined host in an ansible inventory


#### Prerequisites

* python 3.5 or greater
* ansible 2.4 or greater
* openssh client (present in most systems)

Tested in ubuntu, debian and arch linux,  but should be work on almost linux systems

## Install

clone the project and install it.
```sh
git clone https://github.com/alex-left/ansible-tty
cd ansible-tty
sudo python3 setup.py install

```

## Usage
```
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
