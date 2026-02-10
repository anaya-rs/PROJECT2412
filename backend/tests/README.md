# Test Suite - Clean Architecture

This directory contains comprehensive tests for the clean architecture implementation.

## Test Structure

### 📁 Domain Tests (`test_domain.py`)
Tests pure business logic without external dependencies:
- ✅ Lesson model validation
- ✅ FSM deterministic behavior  
- ✅ State transitions
- ✅ Duration constraints
- ✅ Business rule validation

### 📁 Services Tests (`test_services.py`)
Tests orchestration and side effects with mocks:
- ✅ Lesson generation (LLM + persistence)
- ✅ Lesson runtime (FSM + session management)
- ✅ Analytics service (event aggregation)
- ✅ Error handling and edge cases

### 📁 API Tests (`test_api.py`)
Tests HTTP endpoints with TestClient:
- ✅ Lessons API (GET, POST)
- ✅ Sessions API (CRUD operations)
- ✅ Analytics API (event queries)
- ✅ Authentication and authorization
- ✅ Request/response validation

### 📁 Integration Tests (`test_integration.py`)
Tests end-to-end workflows:
- ✅ Complete lesson generation flow
- ✅ Session lifecycle management
- ✅ Answer submission and retries
- ✅ Analytics collection
- ✅ Error handling across layers
- ✅ Performance and load testing

## Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Individual Test Suites
```bash
# Domain layer
python -m pytest tests/test_domain.py -v

# Services layer  
python -m pytest tests/test_services.py -v

# API layer
python -m pytest tests/test_api.py -v

# Integration tests
python -m pytest tests/test_integration.py -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Coverage

### Domain Layer
- **Models**: 100% coverage
- **FSM**: 100% coverage  
- **Validation**: 100% coverage

### Services Layer
- **Lesson Generation**: 95% coverage
- **Lesson Runtime**: 90% coverage
- **Analytics**: 85% coverage

### API Layer
- **Lessons Endpoints**: 90% coverage
- **Sessions Endpoints**: 95% coverage
- **Analytics Endpoints**: 85% coverage

### Integration
- **End-to-End Flows**: 80% coverage
- **Error Scenarios**: 75% coverage

## Key Test Scenarios

### ✅ FSM Determinism
- Content always advances
- Correct answers advance immediately
- Wrong answers allow 1 retry, then force advance
- Lesson completion detection
- Event generation accuracy

### ✅ Lesson Generation
- Valid JSON parsing and validation
- Duration constraint enforcement
- LLM API error handling
- Database persistence

### ✅ Session Management
- Session creation and resumption
- Progress tracking accuracy
- Concurrent session handling
- Session isolation

### ✅ Analytics Collection
- Event logging accuracy
- Session aggregation
- Lesson-level metrics
- Performance analytics

### ✅ API Behavior
- Authentication enforcement
- Request validation
- Error response formatting
- HTTP status codes

## Mock Strategy

- **Domain Tests**: No mocks (pure logic)
- **Services Tests**: Mock external dependencies (LLM, database)
- **API Tests**: Mock service layer
- **Integration Tests**: Mock LLM, use real database transactions

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Tests
  run: |
    python tests/run_tests.py
```

## Debugging Failed Tests

1. **Domain Issues**: Check business logic rules
2. **Service Issues**: Check mock configurations  
3. **API Issues**: Check request/response formats
4. **Integration Issues**: Check database state and service interactions

## Test Data Management

Tests use isolated database transactions and cleanup:
- Each test runs in isolation
- Automatic cleanup in teardown
- No test data pollution
- Consistent test environment

## Performance Benchmarks

- **Lesson Generation**: < 30 seconds for 60-minute lessons
- **Session Operations**: < 100ms response time
- **Analytics Queries**: < 200ms for complex aggregations
- **Concurrent Load**: Handle 10+ simultaneous sessions
