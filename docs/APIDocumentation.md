# API Documentation

## Overview

The Distributed Caching System provides a RESTful API to interact with the cache. This API supports standard cache operations like adding, retrieving, and deleting cache entries, as well as management operations.

## Endpoints

### 1. Cache Operations

#### GET /cache/{key}

- **Description**: Retrieve a cache entry by its key.
- **Response**: The cached value or a 404 if not found.
- **Methods**: GET
- **Status Codes**:
  - 200: Success
  - 404: Not Found

#### POST /cache

- **Description**: Add a new cache entry or update an existing one.
- **Request Body**:

  ```json
  {
    "key": "string",
    "value": "string",
    "ttl": "integer (optional)"
  }
  ```

- **Methods**: POST
- **Status Codes**:
  - 201: Created
  - 400: Bad Request

#### DELETE /cache/{key}

- **Description**: Delete a cache entry by its key.
- **Methods**: DELETE
- **Status Codes**:
  - 200: Success
  - 404: Not Found

### 2. Admin Operations

#### GET /nodes

- **Description**: Retrieve the list of active cache nodes.
- **Methods**: GET
- **Status Codes**:
  - 200: Success

#### POST /nodes/add

- **Description**: Add a new cache node to the system.
- **Request Body**:

  ```json
  {
    "address": "string"
  }
  ```

- **Methods**: POST
- **Status Codes**:
  - 201: Created
  - 400: Bad Request
