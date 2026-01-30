# ml-tech-assessment

## Environment Setup

### Using Conda (Recommended)

1. Install Conda if you haven't already:
   - Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)

2. Create and activate a new conda environment:
   ```bash
   conda create -n ml-assessment python=3.12
   conda activate ml-assessment
   ```

## Installing Poetry and Dependencies

1. Install Poetry using pip:
   ```bash
   pip install poetry
   ```

2. Install project dependencies:
   ```bash
   poetry install
   ```

## Environment Variables

1. Create a `.env` file in the root directory of the project
2. Copy the contents of the provided `.env` file into your local `.env` file

## Running the API

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/transcripts/analyze` | Analyze a single transcript |
| GET | `/transcripts/{id}` | Get analysis by ID |
| POST | `/transcripts/analyze/batch` | Analyze multiple transcripts concurrently |
| GET | `/health` | Health check |

## Running Tests

To run the tests, make sure you have:
1. Activated your virtual environment
2. Installed all dependencies using Poetry
3. Created and populated the `.env` file

Then run:
```bash
pytest
```

For more detailed test output:
```bash
pytest -v
```

For test coverage report:
```bash
pytest --cov
```
