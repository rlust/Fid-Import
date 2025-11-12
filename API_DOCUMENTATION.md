# REST API Documentation

Fidelity Portfolio Tracker provides a RESTful API for accessing portfolio data from mobile apps and external integrations.

## Base URL

```
http://localhost:8000
```

In production, replace with your domain.

## Authentication

Currently, the API does not require authentication. For production deployments, implement one of:

- API Keys
- JWT tokens
- OAuth 2.0

See [Security](#security) section for recommendations.

## Interactive Documentation

The API includes auto-generated documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### Health Check

Check if API is running.

**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-12T18:30:00"
}
```

---

### Portfolio Summary

Get current portfolio summary.

**GET** `/api/v1/portfolio/summary`

**Response:**
```json
{
  "total_value": 150000.50,
  "total_holdings": 15,
  "total_gain_loss": 12500.00,
  "total_return_percent": 9.09,
  "last_updated": "2024-11-12T18:00:00"
}
```

---

### Get Holdings

Get all current portfolio holdings.

**GET** `/api/v1/portfolio/holdings`

**Query Parameters:**
- `limit` (optional): Limit number of holdings returned

**Example Request:**
```bash
curl http://localhost:8000/api/v1/portfolio/holdings?limit=5
```

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "quantity": 100,
    "last_price": 150.00,
    "value": 15000.00,
    "cost_basis": 12000.00,
    "gain_loss": 3000.00,
    "gain_loss_percent": 25.0,
    "portfolio_weight": 10.0,
    "sector": "Technology",
    "industry": "Consumer Electronics"
  },
  ...
]
```

---

### Sector Allocation

Get portfolio allocation by sector.

**GET** `/api/v1/portfolio/sectors`

**Response:**
```json
[
  {
    "sector": "Technology",
    "value": 45000.00,
    "percentage": 30.0
  },
  {
    "sector": "Healthcare",
    "value": 30000.00,
    "percentage": 20.0
  },
  ...
]
```

---

### Top Holdings

Get top holdings by value.

**GET** `/api/v1/portfolio/top-holdings`

**Query Parameters:**
- `limit` (optional, default=10): Number of top holdings to return

**Example:**
```bash
curl http://localhost:8000/api/v1/portfolio/top-holdings?limit=3
```

---

### Historical Snapshots

Get list of historical snapshots.

**GET** `/api/v1/snapshots`

**Query Parameters:**
- `limit` (optional, default=10): Number of snapshots
- `days` (optional): Get snapshots from last N days

**Example:**
```bash
curl http://localhost:8000/api/v1/snapshots?days=30
```

**Response:**
```json
[
  {
    "id": 42,
    "timestamp": "2024-11-12T18:00:00",
    "total_value": 150000.50
  },
  {
    "id": 41,
    "timestamp": "2024-11-11T18:00:00",
    "total_value": 149500.00
  },
  ...
]
```

---

### Get Specific Snapshot

Get details of a specific snapshot.

**GET** `/api/v1/snapshots/{snapshot_id}`

**Parameters:**
- `snapshot_id`: Snapshot ID

**Example:**
```bash
curl http://localhost:8000/api/v1/snapshots/42
```

---

### Snapshot Holdings

Get holdings for a specific snapshot.

**GET** `/api/v1/snapshots/{snapshot_id}/holdings`

**Parameters:**
- `snapshot_id`: Snapshot ID

---

### Portfolio History

Get portfolio value over time.

**GET** `/api/v1/portfolio/history`

**Query Parameters:**
- `days` (optional, default=90): Number of days of history

**Response:**
```json
{
  "data": [
    {
      "timestamp": "2024-11-12T18:00:00",
      "total_value": 150000.50
    },
    {
      "timestamp": "2024-11-11T18:00:00",
      "total_value": 149500.00
    },
    ...
  ],
  "period_days": 90,
  "data_points": 45
}
```

## Error Responses

### 404 Not Found

```json
{
  "error": "Not found",
  "detail": "No portfolio data found"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/portfolio/summary")
@limiter.limit("10/minute")
async def get_portfolio_summary():
    ...
```

## CORS

CORS is enabled for all origins. For production, restrict to your domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

## Running the API

### Development

```bash
# Using Python directly
python -m fidelity_tracker.api.server

# Using uvicorn with auto-reload
uvicorn fidelity_tracker.api.server:app --reload --port 8000
```

### Production

