# Financial Lineage Graph - Design Documentation

**Version:** 1.0
**Date:** 2026-01-07
**Purpose:** Graph-based lineage tracking for financial transformations

---

## Overview

The Financial Lineage Graph redesigns internal tracing from **flat tables** to a **directed acyclic graph (DAG)** structure, enabling powerful provenance queries and audit trails.

### Why Graph vs. Tables?

| Aspect | Flat Tables | Graph |
|--------|-------------|-------|
| **Relationships** | Foreign keys | Native edges |
| **Many-to-one** | Complex joins | Single traversal |
| **Path finding** | Recursive CTEs | Dijkstra's algorithm |
| **Conditional logic** | Multiple tables | Edge attributes |
| **Query complexity** | O(n²) joins | O(E) traversal |

---

## Graph Structure

### Nodes = Financial Facts

```
SourceCellNode → ExtractedNode → MappedNode → AggregatedNode → CalculatedNode
     |               |               |              |                |
   Excel         messy CSV      normalized CSV    pivoted        DCF/LBO
   B5:$100K     "Total Sales"   us-gaap_Revenues  $100K         Revenue
```

**Node Types:**
1. `SOURCE_CELL` - Excel cell (sheet, row, col, value)
2. `EXTRACTED` - Extracted row (label, amount, period)
3. `MAPPED` - Normalized row (concept, value, period)
4. `AGGREGATED` - Pivoted value (concept+period → single value)
5. `CALCULATED` - Derived value (formula result)

**Node Attributes:**
- `node_id`: Unique identifier
- `concept`: XBRL concept (if known)
- `label`: Human-readable label
- `value`: The actual value
- `period`: Time period
- `is_active`: False if superseded

### Edges = Transformations

```python
# Many-to-one (aggregation)
[Cell1, Cell2, Cell3] --[AGGREGATION]--> AggregatedValue

# One-to-one (mapping)
ExtractedRow --[MAPPING]--> MappedRow

# One-to-many (calculation)
Revenue --[CALCULATION]--> [EBITDA, GrossProfit, ...]
```

**Edge Types:**
1. `EXTRACTION` - Excel → Extracted
2. `MAPPING` - Label → Concept
3. `AGGREGATION` - Many → One (hierarchy-aware)
4. `CALCULATION` - Formula
5. `SUPERSEDED` - Old edge → New edge (analyst brain)

**Edge Attributes:**
- `edge_id`: Unique identifier
- `source_node_ids`: List of source nodes (supports many-to-one)
- `target_node_id`: Single target node
- `method`: Human-readable method
- `confidence`: 0.0 to 1.0
- `source`: MappingSource enum (analyst_brain, alias, exact_label, keyword, hierarchy)
- `is_active`: False if path not taken
- `condition`: Why this path was/wasn't taken
- `aggregation_strategy`: How aggregation was resolved
- `excluded_source_ids`: Sources excluded to prevent double-counting
- `formula`: For calculations
- `alternatives_considered`: Audit trail

---

## Key Features

### 1. Many-to-One Support (Aggregation)

**Problem:** Multiple cells map to same concept+period

```
"Total Net Sales" ($100K) → us-gaap_Revenues | 2023
"Product Sales"   ($60K)  → us-gaap_Revenues | 2023
"Service Sales"   ($40K)  → us-gaap_Revenues | 2023
```

**Graph Solution:**
```python
# Create 3 mapping nodes
map1 = MappedNode("us-gaap_Revenues", 100000, "2023")
map2 = MappedNode("us-gaap_Revenues", 60000, "2023")
map3 = MappedNode("us-gaap_Revenues", 40000, "2023")

# Create aggregation edge with 3 sources
agg_edge = FinancialEdge(
    source_node_ids=[map1.id, map2.id, map3.id],
    target_node_id=agg_node.id,
    aggregation_strategy=TOTAL_LINE_USED,
    excluded_source_ids=[map2.id, map3.id],  # Components excluded
    condition="Total detected, preventing double-counting"
)
```

**Query:** "Which sources contributed to this aggregated value?"
```python
incoming_edges = graph.get_incoming_edges(agg_node.id)
source_nodes = [graph.get_node(sid) for sid in incoming_edges[0].source_node_ids]
```

### 2. One-to-Many Support (Calculation)

**Problem:** One value flows into multiple calculations

```
Revenue ($100K) → EBITDA
              → Gross Profit
              → Revenue Growth %
```

