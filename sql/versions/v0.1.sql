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
    CONSTRAINT fk_schema FOREIGN KEY ("schema") 
        REFERENCES query_orchestrator.schemas(id) 
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS query_orchestrator.constraints (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    origin_table INT NOT NULL,
    destination_table INT NOT NULL,
    origin_key TEXT NOT NULL,
    destination_key TEXT NOT NULL,
    CONSTRAINT fk_origin_table FOREIGN KEY (origin_table) 
        REFERENCES query_orchestrator.tables(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_destination_table FOREIGN KEY (destination_table) 
        REFERENCES query_orchestrator.tables(id) 
        ON DELETE CASCADE
);