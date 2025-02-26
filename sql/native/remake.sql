DROP SCHEMA IF EXISTS query_orchestrator CASCADE;
CREATE SCHEMA IF NOT EXISTS query_orchestrator;
CREATE TABLE IF NOT EXISTS query_orchestrator.schemas (
	id SERIAL PRIMARY KEY,
	name TEXT NOT NULL,
	"group" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS query_orchestrator.tables (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    "schema" INT NOT NULL,
    table_id TEXT NOT NULL,
    serial_id BOOLEAN NOT NULL,
    CONSTRAINT fk_schema FOREIGN KEY ("schema") 
        REFERENCES query_orchestrator.schemas(id) 
        ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS query_orchestrator.constraints (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    "table" INT NOT NULL,
    referenced_table INT NOT NULL,
    table_key TEXT NOT NULL,
    referenced_table_key TEXT NOT NULL,
    CONSTRAINT fk_table FOREIGN KEY ("table") 
        REFERENCES query_orchestrator.tables(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_referenced_table FOREIGN KEY (referenced_table) 
        REFERENCES query_orchestrator.tables(id) 
        ON DELETE CASCADE
);