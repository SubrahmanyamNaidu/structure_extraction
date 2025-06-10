# Schema Extraction

## Postgres
pip install sqlalchemy psycopg2
DATABASE_URL = 'postgresql+psycopg2://postgres:postgres@localhost:5432/test_schema_db'
docker-compose up -d

## SQl
pip install sqlalchemy pymysql cryptography
DATABASE_URL = 'mysql+pymysql://user:password@localhost:3306/test_schema_db'
docker-compose up -d
