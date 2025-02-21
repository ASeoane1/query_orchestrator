CREATE SCHEMA IF NOT EXISTS test1;

CREATE TABLE IF NOT EXISTS test1.employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
	manager INTEGER,
	FOREIGN KEY(manager) REFERENCES test1.employees(id)
);


CREATE TABLE IF NOT EXISTS test1.projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
	manager INTEGER REFERENCES test1.employees(id)
);

CREATE TABLE IF NOT EXISTS test1.employees_projects (
  employee_id INTEGER REFERENCES test1.employees(id),
  project_id INTEGER REFERENCES test1.projects(id),
  CONSTRAINT employees_projects_pk PRIMARY KEY(employee_id, project_id)
);