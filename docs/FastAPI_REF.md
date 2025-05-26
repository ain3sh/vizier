# Vizier API Documentation

## Overview

This document provides complete documentation for the Vizier backend API. The API enables seamless integration between the frontend and backend components of the research co-pilot system.

## Base URL

```
http://localhost:8000
```

## Authentication

### Headers

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Endpoints

#### OAuth Flow

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/callback` | OAuth callback handler |
| GET | `/auth/me` | Get current authenticated user info |

## Core Endpoints

### Queries

#### Create New Query

```http
POST /queries
```

Request body:
```json
{
  "query": "string"
}
```

Response:
```json
{
  "query_id": "uuid"
}
```

#### Get Query Status

```http
GET /queries/{query_id}
```

Response:
```json
{
  "query_id": "uuid",
  "user_id": "string",
  "query_text": "string",
  "refined_query": "string",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Start Query Refinement

```http
POST /queries/{query_id}/refine
```

Response:
```json
{
  "refined_query": "string"
}
```

#### Stream Query Progress

```http
GET /queries/stream/{query_id}
```

Server-Sent Events stream with the following event types:

```json
{
  "stage": "ProcessStage",
  "timestamp": "datetime",
  "data": {
    // Stage-specific data
  }
}
```

Process Stages:
- QUERY_RECEIVED
- REFINEMENT_STARTED
- REFINEMENT_COMPLETED
- ROUTING_STARTED
- ROUTING_COMPLETED
- WEB_SEARCH_STARTED
- WEB_SEARCH_COMPLETED
- TWITTER_SEARCH_STARTED
- TWITTER_SEARCH_COMPLETED
- SOURCE_RERANK_STARTED
- SOURCE_RERANK_COMPLETED
- SOURCE_REVIEW_READY
- SOURCE_REVIEW_COMPLETED
- WRITING_STARTED
- DRAFT_READY
- DRAFT_APPROVED
- COMPLETED

### Drafts

#### Generate Draft

```http
POST /drafts/generate
```

Request body:
```json
{
  "query_id": "uuid"
}
```

Response:
```json
{
  "draft_id": "uuid"
}
```

#### Get Draft

```http
GET /drafts/{draft_id}
```

Response:
```json
{
  "draft_id": "uuid",
  "query_id": "uuid",
  "content": "string",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Stream Draft Generation

```http
GET /drafts/stream/{draft_id}
```

Server-Sent Events stream with the following event types:

```json
{
  "type": "content_update",
  "content": "string",
  "timestamp": "datetime"
}
```

#### Accept Draft

```http
POST /drafts/{draft_id}/accept
```

Response:
```json
{
  "status": "accepted"
}
```

#### Reject Draft

```http
POST /drafts/{draft_id}/reject
```

Request body:
```json
{
  "feedback": "string"
}
```

Response:
```json
{
  "status": "rejected"
}
```

### Sources

#### Get Query Sources

```http
GET /queries/{query_id}/sources
```

Response:
```json
{
  "web_sources": [
    {
      "url": "string",
      "title": "string",
      "content": "string",
      "relevance_score": 0.95,
      "source_type": "web",
      "timestamp": "string",
      "metadata": {}
    }
  ],
  "twitter_sources": [
    {
      "url": "string",
      "title": "string",
      "content": "string",
      "relevance_score": 0.85,
      "source_type": "twitter",
      "timestamp": "string",
      "metadata": {}
    }
  ]
}
```

#### Submit Source Review

```http
POST /queries/{query_id}/sources/review
```

Request body:
```json
{
  "included": ["url1", "url2"],
  "excluded": ["url3"],
  "reranked_urls": ["url2", "url1"]
}
```

Response:
```json
{
  "status": "success",
  "source_count": 2
}
```

### User Management

#### Get User Profile

```http
GET /user/me
```

Response:
```json
{
  "user_id": "string",
  "email": "string",
  "name": "string",
  "preferences": {
    // User preferences
  }
}
```

#### Update User Profile

```http
POST /user/profile
```

Request body:
```json
{
  "name": "string",
  "preferences": {
    // Updated preferences
  }
}
```

## Data Models

### ProcessStage

Enum representing different stages in the query processing pipeline:

```typescript
enum ProcessStage {
  QUERY_RECEIVED = "query_received",
  REFINEMENT_STARTED = "refinement_started",
  REFINEMENT_COMPLETED = "refinement_completed",
  ROUTING_STARTED = "routing_started",
  ROUTING_COMPLETED = "routing_completed",
  WEB_SEARCH_STARTED = "web_search_started",
  WEB_SEARCH_COMPLETED = "web_search_completed",
  TWITTER_SEARCH_STARTED = "twitter_search_started",
  TWITTER_SEARCH_COMPLETED = "twitter_search_completed",
  SOURCE_RERANK_STARTED = "source_rerank_started",
  SOURCE_RERANK_COMPLETED = "source_rerank_completed",
  SOURCE_REVIEW_READY = "source_review_ready",
  SOURCE_REVIEW_COMPLETED = "source_review_completed",
  WRITING_STARTED = "writing_started",
  DRAFT_READY = "draft_ready",
  DRAFT_APPROVED = "draft_approved",
  COMPLETED = "completed"
}
```

### Query Status

String enum representing query statuses:

```typescript
type QueryStatus = "pending" | "processing" | "completed" | "error"
```

### Draft Status

String enum representing draft statuses:

```typescript
type DraftStatus = "writing" | "completed" | "accepted" | "rejected"
```

### SourceItem

```typescript
interface SourceItem {
  url: string;
  title: string;
  content: string;
  relevance_score: number;
  source_type: "web" | "twitter";
  timestamp?: string;
  metadata: Record<string, any>;
}
```

### SourceReview

```typescript
interface SourceReview {
  included: string[];  // List of source URLs to include
  excluded: string[];  // List of source URLs to exclude
  reranked_urls: string[];  // Sources in desired order
}
```

## Error Handling

The API uses standard HTTP status codes and returns error responses in the following format:

```json
{
  "detail": "Error message"
}
```

Common status codes:
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Event Streams

The API uses Server-Sent Events (SSE) for real-time updates. The frontend should implement proper SSE handling:

```typescript
const eventSource = new EventSource(`/queries/stream/${queryId}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle event data
};

eventSource.onerror = (error) => {
  // Handle error
  eventSource.close();
};
```

## Frontend Integration Example

Here's a complete example of frontend integration using TypeScript and the Fetch API:

```typescript
async function createQuery(query: string): Promise<string> {
  const response = await fetch('/queries', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });
  
  if (!response.ok) {
    throw new Error('Failed to create query');
  }
  
  const data = await response.json();
  return data.query_id;
}

function subscribeToQueryProgress(queryId: string, callbacks: {
  onStageChange: (stage: ProcessStage, data: any) => void,
  onError: (error: any) => void,
  onComplete: () => void
}): () => void {
  const eventSource = new EventSource(`/queries/stream/${queryId}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    callbacks.onStageChange(data.stage, data.data);
    
    if (data.stage === 'COMPLETED') {
      eventSource.close();
      callbacks.onComplete();
    }
  };
  
  eventSource.onerror = (error) => {
    callbacks.onError(error);
    eventSource.close();
  };
  
  return () => eventSource.close();
}

