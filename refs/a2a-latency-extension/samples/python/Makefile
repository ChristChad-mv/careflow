SHELL := /bin/bash

install:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

start:
	source venv/bin/activate && python start.py

server:
	source venv/bin/activate && \
	export $$(cat .env | xargs) && \
	python -u -m src.server.app
