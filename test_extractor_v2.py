from sqlalchemy import create_engine, inspect, MetaData, text
import json

# Replace with your connection string
# Examples:
# MySQL:       'mysql+pymysql://user:pass@localhost/dbname'
# PostgreSQL:  'postgresql+psycopg2://user:pass@localhost/dbname'
# SQLite:      'sqlite:///your.db'
DATABASE_URL = 'mysql+pymysql://user:password@localhost:3306/test_schema_db'



engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
metadata = MetaData()
metadata.reflect(bind=engine)

# Determine DB type
db_type = engine.name
schema_json = {"tables": {}}

# Function to get check constraints (Postgres/SQLite only)
def get_check_constraints_postgres(connection, table_name):
    # NOTE: Safe since `table_name` comes from SQLAlchemy's inspector
    sql = f"""
    SELECT conname, pg_get_constraintdef(oid) as definition
    FROM pg_constraint
    WHERE conrelid = '{table_name}'::regclass AND contype = 'c';
    """
    result = connection.execute(text(sql))
    return [row._mapping["definition"] for row in result]



def get_check_constraints_sqlite(connection, table_name):
    sql = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    result = connection.execute(text(sql)).fetchone()
    if result:
        sql_text = result[0]
        import re
        return re.findall(r'CHECK\s*\((.*?)\)', sql_text, re.IGNORECASE)
    return []

# Start extraction
with engine.connect() as conn:
    for table_name in inspector.get_table_names():
        table_info = {
            "columns": {},
            "primary_key": [],
            "foreign_keys": {},
            "unique_constraints": [],
            "indexes": [],
            "check_constraints": []
        }   

        # Primary Keys
        pk = inspector.get_pk_constraint(table_name)
        table_info["primary_key"] = pk.get("constrained_columns", [])

        # Foreign Keys
        for fk in inspector.get_foreign_keys(table_name):
            for col, ref_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                table_info["foreign_keys"][col] = {
                    "references": f"{fk['referred_table']}.{ref_col}"
                }

        # Unique Constraints
        for uc in inspector.get_unique_constraints(table_name):
            table_info["unique_constraints"].append(uc.get("column_names", []))

        # Indexes
        for idx in inspector.get_indexes(table_name):
            table_info["indexes"].append({
                "name": idx["name"],
                "columns": idx["column_names"],
                "unique": idx.get("unique", False)
            })

        # Check Constraints (Postgres/SQLite)
        if db_type == "postgresql":
            table_info["check_constraints"] = get_check_constraints_postgres(conn, table_name)
        elif db_type == "sqlite":
            table_info["check_constraints"] = get_check_constraints_sqlite(conn, table_name)

        # Columns
        for column in inspector.get_columns(table_name):
            col_name = column["name"]
            col_type = str(column["type"])
            nullable = column["nullable"]
            default = column.get("default", None)
            autoincrement = column.get("autoincrement", False)
            is_unique = any(col_name in uc for uc in table_info["unique_constraints"])
            is_primary = col_name in table_info["primary_key"]

            table_info["columns"][col_name] = {
                "type": col_type,
                "nullable": nullable,
                "default": default,
                "auto_increment": autoincrement,
                "unique": is_unique,
                "primary_key": is_primary
            }

        schema_json["tables"][table_name] = table_info

# Save to JSON file
with open("universal_sql_schema.json", "w") as f:
    json.dump(schema_json, f, indent=2)

print(f"✅ Schema extracted from `{db_type}` and saved to universal_sql_schema.json")