```bash
# Using uvicorn with multiple workers
uvicorn fidelity_tracker.api.server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info

# Using gunicorn
gunicorn fidelity_tracker.api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Docker

```bash
docker-compose up api
```

## Security

### Recommended Security Measures

1. **API Key Authentication**

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY = "your-secret-api-key"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.get("/api/v1/portfolio/summary")
async def get_portfolio_summary(api_key: str = Depends(verify_api_key)):
    ...
```

2. **HTTPS Only**

Use a reverse proxy (nginx) to handle SSL:

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Rate Limiting**

Install slowapi:

```bash
pip install slowapi
```

4. **Input Validation**

Already handled by Pydantic models.

## Client Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Get portfolio summary
response = requests.get(f"{BASE_URL}/api/v1/portfolio/summary")
summary = response.json()
print(f"Total Value: ${summary['total_value']:,.2f}")

# Get top holdings
response = requests.get(f"{BASE_URL}/api/v1/portfolio/top-holdings?limit=5")
holdings = response.json()
for holding in holdings:
    print(f"{holding['symbol']}: ${holding['value']:,.2f}")

# Get portfolio history
response = requests.get(f"{BASE_URL}/api/v1/portfolio/history?days=30")
history = response.json()
print(f"Data points: {history['data_points']}")
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'http://localhost:8000';

// Get portfolio summary
async function getPortfolioSummary() {
  const response = await fetch(`${BASE_URL}/api/v1/portfolio/summary`);
  const summary = await response.json();
  return summary;
}

// Get holdings
async function getHoldings(limit = 10) {
  const response = await fetch(
    `${BASE_URL}/api/v1/portfolio/holdings?limit=${limit}`
  );
  const holdings = await response.json();
  return holdings;
}

// Get sector allocation
async function getSectorAllocation() {
  const response = await fetch(`${BASE_URL}/api/v1/portfolio/sectors`);
  const sectors = await response.json();
  return sectors;
}
```

### Swift (iOS)

```swift
import Foundation

class PortfolioAPI {
    let baseURL = "http://localhost:8000"

    func getPortfolioSummary(completion: @escaping (Result<PortfolioSummary, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/api/v1/portfolio/summary") else { return }

        URLSession.shared.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else { return }

            do {
                let summary = try JSONDecoder().decode(PortfolioSummary.self, from: data)
                completion(.success(summary))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}

struct PortfolioSummary: Codable {
    let totalValue: Double
    let totalHoldings: Int
    let totalGainLoss: Double?
    let totalReturnPercent: Double?
    let lastUpdated: String
}
```

### React Native

```typescript
import React, { useEffect, useState } from 'react';
import { View, Text, FlatList } from 'react-native';

const BASE_URL = 'http://localhost:8000';

const PortfolioScreen = () => {
  const [summary, setSummary] = useState(null);
  const [holdings, setHoldings] = useState([]);

  useEffect(() => {
    fetchPortfolioData();
  }, []);

  const fetchPortfolioData = async () => {
    try {
      // Get summary
      const summaryResponse = await fetch(`${BASE_URL}/api/v1/portfolio/summary`);
      const summaryData = await summaryResponse.json();
      setSummary(summaryData);

      // Get holdings
      const holdingsResponse = await fetch(`${BASE_URL}/api/v1/portfolio/holdings`);
      const holdingsData = await holdingsResponse.json();
      setHoldings(holdingsData);
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
    }
  };

  return (
    <View>
      {summary && (
        <Text>Total Value: ${summary.total_value.toFixed(2)}</Text>
      )}
      <FlatList
        data={holdings}
        keyExtractor={(item) => item.symbol}
        renderItem={({ item }) => (
          <View>
            <Text>{item.symbol}: ${item.value.toFixed(2)}</Text>
          </View>
        )}
      />
    </View>
  );
};

export default PortfolioScreen;
```

## WebSocket Support (Future)

For real-time updates, WebSocket support can be added:

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Send portfolio updates
        summary = get_portfolio_summary()
        await websocket.send_json(summary)
        await asyncio.sleep(60)  # Update every minute
```

## Testing

```bash
# Run all API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/portfolio/summary
curl http://localhost:8000/api/v1/portfolio/holdings
curl http://localhost:8000/api/v1/portfolio/sectors
curl http://localhost:8000/api/v1/snapshots

# Test with authentication (if implemented)
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/portfolio/summary
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/rlust/Fid-Import/issues
- API Documentation: http://localhost:8000/docs