**Graph Solution:**
```python
# Create calculation edges
ebitda_edge = FinancialEdge(
    source_node_ids=[revenue_node.id, cogs_node.id, opex_node.id],
    target_node_id=ebitda_node.id,
    formula="Revenue - COGS - OpEx"
)

gross_profit_edge = FinancialEdge(
    source_node_ids=[revenue_node.id, cogs_node.id],
    target_node_id=gross_profit_node.id,
    formula="Revenue - COGS"
)
```

**Query:** "Where does this value flow to?"
```python
descendants = graph.trace_forward(revenue_node.id)
```

### 3. Conditional Edges (Hierarchy-Aware)

**Problem:** Multiple aggregation strategies possible, only one used

```
Strategy 1: Use total line ($100K)        ← ACTIVE
Strategy 2: Sum components ($60K + $40K)  ← INACTIVE (would double-count)
```

**Graph Solution:**
```python
# Edge 1: Active (path taken)
edge1 = FinancialEdge(
    source_node_ids=[total_line.id],
    target_node_id=agg_node.id,
    is_active=True,
    condition="Total line used"
)

# Edge 2: Inactive (path not taken)
edge2 = FinancialEdge(
    source_node_ids=[component1.id, component2.id],
    target_node_id=agg_node.id,
    is_active=False,
    condition="Components excluded to prevent double-counting"
)
```

**Query:** "Show me aggregation conflicts"
```python
conflicts = graph.query_aggregations_with_conflicts()
for node, inactive_edges in conflicts:
    print(f"Concept: {node.concept}")
    print(f"Active path: {graph.get_incoming_edges(node.id, active_only=True)}")
    print(f"Rejected paths: {inactive_edges}")
```

### 4. Analyst Brain Overrides

**Problem:** System mapping wrong, analyst provides correct mapping

**Graph Solution:**
```python
# Original system mapping (now inactive)
old_edge = FinancialEdge(
    source_node_ids=[extracted.id],
    target_node_id=wrong_concept.id,
    method="Keyword Match",
    source=MappingSource.KEYWORD,
    is_active=False,
    condition="Superseded by analyst brain"
)

# Analyst brain mapping (active)
new_edge = FinancialEdge(
    source_node_ids=[extracted.id],
    target_node_id=correct_concept.id,
    method="Analyst Brain Override",
    source=MappingSource.ANALYST_BRAIN,
    confidence=1.0,
    is_active=True
)

# Superseded edge linking them
superseded = FinancialEdge(
    edge_type=EdgeType.SUPERSEDED,
    source_node_ids=[old_edge.id],
    target_node_id=new_edge.id,
    condition="User correction applied"
)
```

**Query:** "Show me all analyst brain overrides"
```python
overrides = graph.query_analyst_brain_overrides()
for node, edge in overrides:
    print(f"{edge.source_node_ids[0]} → {node.concept} (confidence: {edge.confidence})")
```

---

## Storage Formats

### 1. In-Memory (Runtime)

**Python Data Structures:**
```python
class FinancialLineageGraph:
    nodes: Dict[str, FinancialNode]                    # Fast lookup
    edges: Dict[str, FinancialEdge]

    # Adjacency lists for O(1) traversal
    _outgoing: Dict[str, Set[str]]                     # node_id -> edge_ids
    _incoming: Dict[str, Set[str]]                     # node_id -> edge_ids

    # Indexes for fast queries
    _by_type: Dict[NodeType, Set[str]]                 # node_type -> node_ids
    _by_concept: Dict[str, Set[str]]                   # concept -> node_ids
    _by_period: Dict[str, Set[str]]                    # period -> node_ids
    _by_cell: Dict[Tuple[str,int,int], str]           # (sheet,row,col) -> node_id
```

**Complexity:**
- Node lookup: O(1)
- Edge lookup: O(1)
- Find children: O(d) where d = out-degree
- Find parents: O(d) where d = in-degree
- Trace backward/forward: O(V + E) BFS

### 2. JSON Export (Serialization)

