# Introduction
This repository contains a small utility to interact with local Tuya-based thermostats.


## SETUP

```powershell
python -m tinytuya scan
```

```powershell
python -m tinytuya wizard
```

## Run app


```powershell
python moes_tuya_thermostat_bridge.py --tuya_dev_id="1234" --tuya_dev_ip="192.160.1.1" --tuya_dev_local_key="secret_key"
```








------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
## Windows: create, activate venv, and run

Follow these exact commands in a Windows terminal.

- Create a virtual environment (run from repository root):

```powershell
py -3 -m venv venv
```

- Activate the virtual environment:

```powershell
# If PowerShell blocks script execution, allow it for this session:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activate (dot + space ensures it runs in the current shell):
. .\.venv\Scripts\Activate.ps1
```

```bat
.venv\Scripts\activate
```

- Install dependencies (after activation):

```powershell
pip install -r requirements.txt
```

- Run the application:

```powershell
python moes_tuya_thermostat_bridge.py
```

## Build and Test

Instructions for building and testing go here.

