#!/usr/bin/env python3
"""Ansible dynamic inventory backed by the sentinel devops-inventory API.

Servers register themselves with sentinel (the devops_inventory backend) via
the inventory_client role's periodic check-in. This script queries sentinel's
Ansible inventory endpoint so that Ansible always targets exactly the set of
servers sentinel knows about, instead of a hand-maintained host list.

Required env var:
  ANSIBLE_INVENTORY_TOKEN   Bearer token for the sentinel Ansible inventory API

Optional env var:
  ANSIBLE_INVENTORY_API_URL  Base URL of the sentinel backend
                              (default: https://sentinel.devops.mrmilu.com)

Usage:
  python sentinel_inventory.py --list   # called by Ansible automatically
  python sentinel_inventory.py --host <name>  # unused, hostvars come from --list
"""

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_API_URL = "https://sentinel.devops.mrmilu.com"
INVENTORY_PATH = "/api/v1/inventory/ansible/"


def fetch_inventory() -> dict:
    """Fetch the Ansible inventory JSON from sentinel."""
    token = os.environ.get("ANSIBLE_INVENTORY_TOKEN", "")
    if not token:
        print(
            "[sentinel_inventory] ANSIBLE_INVENTORY_TOKEN is not set", file=sys.stderr
        )
        sys.exit(1)

    base_url = os.environ.get("ANSIBLE_INVENTORY_API_URL", DEFAULT_API_URL).rstrip(
        "/"
    )
    url = base_url + INVENTORY_PATH
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"[sentinel_inventory] API error: {exc}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"[sentinel_inventory] Failed to reach {url}: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Entry point — handle --list and --host flags."""
    if len(sys.argv) == 3 and sys.argv[1] == "--host":
        # hostvars are already included in _meta from --list
        print(json.dumps({}))
        return

    print(json.dumps(fetch_inventory(), indent=2))


if __name__ == "__main__":
    main()
