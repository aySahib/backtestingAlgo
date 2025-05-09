# backtestingAlgo
ADDED MINE: JANG
Added new: Sahib
# BacktestingAlgo

A Flask-based trading backtesting and algorithmic testing platform.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Windows Built-in Virtual Environment](#windows-built-in-virtual-environment)
- [Install Dependencies](#install-dependencies)
- [Running the Server](#running-the-server)
- [Git Workflow](#git-workflow)
  - [Cloning the Repository](#cloning-the-repository)
  - [Branching](#branching)
  - [Pushing Your Work](#pushing-your-work)
  - [Pulling Updates](#pulling-updates)
  - [Merging Into `main`](#merging-into-main)
- [Project Structure](#project-structure)

---

## Prerequisites

- Python 3.8+ installed on your system.
- Git installed and configured with your GitHub account.

---

## Windows Built-in Virtual Environment

1. Open **PowerShell** (or **CMD**) and navigate to the project directory:
   ```powershell
   cd C:\path\to\backtestingAlgo  DONT DO THIS ONE IF U IN THE FOLDER ALREADY SKIP IT
   ```

2. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```

3. Activate the virtual environment:

   - In **PowerShell**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```

   - In **CMD**:
     ```cmd
     .\.venv\Scripts\activate.bat
     ```

---

## Install Dependencies

With your virtual environment activated, install Python packages:

```powershell
pip install -r requirements.txt
```

This will install all required libraries, including Flask and any analytics or backtesting dependencies.

---

## Running the Server

Start the Flask server on a free port:

```powershell
python server.py
```

You should see output similar to:

```
INFO [timestamp] Logging is configured.
INFO [timestamp] Starting Flask app on http://127.0.0.1:54321
```

Open the printed URL in your browser to access the dashboard (`dash.html`).

---

## Git Workflow

### Cloning the Repository

If you haven’t cloned the project yet:

```bash
git clone https://github.com/yourusername/backtestingAlgo.git
cd backtestingAlgo
```

### Branching

Create a new branch for your feature or fix:

```bash
git checkout -b feature/my-new-algo
```

List all local and remote branches:

```bash
git branch         # local

git branch -r      # remote

git branch -a      # all
```

### Pushing Your Work

After making changes:

```bash
git add .
git commit -m "Describe your changes"
git push origin feature/my-new-algo
```

### Pulling Updates

Keep your branch up-to-date:

```bash
git pull origin main  # merge latest main into your branch
```

### Merging Into `main`

1. Switch to `main`:
   ```bash
   git checkout main
   ```

2. Pull latest changes:
   ```bash
   git pull origin main
   ```

3. Merge your feature branch:
   ```bash
   git merge feature/my-new-algo
   ```

4. Resolve any merge conflicts, then commit.

5. Push the updated `main`:
   ```bash
   git push origin main
   ```

6. (Optional) Delete the feature branch locally and remotely:
   ```bash
   git branch -d feature/my-new-algo
   git push origin --delete feature/my-new-algo
   ```

---

## Project Structure

```
backtestingAlgo/
├─ flask_app/           # Flask application package
│  ├─ __init__.py       # App factory and config
│  ├─ controllers/      # Blueprints (routes)
│  ├─ models/           # Core logic (backtester, strategies)
│  ├─ static/           # Static assets (JS, CSS)
│  └─ templates/        # Jinja2 templates (dash.html)
├─ server.py            # Entry point (finds free port, logging)
├─ requirements.txt     # Pinned dependencies
├─ Pipfile & Pipfile.lock
├─ .env                 # Environment variables (optional)
└─ README.md            # This file
```

---

Now you’re set! Happy backtesting and good luck with your trading algorithms! 🚀

