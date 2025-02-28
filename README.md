# ha-vinx

[![Tests](https://github.com/NitorCreations/ha-vinx/actions/workflows/unittest.yaml/badge.svg)](https://github.com/NitorCreations/ha-vinx/actions/workflows/unittest.yaml)
[![Linting](https://github.com/NitorCreations/ha-vinx/actions/workflows/ruff.yaml/badge.svg)](https://github.com/NitorCreations/ha-vinx/actions/workflows/ruff.yaml)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=NitorCreations&repository=https%3A%2F%2Fgithub.com%2FNitorCreations%2Fha-vinx)

Custom integration for controlling Lightware VINX encoders and decoders

## Features

* Auto-discovery of devices on the network
* Auto-discovery of available sources for decoders

The following entities are exposed:

* media players for encoders and decoders
* a button for rebooting devices
* a button for triggering source auto-discovery

## Development

Install dependencies:

```bash
pip3 install -r requirements.txt
```

Mount/symlink `custom_components/vinx` into a Home Assistant development environment.

## Tests

```bash
python3 -m unittest discover -s tests/ -v
```
