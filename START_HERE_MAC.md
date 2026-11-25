# Run Farmwise on your MacBook

This source package works with Intel and Apple silicon Macs using Python 3.11 or 3.12. It contains no Linux virtual environment or precompiled dependencies; your Mac installs the appropriate packages locally. Internet is needed for the first installation.

## 1. Install Python

If you do not have Python 3.11 or 3.12, install Python 3.12 from https://www.python.org/downloads/macos/ and follow its installer instructions. If the installer includes **Install Certificates.command**, run that once. The system-provided Python may be too old.

In Terminal, check:

```bash
python3.12 --version
```

## 2. Unzip the download

Double-click `farmer-advisory.zip` in Finder. It creates a folder named `farmer-advisory`. Keep that folder together: the app needs its `data` directory.

## 3. Start the app

Open Terminal. Type `cd ` (including the space), drag the extracted `farmer-advisory` folder into the Terminal window, and press Return. Then run:

```bash
bash run-mac.command
```

The launcher finds Python 3.12 or 3.11, creates a fresh `.venv`, installs the requirements on its first run, and starts Streamlit. If your browser does not open automatically, visit http://localhost:8501. Stop the server with Control-C in Terminal.

If you prefer manual setup:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Substitute `python3.11` if that is the supported version installed on your Mac. Later launches can use `bash run-mac.command` again. To update dependencies after editing requirements, activate `.venv` and run `python -m pip install -r requirements.txt`.

## 4. Try it without an API key

Leave **Offline demo** selected, choose an example and click **Generate advice**. The demo uses prewritten examples, not live AI, and deliberately shows no measured usage or cost.

For live AI, copy `.env.example` to `.env`, set `ANTHROPIC_API_KEY` and an available `ANTHROPIC_MODEL`, restart the app, and choose **Live API**. Finder hides dotfiles; use Command-Shift-Period to reveal `.env.example`, or run `cp .env.example .env` in Terminal. Keep your real `.env` private.

## 5. Run tests (optional)

```bash
source .venv/bin/activate
python -m pytest -q
```

## Troubleshooting

- **No compatible Python found:** install Python 3.12 and reopen Terminal.
- **Port 8501 is busy:** activate `.venv` and run `python -m streamlit run app.py --server.port 8502`, then open http://localhost:8502.
- **Certificates fail:** run the Python installer's Install Certificates.command, then retry; do not disable TLS verification.
- **A moved/copied `.venv` fails:** virtual environments are machine-specific. Rename the existing `.venv` folder and rerun the launcher to create one on this Mac.
- **API errors:** check your provider key, account's available model ID and quota. Offline demo needs none of these.

Verification: the automated tests ran on Linux with Python 3.12; execution on physical Mac hardware has not been tested. The package uses portable Python source and dependencies installed from PyPI for your platform.
