# Discord Message Fetcher Documentation

## Overview

The **Discord Message Fetcher** is a Python script designed to fetch messages from specified Discord channels and store them using various backends such as PostgreSQL, OpenSearch, InfluxDB, or simply save them to a file. It can be configured to fetch historical messages as well as new messages on an ongoing basis. The script is highly configurable through command-line arguments and environment variables, making it flexible for different use cases.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Command-Line Arguments](#command-line-arguments)
- [Usage](#usage)
  - [Running the Script](#running-the-script)
  - [Sample Commands](#sample-commands)
- [Storage Options](#storage-options)
  - [File-Based Storage](#file-based-storage)
  - [PostgreSQL Storage](#postgresql-storage)
  - [OpenSearch Storage](#opensearch-storage)
  - [InfluxDB Storage](#influxdb-storage)
- [Logging and Monitoring](#logging-and-monitoring)
- [OpenTelemetry Tracing](#opentelemetry-tracing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Features

- Fetch messages from one or multiple Discord channels.
- Support for fetching historical messages.
- Storage backends:
  - File-based storage (JSON format).
  - PostgreSQL database.
  - OpenSearch indexing.
  - InfluxDB for time-series data.
- Optional OpenTelemetry tracing for monitoring.
- Configurable via environment variables and command-line arguments.
- Logging support with customizable log file location.

## Prerequisites

- **Python 3.7 or higher**: Ensure you have Python installed on your system.
- **Discord Bot Token**: You need a Discord bot token to authenticate and connect to Discord.
- **Discord.py Library**: The script uses the `discord.py` library for interacting with Discord.
- **Dependencies**: Other libraries include `psycopg2`, `opensearch-py`, `influxdb-client`, `python-dotenv`, `argparse`, and `opentelemetry`.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/nthuls/Discord_bot.git
   cd Discord_bot
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   If a `requirements.txt` file is not provided, you can install the dependencies manually:

   ```bash
   pip install discord.py psycopg2-binary opensearch-py python-dotenv argparse influxdb-client opentelemetry-sdk opentelemetry-exporter-otlp
   ```

## Configuration

### Environment Variables

The script uses environment variables for configuration. You can set them in a `.env` file in the root directory or export them in your shell environment.

Here's an example of a `.env` file:

```dotenv
# Discord Bot Configuration
DISCORD_BOT_TOKEN=place-your-bot-token-here
CHANNEL_IDS=channelid0,channelid1

# Fetch History
FETCH_HISTORY=true

# Storage Options
USE_FILE_STORAGE=true
USE_POSTGRESQL=true
USE_OPENSEARCH=false
USE_INFLUXDB=true

# OpenTelemetry
USE_OPENTELEMETRY=false

# PostgreSQL Configuration
DB_HOST=localhost
DB_NAME=discord_messages
DB_USER=your_db_username
DB_PASSWORD=your_db_password

# OpenSearch Configuration
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200

# InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086/
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=Discord_bot
```

**Note:** Ensure that the `CHANNEL_IDS` are the IDs of the Discord channels you wish to monitor, separated by commas.

### Command-Line Arguments

The script also supports command-line arguments to override configurations:

- `--fetch-history` / `--no-fetch-history`: Enable or disable fetching historical messages.
- `--use-postgresql`: Enable PostgreSQL storage.
- `--use-opensearch`: Enable OpenSearch storage.
- `--use-opentelemetry`: Enable OpenTelemetry tracing.
- `--use-file-storage`: Enable file-based storage.
- `--use-influxdb`: Enable InfluxDB storage.
- `--output-file <filename>`: Specify the output file for messages when using file storage.
- `--log-file <filename>`: Specify the log file location.

**Note:** Command-line arguments take precedence over environment variables.

## Usage

### Running the Script

Make sure you have configured your environment variables or have a `.env` file in place.

Run the script using Python:

```bash
python discord_message_fetcher.py [options]
```

### Sample Commands

1. **Fetch messages and store in a file:**

   ```bash
   python discord_message_fetcher.py --use-file-storage --output-file messages.json
   ```

2. **Fetch messages and store in PostgreSQL:**

   ```bash
   python discord_message_fetcher.py --use-postgresql
   ```

3. **Fetch messages, store in InfluxDB, and enable OpenTelemetry tracing:**

   ```bash
   python discord_message_fetcher.py --use-influxdb --use-opentelemetry
   ```

4. **Disable fetching historical messages and store in OpenSearch:**

   ```bash
   python discord_message_fetcher.py --no-fetch-history --use-opensearch
   ```

5. **Specify a custom log file:**

   ```bash
   python discord_message_fetcher.py --log-file custom_log.log
   ```

6. **Fetch messages using all storage options:**

   ```bash
   python discord_message_fetcher.py --use-file-storage --use-postgresql --use-opensearch --use-influxdb
   ```

**Note:** Replace `discord_message_fetcher.py` with the actual name of your script file if it's different.

## Storage Options

### File-Based Storage

If `USE_FILE_STORAGE` is set to `true` or `--use-file-storage` is passed, messages will be stored in a JSON file specified by `--output-file` or defaulting to `messages.json`.

**Example:**

```bash
python discord_message_fetcher.py --use-file-storage --output-file messages.json
```

**Sample Output in `messages.json`:**

```json
{
  "id": 123456789012345678,
  "channel_id": 123456789012345678,
  "channel_name": "general",
  "author_id": 123456789012345678,
  "author_name": "Username",
  "content": "Hello, world!",
  "timestamp": "2023-10-01 12:34:56.789000",
  "attachments": []
}
```

### PostgreSQL Storage

To store messages in PostgreSQL, ensure that `USE_POSTGRESQL` is set to `true` or use the `--use-postgresql` flag. Also, configure the database connection settings.

**Environment Variables:**

- `DB_HOST`: Database host, default is `localhost`.
- `DB_NAME`: Database name.
- `DB_USER`: Database username.
- `DB_PASSWORD`: Database password.

**Example:**

```bash
python discord_message_fetcher.py --use-postgresql
```

**Note:** Ensure that the `messages` table exists in your PostgreSQL database. Here's a sample SQL statement to create the table:

```sql
CREATE TABLE messages (
    id BIGINT PRIMARY KEY,
    channel_id BIGINT,
    author_id BIGINT,
    content TEXT,
    timestamp TIMESTAMP,
    attachments TEXT[]
);
```

### OpenSearch Storage

To index messages in OpenSearch, set `USE_OPENSEARCH` to `true` or use the `--use-opensearch` flag. Configure the OpenSearch connection settings.

**Environment Variables:**

- `OPENSEARCH_HOST`: OpenSearch host, default is `localhost`.
- `OPENSEARCH_PORT`: OpenSearch port, default is `9200`.

**Example:**

```bash
python discord_message_fetcher.py --use-opensearch
```

**Note:** Ensure that your OpenSearch instance is running and accessible. Adjust the `http_auth` parameter in the script if authentication is required.

### InfluxDB Storage

For time-series data storage in InfluxDB, set `USE_INFLUXDB` to `true` or use the `--use-influxdb` flag. Configure the InfluxDB connection settings.

**Environment Variables:**

- `INFLUXDB_URL`: InfluxDB URL, e.g., `http://localhost:8086/`.
- `INFLUXDB_TOKEN`: InfluxDB authentication token.
- `INFLUXDB_ORG`: InfluxDB organization name.
- `INFLUXDB_BUCKET`: InfluxDB bucket name where data will be stored.

**Example:**

```bash
python discord_message_fetcher.py --use-influxdb
```

**Note:** Ensure that your InfluxDB instance is running and accessible.

**Sample Data Point in InfluxDB:**

Each message is stored as a data point with tags and fields, including the message content, author, and timestamp.

### Combined Storage Options

You can enable multiple storage options simultaneously. For example, to store messages in both PostgreSQL and InfluxDB:

```bash
python discord_message_fetcher.py --use-postgresql --use-influxdb
```

## Logging and Monitoring

The script uses the `logging` module to log information and errors. By default, logs are written to `message_fetcher.log`. You can specify a different log file using the `--log-file` argument.

**Example:**

```bash
python discord_message_fetcher.py --log-file my_custom_log.log
```

**Sample Log Entry:**

```
2023-10-01 12:34:56,789 - INFO - Logged in as YourBotName#1234
```

## OpenTelemetry Tracing

If `USE_OPENTELEMETRY` is set to `true` or the `--use-opentelemetry` flag is used, the script will enable OpenTelemetry tracing. This is useful for monitoring and debugging purposes.

**Environment Variables:**

- `USE_OPENTELEMETRY`: Set to `true` to enable.

**Example:**

```bash
python discord_message_fetcher.py --use-opentelemetry
```

**Note:**

- Ensure that you have an OpenTelemetry Collector or compatible endpoint running to collect the traces.
- The script is configured to export traces to `localhost:4317` using gRPC. Adjust the `endpoint` and `insecure` parameters in the script if needed.

## Troubleshooting

- **Cannot connect to Discord:**

  - Ensure that your bot token (`DISCORD_BOT_TOKEN`) is correct.
  - Verify that the bot is invited to the server and has the necessary permissions to read messages.

- **Database connection errors:**

  - Double-check your database connection settings (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
  - Ensure that the database server is running and accessible.
  - For PostgreSQL, ensure that the `psycopg2` package is installed (`psycopg2-binary` might be easier to install).

- **Permission errors accessing channels:**

  - The bot may not have permissions to read messages from certain channels.
  - Adjust the bot's permissions in your Discord server or check channel-specific permissions.

- **Rate limiting:**

  - The script includes handling for rate limits, but if you encounter rate limit errors, consider reducing the frequency of message fetching.
  - The script sleeps for `60` seconds after each fetch cycle.

- **Missing dependencies:**

  - Ensure all required Python packages are installed.
  - Use `pip install -r requirements.txt` to install dependencies from a requirements file.

- **Errors related to OpenTelemetry or InfluxDB:**

  - Ensure that the respective services are running and accessible.
  - Verify the connection settings and authentication tokens.

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/nthuls/Discord_bot.git).

---

**Note:** This documentation is based on the provided script and assumes that the script filename is `discord_message_fetcher.py`. Adjust the filename in the commands if your script has a different name.