**File Structure:**
```json
{
  "metadata": {
    "session_id": "ses_abc123",
    "source_file": "apple_10k.xlsx",
    "created_at": "2026-01-07T12:00:00Z",
    "total_nodes": 1523,
    "total_edges": 2891,
    "active_edges": 2654
  },
  "nodes": {
    "ses_abc123:cell:00000001": {
      "node_id": "ses_abc123:cell:00000001",
      "node_type": "source_cell",
      "label": "Total Net Sales",
      "value": 100000,
      "sheet_name": "Income Statement",
      "cell_ref": "C6",
      "row_index": 5,
      "col_index": 2,
      "is_active": true
    }
  },
  "edges": {
    "ses_abc123:extract:00000001": {
      "edge_id": "ses_abc123:extract:00000001",
      "edge_type": "extraction",
      "source_node_ids": ["ses_abc123:cell:00000001"],
      "target_node_id": "ses_abc123:extracted:00000001",
      "method": "excel_extraction",
      "confidence": 1.0,
      "is_active": true
    }
  }
}
```

**File Size:** ~1-5MB for typical 3-statement company

### 3. Graph Database (Optional, for Scale)

**Neo4j Cypher Mapping:**

```cypher
// Create nodes
CREATE (c:SourceCell {
  node_id: "ses_abc123:cell:00000001",
  label: "Total Net Sales",
  value: 100000,
  cell_ref: "C6"
})

CREATE (e:Extracted {
  node_id: "ses_abc123:extracted:00000001",
  label: "Total Net Sales",
  value: 100000,
  period: "2023"
})

// Create edge
CREATE (c)-[:EXTRACTION {
  edge_id: "ses_abc123:extract:00000001",
  method: "excel_extraction",
  confidence: 1.0
}]->(e)
```

**Cypher Queries:**

```cypher
// Find path from cell to DCF line
MATCH path = (source:SourceCell {cell_ref: "C6"})-[*]->(target:Calculated {label: "Revenue"})
WHERE ALL(r IN relationships(path) WHERE r.is_active = true)
RETURN path

// Find aggregation conflicts
MATCH (n:Aggregated)<-[r:AGGREGATION]-(sources)
WHERE r.is_active = false
RETURN n, collect(r) as conflicts

// Find analyst brain overrides
MATCH (e:Extracted)-[r:MAPPING {source: "analyst_brain"}]->(m:Mapped)
RETURN e.label, m.concept, r.confidence
```

**When to use Neo4j:**
- Dataset > 100K nodes
- Complex graph analytics (centrality, community detection)
- Real-time collaboration (multiple analysts)

---

## Query Patterns

### 1. Provenance Queries

**Q1: Where did this DCF Revenue come from?**
```python
dcf_revenue = graph.query_nodes_by_concept("us-gaap_Revenues", period="2023")[0]
ancestors = graph.trace_backward(dcf_revenue.node_id)

# Walk backward to source cells
source_cells = [n for n in ancestors if n.node_type == NodeType.SOURCE_CELL]
for cell in source_cells:
    print(f"Sheet: {cell.sheet_name}, Cell: {cell.cell_ref}, Value: {cell.value}")
```

**Q2: If I change this Excel cell, what's affected?**
```python
cell = graph.query_node_by_cell("Income Statement", row=5, col=2)
descendants = graph.trace_forward(cell.node_id)

# Group by final destination
dcf_lines = [n for n in descendants if n.node_type == NodeType.CALCULATED]
for line in dcf_lines:
    print(f"Affects DCF line: {line.label}")
```

### 2. Conflict Analysis

**Q3: Show me all hierarchy conflicts**
```python
conflicts = graph.query_aggregations_with_conflicts()

for target_node, inactive_edges in conflicts:
    print(f"\nConcept: {target_node.concept} | Period: {target_node.period}")
    print(f"Final value: {target_node.value}")

    active = graph.get_incoming_edges(target_node.node_id, active_only=True)[0]
    print(f"Strategy used: {active.aggregation_strategy.value}")

    for edge in inactive_edges:
        sources = [graph.get_node(sid) for sid in edge.source_node_ids]
        print(f"Rejected: {[s.label for s in sources]} (reason: {edge.condition})")
```

**Q4: Find low-confidence mappings**
```python
low_conf = graph.query_low_confidence_mappings(threshold=0.7)

for node, edge in low_conf:
    print(f"Label: {node.label} → Concept: {node.concept}")
    print(f"Method: {edge.method} | Confidence: {edge.confidence}")
    print(f"Alternatives: {edge.alternatives_considered}")
```

### 3. Path Finding

**Q5: Find shortest path between two nodes**
```python
source_cell = graph.query_node_by_cell("Income Statement", 5, 2)
dcf_revenue = graph.query_nodes_by_concept("Revenue", period="2023")[0]

path = graph.find_path(source_cell.node_id, dcf_revenue.node_id)

print("Transformation path:")
for node, edge in path:
    print(f"{node.node_type.value} --[{edge.method}]--> ", end="")
print(f"{path[-1][1].target_node_id}")
```

