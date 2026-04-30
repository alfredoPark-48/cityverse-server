# 🌆 CityVerse Server

CityVerse is a high-fidelity urban mobility simulation built with **Python** and **Mesa**. It models complex interactions between cars, pedestrians, and public transport in a dynamic, data-driven city environment.

This project is a refactored and significantly improved version of the original [Project-Multiagentes](https://github.com/ivalani/Project-Multiagentes).

---

## 📑 Table of Contents
1. [Project Overview](#-project-overview)
2. [Quick Start](#-quick-start)
3. [Architecture Blueprint](./doc/ARCHITECTURE.md)
4. [Agent Behaviors](./doc/AGENTS.md)
5. [Data Structures & Algorithms](./doc/ALGORITHMS.md)
6. [Legacy Comparison](./doc/LEGACY_COMPARISON.md)
7. [Key Features](#-key-features)
8. [Roadmap](#-roadmap)

---

## 🚀 Project Overview

CityVerse evolved from a research prototype into a robust simulation engine. The primary focus of this version is **system stability**, **architectural clarity**, and **algorithmic efficiency**.

### Core Improvements
- **Clean Architecture**: Transitioned to a decoupled 3-tier architecture (Domain, Application, Infrastructure) for better maintainability.
- **Enhanced Navigation**: Implementation of A* pathfinding with a BFS fallback mechanism to ensure topological robustness.
- **Multimodal Simulation**: Seamless transitions for pedestrians between walking and public transport using state-machine logic.
- **Modular Design**: Services like spawning, navigation, and graph building are now isolated, allowing for easier testing and expansion.

---

## 🛠 Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose

### Installation
```bash
# Clone the repository
git clone https://github.com/alfredoPark-48/cityverse-server.git
cd cityverse-server

# Install dependencies
pip install -r requirements.txt

# Start the simulation server
python run.py
```

---

## ✨ Key Features

### 1. Multimodal Intelligence
Pedestrians dynamically evaluate the efficiency of the public transport network. They calculate potential time-savings using bus routes versus walking paths and navigate to stops accordingly.

### 2. Directed Network Topology
The simulation builds two distinct directed graphs (Road and Pedestrian) from a plain-text grid. This ensures vehicles respect one-way constraints and pedestrians stay on designated sidewalks.

### 3. Real-Time Metrics & Analytics
The simulation exposes a standardized API for front-end consumption, providing live stats on agent frustration, bus occupancy, and trip completion rates.

---

## 🛣 Roadmap
- [ ] **AI Traffic Control**: Reinforcement learning for adaptive traffic light cycles.
- [ ] **Weather & Environmental Factors**: Impacting agent visibility and speed.
- [ ] **Emission Tracking**: Modeling the environmental impact of urban traffic.

---

> **Note**: This repository follows clean code practices and modular design patterns to provide a scalable foundation for urban mobility research.
