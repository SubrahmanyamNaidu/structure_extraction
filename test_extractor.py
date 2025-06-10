from sqlalchemy import create_engine, inspect, MetaData
import json

# Replace with your DB URL
DATABASE_URL = 'mysql+pymysql://username:password@localhost/dbname'

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
metadata = MetaData()
metadata.reflect(bind=engine)

schema_json = {"tables": {}}

for table_name in inspector.get_table_names():
    table_info = {
        "columns": {},
        "primary_key": [],
        "foreign_keys": {},
        "unique_constraints": [],
        "indexes": []
    }

    # Primary Key
    pk = inspector.get_pk_constraint(table_name)
    table_info["primary_key"] = pk.get("constrained_columns", [])

    # Foreign Keys
    fks = inspector.get_foreign_keys(table_name)
    for fk in fks:
        for col, ref_col in zip(fk["constrained_columns"], fk["referred_columns"]):
            table_info["foreign_keys"][col] = {
                "references": f"{fk['referred_table']}.{ref_col}"
            }

    # Unique Constraints
    unique_constraints = inspector.get_unique_constraints(table_name)
    for uc in unique_constraints:
        table_info["unique_constraints"].append(uc.get("column_names", []))

    # Indexes
    indexes = inspector.get_indexes(table_name)
    for idx in indexes:
        table_info["indexes"].append({
            "name": idx["name"],
            "columns": idx["column_names"],
            "unique": idx.get("unique", False)
        })

    # Columns
    for column in inspector.get_columns(table_name):
        col_name = column["name"]
        col_type = str(column["type"])
        nullable = column["nullable"]
        default = column.get("default", None)
        autoincrement = column.get("autoincrement", False)

        is_unique = any(
            col_name in uc for uc in table_info["unique_constraints"]
        )
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
with open("enhanced_sql_schema.json", "w") as f:
    json.dump(schema_json, f, indent=2)

print("✅ Enhanced schema extracted and saved to enhanced_sql_schema.json")
