import os
import discord
import datetime
import asyncio
import psycopg2
from opensearchpy import OpenSearch, RequestsHttpConnection
from dotenv import load_dotenv
import argparse
import json
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Load environment variables
load_dotenv()

# Command-line arguments
parser = argparse.ArgumentParser(description='Discord Message Fetcher')
parser.add_argument('--fetch-history', action='store_true', help='Fetch historical messages')
parser.add_argument('--no-fetch-history', dest='fetch_history', action='store_false', help='Do not fetch historical messages')
parser.add_argument('--use-postgresql', action='store_true', help='Enable PostgreSQL for storage')
parser.add_argument('--use-opensearch', action='store_true', help='Enable OpenSearch for storage')
parser.add_argument('--use-opentelemetry', action='store_true', help='Enable OpenTelemetry tracing')
parser.add_argument('--use-file-storage', action='store_true', help='Enable file-based storage for messages')
parser.add_argument('--output-file', type=str, help='Specify the output file to save messages', default='messages.json')
parser.add_argument('--log-file', type=str, help='Specify the log file location', default='message_fetcher.log')
args = parser.parse_args()

# Configuration
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_IDS = os.getenv('CHANNEL_IDS')
CHANNEL_IDS = [int(id.strip()) for id in CHANNEL_IDS.split(',')]
FETCH_HISTORY = args.fetch_history if args.fetch_history is not None else os.getenv('FETCH_HISTORY', 'true').lower() == 'true'
USE_POSTGRESQL = args.use_postgresql or os.getenv('USE_POSTGRESQL', 'false').lower() == 'true'
USE_OPENSEARCH = args.use_opensearch or os.getenv('USE_OPENSEARCH', 'false').lower() == 'true'
USE_OPENTELEMETRY = args.use_opentelemetry or os.getenv('USE_OPENTELEMETRY', 'false').lower() == 'true'
USE_FILE_STORAGE = args.use_file_storage or os.getenv('USE_FILE_STORAGE', 'false').lower() == 'true'

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'discord_messages')
DB_USER = os.getenv('DB_USER', 'your_db_username')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_db_password')

OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'localhost')
OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', 9200))

LAST_MESSAGE_ID_FILE = 'last_message_ids.json'

# Initialize logging
logging.basicConfig(level=logging.INFO, filename=args.log_file, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize OpenTelemetry Tracer only if enabled
if USE_OPENTELEMETRY:
    logging.info("OpenTelemetry is enabled")
    resource = Resource(attributes={"service.name": "discord-message-fetcher"})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)
    otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
else:
    logging.info("OpenTelemetry is disabled")
    tracer = None

# Initialize Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Load last message IDs
def load_last_message_ids():
    if os.path.exists(LAST_MESSAGE_ID_FILE):
        with open(LAST_MESSAGE_ID_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_last_message_ids(last_message_ids):
    with open(LAST_MESSAGE_ID_FILE, 'w') as f:
        json.dump(last_message_ids, f)

last_message_ids = load_last_message_ids()

# Database connection (PostgreSQL) only if enabled
if USE_POSTGRESQL:
    def get_db_connection():
        return psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
else:
    logging.info("PostgreSQL is disabled")
    get_db_connection = None

# OpenSearch client only if enabled
if USE_OPENSEARCH:
    opensearch_client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth=('username', 'password'),  # Adjust if authentication is enabled
        use_ssl=False,  # Set to True if SSL is enabled
        verify_certs=False,
        connection_class=RequestsHttpConnection
    )
else:
    logging.info("OpenSearch is disabled")
    opensearch_client = None

# Insert messages into PostgreSQL only if enabled
def insert_messages_pg(messages):
    if USE_POSTGRESQL and get_db_connection:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for message in messages:
                try:
                    cursor.execute("""
                        INSERT INTO messages (id, channel_id, author_id, content, timestamp, attachments)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING;
                    """, (
                        message.id,
                        message.channel.id,
                        message.author.id,
                        message.content,
                        message.created_at,
                        [attachment.url for attachment in message.attachments]
                    ))
                except Exception as e:
                    logging.error(f'Error inserting message {message.id}: {e}')
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.exception("Error connecting to PostgreSQL")
    else:
        logging.info("PostgreSQL is disabled or unavailable")

