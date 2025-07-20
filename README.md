# Particle Event Simulator and Visualizer

This project is a simulation and visualization tool for generating synthetic particle events in HepMC ASCII format, supporting pion, kaon, and proton species. It uses [ROOT](https://root.cern/) for random generation, histogramming, and fitting.

## Features

- Generate synthetic particle events with randomized momenta and vertices
- Save events in HepMC v3 ASCII format
- Parse and visualize vertex and momentum distributions using ROOT
- Fit distributions with Gaussian and 2D Gaussian functions
- Interactive plotting interface

## Requirements

- Python 3.x
- [ROOT](https://root.cern/install/) (Python bindings must be available, e.g., `import ROOT` should work)

## Getting Started

### Running the Program
python3 particle_simulator.py
