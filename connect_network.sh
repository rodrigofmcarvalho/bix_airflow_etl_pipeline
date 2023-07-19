#!/bin/bash

# Containers to connect to the "bix" network
containers=("airflow-airflow-webserver-1" "airflow-airflow-worker-1" "airflow-airflow-scheduler-1" "airflow-airflow-triggerer-1" "airflow-redis-1" "airflow-postgres-1")

# Failure control variable
failed=0

# Connecting containers to the "bix" network
for container in "${containers[@]}"; do
  # Check if the container is already connected to the "bix" network
  if docker network inspect bix | grep -q "\"Name\": \"$container\""; then
    echo "Container $container is already connected to the bix network."
  else
    docker network connect bix "$container"
    if [[ $? -ne 0 ]]; then
      echo "Failed to connect container $container to the bix network."
      failed=1
    fi
  fi
done

# Checking if all containers were connected successfully
if [[ $failed -eq 0 ]]; then
  echo "All containers were connected to the bix network successfully."
else
  echo "Some containers failed to connect to the bix network."
fi

# Execute the "docker network inspect" command and store the output in a variable
network_info=$(docker network inspect bix)

# Extract the IP address of the PostgreSQL container from the output using regular expressions
postgres_ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' postgres)

# Check if the IP address is empty
if [[ -z "$postgres_ip" ]]; then
  echo "Failed to obtain the IP address of the PostgreSQL container."
else
  # Update the variable in the .env file with the IP address of the PostgreSQL container
  sed -i "s/^DB_TARGET_BIX_HOST =.*/DB_TARGET_BIX_HOST = '$postgres_ip'/" airflow/dags/.env

  # Display the IP address for verification
  echo "IP address of the PostgreSQL container: $postgres_ip"
fi
