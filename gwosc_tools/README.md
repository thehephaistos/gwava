# gwava

Tool designed for plotting gravitational wave data from gwosc as Stellar Graveyard Plot

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

--- 

## Installation

Install via pip:

```bash
pip install gwava
```

Or install from source:

```bash
git clone https://github.com/thehephaistos/gwava
cd gwava
pip install -e .
```
---

## Project Structure
```text
.vscode/
│── settings.json
gwosc_tools/
│── dist/
│── docs/
│── gwocs.egg-info
│── gwosc_tools/
│   ├── __init__.py
│   ├── __main__.py
│   ├── api.py
|   ├── cli.py
|   ├── config.py
|   ├── events.py
|   ├── plotting.py
|   ├── sorting.py
│── getYaml.py
│── GWOSC API.yaml
│── pyproject.toml
│── README.md
│── requirements.txt
│── LICENSE
```

## License

This project is licensed under the MIT License. See the `LICENSE` file.

## Authors

Jayanth Bharadwaj
Github: https://github.com/JayanthPhysics
Email: jbharadwaj@ucsd.edu

Ines Belkhodja
Github: https://github.com/ibelkhodja
Email: inesasma.belkhodja@gmail.com

Ogoz Kirmizi
Github: https://github.com/thehephaistos 
Email: oguz.kirmizi@uni.minerva.edu

## Citation

If you use this package in research: 

```bibtex
@software{package2026,
  author = {J. Bharadwaj and I. Belkhodka and O. Kirmizi},
  title = {gwava},
  year = {2026},
  url = {https://github.com/thehephaistos/gwava}
}
```