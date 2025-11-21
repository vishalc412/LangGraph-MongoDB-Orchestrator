# MongoDB AI Agent - Setup Scripts

This directory contains utility scripts for setting up and managing the MongoDB AI Agent.

## Scripts

### `setup_mongodb.py`

Sets up MongoDB with sample movie data for testing and demonstration.

**Usage:**

```bash
# Basic setup (uses defaults)
python scripts/setup_mongodb.py

# Custom database and collection
python scripts/setup_mongodb.py --database mydb --collection mycollection

# MongoDB Atlas (cloud)
python scripts/setup_mongodb.py --uri "mongodb+srv://user:pass@cluster.mongodb.net/"

# Drop existing data and start fresh
python scripts/setup_mongodb.py --drop-existing

# Custom data file
python scripts/setup_mongodb.py --data-file path/to/custom_data.json
```

**Options:**

- `--uri, -u`: MongoDB connection URI (default: `mongodb://localhost:27017`)
- `--database, -d`: Database name (default: `sample_mflix`)
- `--collection, -c`: Collection name (default: `movies`)
- `--data-file, -f`: Path to sample data JSON file (default: `data/sample_movies.json`)
- `--drop-existing`: Drop existing collection before inserting data

**Prerequisites:**

- MongoDB installed and running (local or cloud)
- Python dependencies installed: `pip install pymongo typer rich`

**What it does:**

1. Connects to MongoDB
2. Creates database and collection if they don't exist
3. Loads sample movie data from JSON file
4. Inserts data into collection
5. Creates indexes for common queries:
   - Index on `year`
   - Index on `genres`
   - Index on `imdb.rating` (descending)
   - Text index on `title` and `plot`

## MongoDB Setup Options

### Option 1: Local MongoDB

Install MongoDB locally:

```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Ubuntu/Debian
sudo apt-get install mongodb

# Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

Then run setup:

```bash
python scripts/setup_mongodb.py
```

### Option 2: MongoDB Atlas (Cloud)

1. Create a free MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Create a cluster
3. Get your connection string
4. Run setup with your connection string:

```bash
python scripts/setup_mongodb.py --uri "mongodb+srv://username:password@cluster.mongodb.net/"
```

### Option 3: Docker Compose

Use the provided `docker-compose.yml`:

```bash
docker-compose up -d mongodb
python scripts/setup_mongodb.py
```

## Verifying Setup

After running the setup script, verify it worked:

```bash
# Test connection
mongodb-agent test-connection

# Try a query
mongodb-agent query "What were the top-rated movies in 2020?"

# Start interactive chat
mongodb-agent chat
```

## Troubleshooting

### Connection Refused

- **Local MongoDB**: Make sure MongoDB is running: `brew services list` or `docker ps`
- **MongoDB Atlas**: Check your connection string and whitelist your IP address
- **Docker**: Ensure container is running: `docker ps`

### Authentication Failed

- Check your MongoDB username and password in the connection URI
- Ensure the user has read/write permissions on the database

### Data Not Inserted

- Check that the JSON data file exists and is valid JSON
- Verify you have write permissions on the database
- Check MongoDB logs for errors

## Sample Data

The sample data (`data/sample_movies.json`) contains 15 popular movies with:

- Title, year, director, cast
- Genres, runtime, plot
- IMDB rating and votes
- Countries and languages

You can modify this file or create your own data file with the same structure.

## Custom Data

To use your own data:

1. Create a JSON file with an array of documents
2. Use the `--data-file` option:

```bash
python scripts/setup_mongodb.py --data-file path/to/your_data.json
```

**Example custom data:**

```json
[
  {
    "name": "Product 1",
    "price": 99.99,
    "category": "Electronics",
    "stock": 50
  },
  {
    "name": "Product 2",
    "price": 49.99,
    "category": "Books",
    "stock": 100
  }
]
```