async function getQuerySources(queryId: string): Promise<{web_sources: SourceItem[], twitter_sources: SourceItem[]}> {
  const response = await fetch(`/queries/${queryId}/sources`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch sources');
  }
  
  return response.json();
}

async function submitSourceReview(queryId: string, review: SourceReview): Promise<{status: string, source_count: number}> {
  const response = await fetch(`/queries/${queryId}/sources/review`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(review)
  });
  
  if (!response.ok) {
    throw new Error('Failed to submit source review');
  }
  
  return response.json();
}
```

## Rate Limiting

- Standard rate limit: 100 requests per minute per user
- Draft generation: 10 requests per minute per user
- SSE connections: Maximum 5 concurrent connections per user

## Best Practices

1. Always include error handling for both HTTP requests and SSE streams
2. Implement proper cleanup of SSE connections when components unmount
3. Use TypeScript types/interfaces for better type safety
4. Implement exponential backoff for failed requests
5. Cache responses when appropriate
6. Include authorization headers with every request
7. Validate input before sending to the API

## Notes for Development

1. The API is designed to be RESTful and follows standard HTTP conventions
2. All endpoints support CORS for localhost development
3. JWT tokens should be stored securely in the frontend
4. SSE connections will automatically timeout after 30 minutes of inactivity
5. The API supports both JSON and form-data for file uploads

## Testing

Test endpoints are available in development:

```http
GET /test/auth
GET /test/queries
GET /test/drafts
```

These endpoints don't require authentication and return mock data for frontend testing.