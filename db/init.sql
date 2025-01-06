-- Create the database
CREATE DATABASE nodered;

-- Connect to the database (only required if running commands interactively)
\c nodered;

-- Create the table for storing MQTT data
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    timestamp VARCHAR NOT NULL,
    ip VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    mac VARCHAR NOT NULL
);

CREATE TABLE servers_load (
    id SERIAL PRIMARY KEY,
    timestamp VARCHAR NOT NULL,
    ip VARCHAR NOT NULL,
    server_name VARCHAR NOT NULL,
    free_heap INTEGER NOT NULL,
    uptime INTEGER NOT NULL
);
