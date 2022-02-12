# Document Scanner

Powered by [Streamlit](https://docs.streamlit.io/) + [AWS Textract](https://docs.aws.amazon.com/textract/latest/dg/what-is.html).
Specifically, Streamlit runs the user interaction and AWS Textract does the OCR.

In a business document context Textract is usually the preferred option over Rekognition.
This example uses the Detect Document Text function to extract text from documents.

It also provides a simple folder and basename entry which provide the path in S3 to save the uploaded image.

Detected text can be downloaded as the raw list of lines (json file), or can be editted and then downloaded as a paragraph (txt file).

In a business use case this would either be a submission to save the entry in system of record or otherwise continue the processing pipeline.

## Local Run

### Update AWS connection secrets

- Requires AWS Account with access to Textract service and Read/Write access to an S3 bucket ([AWS Tutorial](https://docs.aws.amazon.com/textract/latest/dg/getting-started.html))
- Copy or Rename `.env.example` as `.env.dev` and fill in AWS Access Key, Secret Key, Bucket Name, Region for your Rekognition account

```sh
mv .env.example .env.dev
```

### Run with Docker

Requires [docker-compose](https://docs.docker.com/compose/install/) to be installed (this comes with Docker Desktop).

```sh
docker-compose up
# Open localhost:8501 in a browser
```

Use `-d` to detach from logs.

Use `--build` on subsequent runs to rebuild dependencies / docker image.

### Lint, Check, Test with Docker

```sh
# Linting
docker-compose run streamlit-app nox.sh -s lint
# Unit Testing
docker-compose run streamlit-app nox.sh -s test
# Both
docker-compose run streamlit-app nox.sh
# As needed:
docker-compose build

# E2E Testing
docker-compose up -d --build
# Replace screenshots
docker-compose exec streamlit-app nox -s test -- -m e2e --visual-baseline
# Compare to visual baseline screenshots
docker-compose exec streamlit-app nox -s test -- -m e2e
# Turn off / tear down
docker-compose down
```

### Local Python environment

For code completion / linting / developing / etc.

```sh
python -m venv venv
. ./venv/bin/activate
# .\venv\Scripts\activate for Windows
python -m pip install -r ./streamlit_app/requirements.dev.txt
pre-commit install

# Linting / Static Checking / Unit Testing
python -m black streamlit_app
python -m isort --profile=black streamlit_app
python -m flake8 --config=./streamlit_app/.flake8 streamlit_app
```

## Features

- Containerization with [Docker](https://docs.docker.com/)
- Dependency installation with Pip
- Test automation with [Nox](https://nox.thea.codes/en/stable/index.html)
- Linting with [pre-commit](https://pre-commit.com/) and [Flake8](https://flake8.pycqa.org/en/latest/)
- Code formatting with [Black](https://black.readthedocs.io/en/stable/)
- Testing with [pytest](https://docs.pytest.org/en/6.2.x/getting-started.html)
- Code coverage with [Coverage.py](https://coverage.readthedocs.io/en/6.2/)