### 4. Audit Queries

**Q6: Generate audit report**
```python
stats = graph.get_statistics()

report = {
    "session": graph.session_id,
    "source_file": graph.source_file,
    "total_transformations": stats["total_edges"],
    "active_paths": stats["active_edges"],
    "rejected_paths": stats["inactive_edges"],
    "mapping_breakdown": stats["mapping_sources"],
    "aggregation_strategies": stats["aggregation_strategies"],
    "avg_confidence": stats["avg_confidence"],
    "analyst_overrides": len(graph.query_analyst_brain_overrides()),
    "conflicts_detected": len(graph.query_aggregations_with_conflicts())
}
```

---

## Integration with Existing Pipeline

### Stage 1: Extraction

```python
# In extractor/extractor.py
from utils.lineage_graph import LineageGraphBuilder

builder = LineageGraphBuilder(session_id, excel_file)

for row_idx, row in enumerate(data_rows):
    for col_idx, cell_value in enumerate(row):
        # Add source cell
        cell_id = builder.add_source_cell(
            sheet=sheet_name,
            row=row_idx,
            col=col_idx,
            cell_ref=f"{chr(65+col_idx)}{row_idx+1}",
            value=cell_value,
            label=label
        )

        # Add extraction
        extracted_id, _ = builder.add_extraction(
            source_cell_id=cell_id,
            extracted_label=label,
            extracted_value=amount,
            period=period
        )
```

### Stage 2: Mapping

```python
# In mapper/mapper.py
def map_input(self, raw_label):
    result = self._resolve_mapping(raw_label)

    # Record in graph
    if self.lineage_builder:
        mapped_id, edge_id = self.lineage_builder.add_mapping(
            extracted_node_id=extracted_id,
            concept=result["element_id"],
            mapping_method=result["method"],
            mapping_source=self._get_mapping_source(result["method"]),
            confidence=result.get("confidence", 1.0),
            alternatives=result.get("alternatives", [])
        )

    return result
```

### Stage 3: Aggregation

```python
# In modeler/engine.py
def _hierarchy_aware_aggregate(self, concept, period, entries):
    # Detect hierarchy
    totals, components = self._detect_hierarchy(entries)

    if totals:
        # Use total line
        final_value = totals[0]["amount"]
        strategy = AggregationStrategy.TOTAL_LINE_USED
        excluded = [c["id"] for c in components]
    else:
        # Sum components
        final_value = sum(c["amount"] for c in components)
        strategy = AggregationStrategy.COMPONENT_SUM
        excluded = []

    # Record in graph
    if self.lineage_builder:
        agg_id, _ = self.lineage_builder.add_aggregation(
            mapped_node_ids=[e["node_id"] for e in entries],
            concept=concept,
            period=period,
            final_value=final_value,
            strategy=strategy,
            excluded_ids=excluded,
            condition=f"Detected {len(totals)} totals, {len(components)} components"
        )

    return final_value
```

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Add node | O(1) | Hash table insert |
| Add edge | O(k) | k = number of source nodes |
| Get node | O(1) | Hash table lookup |
| Get children | O(d) | d = out-degree |
| Get parents | O(d) | d = in-degree |
| Trace backward | O(V + E) | BFS traversal |
| Find path | O(E log V) | Dijkstra's algorithm |
| Query by concept | O(k) | k = nodes with that concept |

### Space Complexity

| Structure | Space | Notes |
|-----------|-------|-------|
| Nodes | O(V) | V = number of nodes |
| Edges | O(E) | E = number of edges |
| Adjacency lists | O(E) | Each edge in 2 lists |
| Indexes | O(V) | Each node indexed by type/concept |
| **Total** | **O(V + E)** | Linear in graph size |

### Typical Sizes

| Company Size | Nodes | Edges | Memory | JSON Size |
|--------------|-------|-------|--------|-----------|
| Small (50 line items) | ~500 | ~1,000 | ~5 MB | ~1 MB |
| Medium (200 line items) | ~2,000 | ~4,000 | ~20 MB | ~3 MB |
| Large (1000 line items) | ~10,000 | ~20,000 | ~100 MB | ~15 MB |

---

## Advantages Over Flat Tables

### 1. Natural Relationships
- **Graph:** `node1 --[edge]--> node2` is first-class
- **Tables:** Requires foreign keys + joins

