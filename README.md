# GPU Jupyter Admin

A Flask web interface to manage JupyterLab sessions with user authentication and session logging for shared GPU resources.
This is a simple interface made because the machine I had available could not run Jupyterhub but I still needed a way to 
manage user access for the students of a machine learning course.

This is a simple solution made for use in the same private network through ipv4 only. I would only use this in a trusted
environment.

## Features
- User registration and login
- Password protection on JupyterLab instances
- Session locking and release
- Admin view for logs and force-release
- Local IP-based JupyterLab startup

## Usage

Configure generate_env.py to suit your needs for the first time and simply run setup.py. Make sure to change DEV_MODE to "False" once satisfied.

```bash
python setup.py
```

You can just run run.py for future use, such as on a task on computer startup.

```bash
python run.py
```