# PRD: Catalog Search Tool

**Version:** 1.0  
**Date:** October 23, 2025  
**Tool:** `catalog_search_tool`

---

## 1. Overview

LangChain tool for intelligent vehicle search with fuzzy matching and advanced filters. Enables natural language queries with typo tolerance.

### Purpose
- Search vehicles in PostgreSQL catalog
- Handle typos (e.g., "toyata" → "toyota")
- Filter by price, mileage, features
- Return structured results for AI agent

---

## 2. Technical Capabilities

### Fuzzy Matching
- **Engine:** rapidfuzz (token-based matching)
- **Threshold:** 80% similarity
- **Scope:** Make (brand) and Model
- **Performance:** <100ms per search

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| `budget_min` | float | Minimum price |
| `budget_max` | float | Maximum price |
| `make` | str | Brand (fuzzy matched) |
| `model` | str | Model (fuzzy matched) |
| `km_max` | int | Maximum mileage |
| `features` | List[str] | Required features |
| `sort_by` | str | Sorting ('price_low', 'price_high', 'year_new', 'km_low') |
| `max_results` | int | Results limit (default: 5, max: 20) |

---

## 3. Schemas

### Input Schema
- `budget_min`: Optional[float] - Minimum price
- `budget_max`: Optional[float] - Maximum price
- `make`: Optional[str] - Brand (fuzzy matched)
- `model`: Optional[str] - Model (fuzzy matched)
- `km_max`: Optional[int] - Maximum kilometers
- `features`: Optional[List[str]] - Required features (e.g., ['bluetooth', 'car_play'])
- `sort_by`: Optional[str] - Sorting method (default: "relevance")
- `max_results`: Optional[int] - Results limit (default: 5, max: 20)

### Output Schema
- `stock_id`: int - Unique vehicle identifier
- `make`: str - Vehicle brand
- `model`: str - Vehicle model
- `year`: int - Model year
- `version`: Optional[str] - Trim/version
- `price`: float - Vehicle price
- `km`: int - Mileage in kilometers
- `features`: Dict[str, bool] - Available features

**Return Type:** List of VehicleResult (0-20 items)

---

## 4. Usage Examples

### Natural Language Queries
| Query | Extracted Filters |
|-------|-------------------|
| "Find Toyota under $300k" | make='toyota', budget_max=300000 |
| "busco Honda con bluetooth" | make='honda', features=['bluetooth'] |
| "vehicles under 50000 km" | km_max=50000 |

---

## 5. Data Flow

```
1. User Query (natural language)
   ↓
2. Agent extracts preferences → catalog_search_tool
   ↓
3. Fuzzy match make/model (rapidfuzz)
   ↓
4. Build SQL query with filters
   ↓
5. PostgreSQL query via vehicle_dao
   ↓
6. Apply additional filters (features)
   ↓
7. Sort results
   ↓
8. Format as VehicleResult[]
   ↓
9. Return to agent
```

---

## 6. Implementation Details

### Fuzzy Matching Process
1. Retrieve all makes/models from database
2. Apply rapidfuzz token-based matching
3. Use 80% similarity threshold
4. Return best match or None

### Database Query
- Uses `vehicle_dao.search_vehicles()` for database access
- Filters: make, model, price range, mileage
- Additional post-query filtering for features
- Sorting applied after filtering

### CSV Data Format
Required columns: stock_id, km, price, make, model, year, version, bluetooth, car_play

---

## 7. Performance Targets (TBD)

| Metric | Target |
|---------|--------|
| Fuzzy matching | <100ms |
| Database query | <500ms |
| Total tool latency | <1s |
| Accuracy (fuzzy) | >90% |
| Results returned | 1-20 |

---

## 8. Error Handling

### Error Cases
1. **No match found:** Return empty list
2. **Invalid filters:** Pydantic validation error
3. **Database error:** Log error, return empty list
4. **Fuzzy match below threshold:** Return empty list

---

## 9. Database Schema

### Vehicle Model
- `stock_id`: int (Primary Key)
- `make`: str (Normalized lowercase)
- `model`: str (Normalized lowercase)
- `year`: int
- `version`: Optional[str]
- `km`: int
- `price`: float
- `features`: Optional[Dict] (JSON)
- `dimensions`: Optional[Dict] (JSON)

---

## 10. Current Limitations

- Fuzzy matching only on make/model
- Limited features in sample data (bluetooth, car_play only)
- No semantic search on descriptions
- No ML-based ranking
- No result caching

---

## 11. Testing Strategy

### Unit Tests
- Typo tolerance for make/model
- Price range filtering
- Feature requirements filtering
- Result sorting accuracy

### Integration Tests
- End-to-end agent search workflow
- Tool invocation with various queries
- Error handling scenarios

---

**File:** `src/tools/catalog_search.py`  
**Database:** PostgreSQL with SQLModel  
**Testing:** `tests/test_catalog_search_tool.py`