### 2. Multi-Parent Support
- **Graph:** Edge has `source_node_ids: [id1, id2, id3]`
- **Tables:** Need junction table + complex join

### 3. Conditional Logic
- **Graph:** `edge.is_active = False`, `edge.condition = "why"`
- **Tables:** Separate status table or flag columns

### 4. Path Finding
- **Graph:** Native traversal algorithms (BFS, Dijkstra)
- **Tables:** Recursive CTEs (slow, limited depth)

### 5. Versioning
- **Graph:** Create new edge, mark old as superseded
- **Tables:** Complex temporal tables

### 6. Query Performance
- **Graph:** O(E) traversal
- **Tables:** O(n²) joins for multi-hop queries

---

## Future Enhancements

### 1. Subgraph Extraction
```python
# Extract just the Revenue lineage for export
revenue_subgraph = graph.extract_subgraph(
    concept="us-gaap_Revenues",
    include_ancestors=True,
    include_descendants=False
)
```

### 2. Graph Diff
```python
# Compare two sessions
diff = graph1.diff(graph2)
print(f"Added nodes: {diff.added_nodes}")
print(f"Removed nodes: {diff.removed_nodes}")
print(f"Changed edges: {diff.changed_edges}")
```

### 3. Temporal Graphs
```python
# Track how lineage changes over time
graph.add_edge_version(edge_id, version=2, timestamp=now())
historical_path = graph.find_path(source, target, as_of=yesterday)
```

### 4. Graph Analytics
```python
# Find most influential nodes (PageRank)
influence_scores = graph.compute_pagerank()

# Find communities (concepts that cluster together)
communities = graph.detect_communities()

# Find bottlenecks (nodes with high betweenness)
bottlenecks = graph.find_bottlenecks()
```

---

## Testing

### Unit Tests
```python
def test_many_to_one_aggregation():
    builder = LineageGraphBuilder("test", "test.xlsx")

    # Create 3 mapped nodes
    map1 = builder.add_mapping(..., concept="us-gaap_Revenues", ...)
    map2 = builder.add_mapping(..., concept="us-gaap_Revenues", ...)
    map3 = builder.add_mapping(..., concept="us-gaap_Revenues", ...)

    # Aggregate
    agg_id, _ = builder.add_aggregation(
        [map1, map2, map3],
        "us-gaap_Revenues",
        "2023",
        100000,
        AggregationStrategy.TOTAL_LINE_USED
    )

    # Assert
    graph = builder.graph
    incoming = graph.get_incoming_edges(agg_id)
    assert len(incoming) == 1
    assert len(incoming[0].source_node_ids) == 3

def test_conditional_edges():
    # Test that inactive edges are not traversed
    graph = create_test_graph_with_conflicts()

    active_path = graph.trace_forward(source_id, active_only=True)
    all_paths = graph.trace_forward(source_id, active_only=False)

    assert len(active_path) < len(all_paths)

def test_analyst_brain_override():
    builder = LineageGraphBuilder("test", "test.xlsx")

    # System mapping
    extracted_id = ...
    map1_id, edge1_id = builder.add_mapping(
        extracted_id, "us-gaap_WrongConcept", "Keyword",
        MappingSource.KEYWORD, 0.6
    )

    # Analyst override
    map2_id, edge2_id = builder.add_mapping(
        extracted_id, "us-gaap_CorrectConcept", "Analyst Brain",
        MappingSource.ANALYST_BRAIN, 1.0
    )

    # Supersede
    builder.graph.supersede_edge(edge1_id, edge2_id)

    # Assert
    edge1 = builder.graph.get_edge(edge1_id)
    assert edge1.is_active == False

    overrides = builder.graph.query_analyst_brain_overrides()
    assert len(overrides) == 1
```

---

## Conclusion

The graph-based lineage model provides:

✅ **Natural representation** of financial transformations
✅ **Efficient queries** for provenance and impact analysis
✅ **Full audit trail** with conditional logic
✅ **Scalable storage** (in-memory, JSON, or graph DB)
✅ **Powerful analytics** (path finding, conflict detection)

This architecture supports all FinanceX requirements:
- Many-to-one aggregation
- Hierarchy-aware resolution
- Analyst brain overrides
- Programmatic queries
- Regulatory compliance

---

**Next Steps:**
1. Integrate `LineageGraphBuilder` into existing pipeline
2. Add graph export to `run_pipeline.py`
3. Create UI for graph visualization
4. Benchmark performance with real-world data
5. Consider Neo4j for datasets > 100K nodes
