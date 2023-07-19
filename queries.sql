EATE USER bix_user WITH ENCRYPTED PASSWORD 'bix_password';
ALTER USER bix_user CREATEDB;
CREATE DATABASE bix_db;
GRANT ALL PRIVILEGES ON DATABASE bix_db TO bix_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO bix_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bix_user;

--RAW TABLES DEFINITION
CREATE TABLE postgresql_raw (
id_venda INT,
id_funcionario INT,
id_categoria INT,
data_venda DATE,
venda INT4
);

CREATE TABLE api_raw (
employee_id INT,
employee_name VARCHAR
);

CREATE TABLE parquet_raw (
id INT,
nome_categoria VARCHAR
);

--TRANSFORMED TABLE DEFINITION
CREATE TABLE transformed_data (
id SERIAL PRIMARY KEY NOT NULL,
sale_date DATE NOT NULL,
category VARCHAR NOT NULL,
employee_name VARCHAR NOT NULL,
total_sales FLOAT NOT NULL
);
