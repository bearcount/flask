# Flask Instance Configuration

This directory contains instance-specific configuration for the Flask application.

## Files

- **instance.json** - Instance-level configuration (secrets, database, etc.)
- **config_loader.py** - Helper module for loading instance configuration
- **.gitkeep** - Ensures directory is tracked by git

## Purpose

The instance folder is Flask's recommended location for:

1. **Runtime-generated files** - Databases, caches, uploaded files
2. **Instance-specific configuration** - Secrets, API keys, environment-specific settings
3. **Instance-specific data** - User uploads, logs, temporary files

## Usage

### Loading Instance Configuration

```python
from flask import Flask
from instance.config_loader import init_app

app = Flask(__name__, instance_relative_config=True)
init_app(app)
```

### Using Factory Pattern

```python
from instance.config_loader import create_app

app = create_app()
```

### Accessing Instance Path

```python
from flask import current_app

instance_path = current_app.instance_path
db_path = os.path.join(instance_path, "flaskr.db")
```

## Security Notes

⚠️ **Important**: The `instance.json` file should NOT be committed to version control!

Add to your `.gitignore`:

```
instance/instance.json
instance/*.db
instance/*.log
```

Create a template file instead:

```bash
cp instance/instance.json instance/instance.json.example
```

Then create your actual config:

```bash
cp instance/instance.json.example instance/instance.json
# Edit instance.json with actual values
```

## Configuration Options

### Security

| Key | Description |
|-----|-------------|
| `SECRET_KEY` | Flask secret key for sessions |
| `SECRET_KEY_FALLBACKS` | Fallback secret keys |
| `SESSION_COOKIE_SECURE` | Require HTTPS for cookies |
| `SESSION_COOKIE_HTTPONLY` | Prevent JavaScript access |
| `SESSION_COOKIE_SAMESITE` | CSRF protection (Lax/Strict) |

### Database

| Key | Description |
|-----|-------------|
| `DATABASE_URI` | Database connection string |
| `UPLOAD_FOLDER` | Path for uploaded files |
| `MAX_UPLOAD_SIZE` | Maximum upload size in bytes |

### Caching

| Key | Description |
|-----|-------------|
| `CACHE_TYPE` | Cache backend (simple/redis/memcached) |
| `CACHE_DEFAULT_TIMEOUT` | Default cache TTL in seconds |
| `REDIS_URL` | Redis connection URL |

### Template Caching (New in 3.3)

| Key | Description |
|-----|-------------|
| `TEMPLATE_CACHE_MODE` | Cache mode: auto/hash/always/never |
| `TEMPLATE_CACHE_SIZE` | Maximum cached templates |
| `TEMPLATE_HASH_ALGO` | Hash algorithm: md5/sha1/sha256 |

### Logging

| Key | Description |
|-----|-------------|
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `LOG_FORMAT` | Log message format |

## Environment Variables

Override instance config using environment variables:

```bash
export FLASK_SECRET_KEY="your-production-secret"
export FLASK_DEBUG=0
export FLASK_DATABASE_URI="postgresql://user:pass@localhost/flask"
```

## Docker Usage

When using Docker, mount the instance folder:

```yaml
# docker-compose.yml
services:
  web:
    volumes:
      - ./instance:/app/instance
    environment:
      - FLASK_INSTANCE_PATH=/app/instance
```
