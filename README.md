# Introduction
This repository contains a small utility to interact with local Tuya-based thermostats.


## SETUP

Based on the TinyTuya project: https://github.com/jasonacox/tinytuya

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


## DOCKER CONTAINER

### Build Image

Command: Build and tag the image locally with a name and version:
```shell
docker build -t rtzan/thermostat_2_mqtt_bridge:1.0.0 -f Dockerfile .
```

List images: Verify the tag:
```shell
docker images rtzan/thermostat_2_mqtt_bridge
```

Run image:
```shell
docker run --rm -e "BRIDGE.TARGET_ENV=prod" -p 18000:18000 rtzan/thermostat_2_mqtt_bridge
```


### Build Container

Build + run with docker-compose:
```shell
docker compose up --build
```

The compose file sets `BRIDGE.TARGET_ENV=dev` by default. To run the container with the `prod` venv, override at runtime:

Using docker compose run:
```shell
docker compose run --rm -e "BRIDGE.TARGET_ENV=prod" app
```

Or create an `.env` or use an env-file:
```shell
echo 'BRIDGE.TARGET_ENV=prod' > .env
docker compose up --build
```

docker run --rm -e "BRIDGE.TARGET_ENV=prod" -p 8000:8000 rtzan/moes_thermostat_2_mqtt_bridge:1.0.0

Notes:
- The entrypoint uses Python to read `BRIDGE.TARGET_ENV` (because variable names with dots are not shell-friendly) and then execs the selected venv's Python interpreter.
- Venvs are created at image build time at `/opt/venvs/dev` and `/opt/venvs/prod`. Add packages to `requirements.txt` before building to have them installed into both venvs.











------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
## PYTHON PROJECT: Windows: create, activate venv, and run

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

