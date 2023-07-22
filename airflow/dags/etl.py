# Import necessary modules
import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from dotenv import load_dotenv
from sqlalchemy import create_engine, exc


def load_env_variables() -> None:
    """
    Load environment variables from the.env file.
    """

    load_dotenv()


# Define tasks(functions) to be executed
def create_engine_source_db() -> create_engine:
    """
    Create engine to connect to source database.
    """

    user = os.getenv('DB_SOURCE_BIX_USER')
    password = os.getenv('DB_SOURCE_BIX_PASSWORD')
    host = os.getenv('DB_SOURCE_BIX_HOST')
    port = os.getenv('DB_SOURCE_BIX_PORT')
    database = os.getenv('DB_SOURCE_BIX_DATABASE')

    return create_engine(
        f'postgresql://{user}:{password}@{host}:{port}/{database}'
    )


def create_engine_target_db() -> create_engine:
    """
    Create engine to connect to target database.
    """

    user = os.getenv('DB_TARGET_BIX_USER')
    password = os.getenv('DB_TARGET_BIX_PASSWORD')
    host = os.getenv('DB_TARGET_BIX_HOST')
    port = os.getenv('DB_TARGET_BIX_PORT')
    database = os.getenv('DB_TARGET_BIX_DATABASE')

    return create_engine(
        f'postgresql://{user}:{password}@{host}:{port}/{database}'
    )


def extract_postgresql_data() -> None:
    """
    Extract data from PostgreSQL database.
    """

    source_table_name = os.getenv('DB_SOURCE_POSTGRESQL_TABLE_NAME')
    target_table_name = os.getenv('DB_TARGET_POSTGRESQL_RAW_TABLE_NAME')

    engine = None

    try:
        engine = create_engine_source_db()

        query = f'SELECT * FROM {source_table_name};'
        df = pd.read_sql_query(query, engine)
        print(df)

    except exc.SQLAlchemyError as error:
        print(
            f'Error connecting to or extracting data from PostgreSQL: {error}'
        )
        raise

    except Exception as error:
        print(f'An unexpected error has occured: {error}')
        raise

    finally:
        if engine is not None:
            engine.dispose()

    load_data(target_table_name, df)


def extract_api_data() -> None:
    """
    Extract data from API.
    """

    base_url = os.getenv('API_SOURCE_BASE_URL')
    target_table_name = os.getenv('DB_TARGET_API_RAW_TABLE_NAME')
    employee_data = []

    for employee_id in range(1, 10):
        try:
            response = requests.get(base_url, params={'id': employee_id})
            if response.status_code == 200:
                employee_data.append(
                    {
                        'employee_id': employee_id,
                        'employee_name': response.text,
                    }
                )
            else:
                print(f'Error retriving data for employee ID: {employee_id}')

        except requests.RequestException as error:
            print(f'An error occurred while making the request: {error}')
            raise

        except Exception as error:
            print(f'An unexpected error has occured: {error}')
            raise

        df = pd.DataFrame(employee_data)
        print(df)

        load_data(target_table_name, df)


def extract_parquet_data() -> None:
    """
    Extract data from a parquet file.
    """

    base_url = os.getenv('PARQUET_SOURCE_BASE_URL')
    target_table_name = os.getenv('DB_TARGET_PARQUET_RAW_TABLE_NAME')

    try:
        df = pd.read_parquet(base_url)
        print(df)
    except Exception as error:
        print(f'An unexpected error has occured: {error}')
        raise

    load_data(target_table_name, df)


def transform_data() -> None:
    """
    Transform data and load into the target database.
    """

    target_table_name = os.getenv('DB_TARGET_TRANSFORMED_DATA_TABLE_NAME')

    try:
        engine = create_engine_target_db()
        query = """
                SELECT por.data_venda AS sale_date, par.nome_categoria AS category, apr.employee_name, SUM(por.venda) AS total_sales
                FROM postgresql_raw AS por
                INNER JOIN api_raw AS apr
                ON por.id_funcionario = apr.employee_id
                INNER JOIN parquet_raw AS par
                ON por.id_categoria = par.id
                GROUP BY por.data_venda, par.nome_categoria, apr.employee_name
                ORDER BY por.data_venda DESC, apr.employee_name, total_sales DESC;
                """
        df = pd.read_sql_query(query, engine)
        print(df)

    except exc.SQLAlchemyError as error:
        print(
            f'Error connecting to or extracting data from PostgreSQL: {error}'
        )
        raise

    except Exception as error:
        print(f'An unexpected error has occured: {error}')
        raise

    load_data(target_table_name, df)


def load_data(table_name: str, df: pd.DataFrame) -> None:
    """
    Load data into the target database.
    """

    if not isinstance(df, pd.DataFrame):
        print('Error: df must be a pandas DataFrame')
        return

    engine = None

    try:
        engine = create_engine_target_db()

        df.to_sql(table_name, engine, if_exists='append', index=False)
        print('Load process completed!')

    except exc.SQLAlchemyError as error:
        print(f'Error connecting to or saving data into PostgreSQL: {error}')
        raise

    except Exception as error:
        print(f'An unexpected error has ocurred: {error}')
        raise

    finally:
        if engine is not None:
            engine.dispose()


load_env_variables()


# Define default arguments for the DAG
default_args = {
    'owner': 'Rodrigo Carvalho',
    'depends_on_past': False,
    'start_date': datetime.today(),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Define the DAG context
with DAG(
    'etl',
    default_args=default_args,
    description='Perform ETL process',
    schedule='@daily',
    catchup=False,
) as dag:

    # Define tasks / operators using the PythonOperator
    t1 = PythonOperator(
        task_id='extract_postgresql_data',
        python_callable=extract_postgresql_data,
    )

    t2 = PythonOperator(
        task_id='extract_api_data',
        python_callable=extract_api_data,
    )

    t3 = PythonOperator(
        task_id='extract_parquet_data',
        python_callable=extract_parquet_data,
    )

    t4 = PythonOperator(
        task_id='transform_data', python_callable=transform_data
    )

# Set up dependencies between tasks / operators[t1, t2, t3] >> t4
[t1, t2, t3] >> t4