# Index messages into OpenSearch only if enabled
def index_messages_os(messages):
    if USE_OPENSEARCH and opensearch_client:
        for message in messages:
            doc = {
                'id': message.id,
                'channel_id': message.channel.id,
                'channel_name': message.channel.name,
                'author_id': message.author.id,
                'author_name': message.author.name,
                'content': message.content,
                'timestamp': message.created_at,
                'attachments': [attachment.url for attachment in message.attachments]
            }
            try:
                opensearch_client.index(index='discord_messages', body=doc, id=message.id)
            except Exception as e:
                logging.error(f'Error indexing message {message.id}: {e}')
    else:
        logging.info("OpenSearch is disabled or unavailable")

# File-based storage function
def store_messages_file(messages):
    with open(args.output_file, 'a', encoding='utf-8') as f:
        for message in messages:
            json.dump({
                'id': message.id,
                'channel_id': message.channel.id,
                'channel_name': message.channel.name,
                'author_id': message.author.id,
                'author_name': message.author.name,
                'content': message.content,
                'timestamp': str(message.created_at),
                'attachments': [attachment.url for attachment in message.attachments]
            }, f, ensure_ascii=False)
            f.write('\n')  # Newline after each message
    logging.info(f'Stored {len(messages)} messages in file {args.output_file}')

async def safe_channel_history(channel, **kwargs):
    messages = []
    while True:
        try:
            async for message in channel.history(**kwargs):
                messages.append(message)
            return messages
        except discord.errors.Forbidden:
            logging.warning(f"Missing permissions to access channel: {channel.name} (ID: {channel.id})")
            return []
        except discord.errors.HTTPException as e:
            if e.status == 429:
                logging.warning(f'Rate limit hit, sleeping for {e.retry_after} seconds')
                await asyncio.sleep(e.retry_after)
            else:
                logging.exception("HTTPException occurred while fetching channel history")
                raise e

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')
    while True:
        try:
            if USE_OPENTELEMETRY:
                span = tracer.start_as_current_span("fetch_messages")
            else:
                span = None

            for channel_id in CHANNEL_IDS:
                channel = client.get_channel(channel_id)
                if channel is None:
                    logging.warning(f'Cannot find channel with ID {channel_id}')
                    continue

                logging.info(f'Fetching messages from channel: {channel.name} (ID: {channel_id})')
                last_message_id = last_message_ids.get(str(channel_id))

                # Fetch new messages since last_message_id
                messages = await safe_channel_history(
                    channel,
                    limit=None,
                    after=discord.Object(id=last_message_id) if last_message_id else None
                )
                logging.info(f'Fetched {len(messages)} new messages from {channel.name}')

                # Process messages if any
                if messages:
                    # Update last_message_id
                    last_message_ids[str(channel_id)] = messages[0].id  # First message is the newest

                    # Process or store messages
                    if USE_POSTGRESQL:
                        insert_messages_pg(messages)
                    if USE_OPENSEARCH:
                        index_messages_os(messages)
                    if USE_FILE_STORAGE:
                        store_messages_file(messages)

                    logging.info(f'Total messages processed for {channel.name}: {len(messages)}')
                else:
                    logging.info(f'No new messages in {channel.name}')

                await asyncio.sleep(1)  # Respect rate limits

            # Save last_message_ids
            save_last_message_ids(last_message_ids)
            logging.info('Waiting for the next cycle...')
            await asyncio.sleep(60)  # Wait before checking for new messages

            if span:
                span.end()

        except Exception as e:
            logging.exception("An error occurred during the message fetching process")

client.run(TOKEN)
