# API Authentication

This API uses API key authentication to secure endpoints.

## Configuration

The API key is configured via the `API_KEY` environment variable in `.env`:

```bash
API_KEY=ta_live_sk_c8f9e2a1b4d3c7f6a9b8d2e5f1c4a7b9e3d6f8a2c5b7d9e1f4a6c8b3d5e7f9a1
```

**Note**: If `API_KEY` is not set, authentication is **disabled** and all endpoints are publicly accessible.

## Using the API

### With Authentication (Recommended)

All `/api/v1/analyses` endpoints require the `X-API-Key` header:

```bash
# List all analyses
curl http://localhost:8000/api/v1/analyses \
  -H "X-API-Key: ta_live_sk_c8f9e2a1b4d3c7f6a9b8d2e5f1c4a7b9e3d6f8a2c5b7d9e1f4a6c8b3d5e7f9a1"

# Analyze a transcript
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  -H "X-API-Key: ta_live_sk_c8f9e2a1b4d3c7f6a9b8d2e5f1c4a7b9e3d6f8a2c5b7d9e1f4a6c8b3d5e7f9a1" \
  --data-urlencode "transcript=Your coaching session transcript here..."

# Get specific analysis
curl http://localhost:8000/api/v1/analyses/{id} \
  -H "X-API-Key: ta_live_sk_c8f9e2a1b4d3c7f6a9b8d2e5f1c4a7b9e3d6f8a2c5b7d9e1f4a6c8b3d5e7f9a1"
```

### Error Responses

**Missing API Key (401)**:
```json
{
  "detail": "API key required. Provide X-API-Key header."
}
```

**Invalid API Key (401)**:
```json
{
  "detail": "Invalid API key"
}
```

## Public Endpoints

The following endpoints do **NOT** require authentication:
- `GET /api/v1/health/live` - Liveness check
- `GET /api/v1/health/ready` - Readiness check
- `GET /docs` - API documentation (Swagger UI)
- `GET /redoc` - API documentation (ReDoc)

## Security Features

- **Structured Logging**: All authentication attempts are logged with timestamps
- **Partial Key Logging**: Only first 8 characters logged for invalid keys (security)
- **Graceful Degradation**: If API_KEY is not configured, authentication is disabled
- **Header-Based**: Uses standard `X-API-Key` header pattern

## Changing the API Key

1. Update `.env` file:
   ```bash
   API_KEY=your_new_secure_key_here
   ```

2. Restart the application:
   ```bash
   docker-compose restart app
   ```

3. Update all API clients with the new key

## Best Practices

1. **Keep Keys Secret**: Never commit API keys to version control
2. **Use Strong Keys**: Generate keys with high entropy (64+ characters)
3. **Rotate Regularly**: Change API keys periodically
4. **Environment Variables**: Always use `.env` file, never hardcode keys
5. **Monitor Logs**: Watch for suspicious authentication failures

## Generating Secure Keys

Use a strong random generator:

```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print('ta_live_sk_' + secrets.token_hex(32))"
```

## Production Considerations

For production deployments:
- Use a secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)
- Implement rate limiting (already configured with Redis backend)
- Consider implementing API key rotation
- Set up monitoring alerts for authentication failures
- Use HTTPS/TLS for all API communications
