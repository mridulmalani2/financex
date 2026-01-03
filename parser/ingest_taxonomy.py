#!/usr/bin/env python3
"""
XBRL Taxonomy Ingestion Script - 2025 US GAAP & IFRS (ID-Based Resolution)
==========================================================================
This script builds a structured SQLite database containing all officially defined
financial statement concepts from the 2025 US GAAP and IFRS XBRL taxonomies.

It relies on STRICT ID-based resolution as mandated by the XBRL 2.1 Specification:
1. Concepts are identified by their unique XSD 'id' attribute (e.g., 'us-gaap_Assets').
2. Linkbases reference these concepts via 'href' anchors (e.g., '#us-gaap_Assets').
3. This script builds a global map of {xsd_id -> concept_id} to ensure 100% 
   deterministic linking without file-path guessing or fuzzy matching.

Output:
  taxonomy_2025.db : A fully relational, traceable financial compiler database.
"""
import os
import re
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from lxml import etree
from tqdm import tqdm


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
OUTPUT_DB = os.path.join(OUTPUT_DIR, "taxonomy_2025.db")

US_GAAP_DIR = os.path.join(ROOT_DIR, "us-gaap-2025")
IFRS_DIR = os.path.join(ROOT_DIR, "ifrs-2025")

NS = {
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "xbrli": "http://www.xbrl.org/2003/instance",
    "xbrldt": "http://xbrl.org/2005/xbrldt",
}

LABEL_ROLES = {
    "http://www.xbrl.org/2003/role/label": "standard",
    "http://www.xbrl.org/2003/role/terseLabel": "terse",
    "http://www.xbrl.org/2003/role/verboseLabel": "verbose",
    "http://www.xbrl.org/2003/role/documentation": "documentation",
    "http://www.xbrl.org/2003/role/definitionGuidance": "definitionGuidance",
    "http://www.xbrl.org/2003/role/disclosureGuidance": "disclosureGuidance",
    "http://www.xbrl.org/2003/role/presentationGuidance": "presentationGuidance",
    "http://www.xbrl.org/2003/role/measurementGuidance": "measurementGuidance",
    "http://www.xbrl.org/2003/role/commentaryGuidance": "commentaryGuidance",
    "http://www.xbrl.org/2003/role/exampleGuidance": "exampleGuidance",
    "http://www.xbrl.org/2003/role/totalLabel": "total",
    "http://www.xbrl.org/2003/role/periodStartLabel": "periodStart",
    "http://www.xbrl.org/2003/role/periodEndLabel": "periodEnd",
    "http://www.xbrl.org/2003/role/negatedLabel": "negated",
    "http://www.xbrl.org/2003/role/negatedTerseLabel": "negatedTerse",
    "http://www.xbrl.org/2003/role/negatedTotalLabel": "negatedTotal",
    "http://www.xbrl.org/2003/role/positiveLabel": "positive",
    "http://www.xbrl.org/2003/role/positiveTerseLabel": "positiveTerse",
    "http://www.xbrl.org/2003/role/positiveTotalLabel": "positiveTotal",
    "http://www.xbrl.org/2003/role/negativeLabel": "negative",
    "http://www.xbrl.org/2003/role/negativeTerseLabel": "negativeTerse",
    "http://www.xbrl.org/2003/role/negativeTotalLabel": "negativeTotal",
    "http://www.xbrl.org/2003/role/zeroLabel": "zero",
    "http://www.xbrl.org/2003/role/zeroTerseLabel": "zeroTerse",
    "http://www.xbrl.org/2003/role/zeroTotalLabel": "zeroTotal",
    "http://www.xbrl.org/2009/role/netLabel": "net",
    "http://www.xbrl.org/2009/role/negatedNetLabel": "negatedNet",
}

DIM_ARCROLES = {
    "http://xbrl.org/int/dim/arcrole/all": "all",
    "http://xbrl.org/int/dim/arcrole/notAll": "notAll",
    "http://xbrl.org/int/dim/arcrole/hypercube-dimension": "hypercube-dimension",
    "http://xbrl.org/int/dim/arcrole/dimension-domain": "dimension-domain",
    "http://xbrl.org/int/dim/arcrole/domain-member": "domain-member",
    "http://xbrl.org/int/dim/arcrole/dimension-default": "dimension-default",
}


# -------------------------------------------------
# DATABASE SETUP
# -------------------------------------------------
def create_db() -> sqlite3.Connection:
    """Create SQLite database with comprehensive schema for XBRL taxonomy data."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    conn = sqlite3.connect(OUTPUT_DB)
    cur = conn.cursor()
    
    # Enable Write-Ahead Logging for performance
    cur.execute("PRAGMA journal_mode=WAL;")
    
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS concepts (
        concept_id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        taxonomy_year INTEGER NOT NULL,
        namespace TEXT,
        concept_name TEXT NOT NULL,
        element_id TEXT,
        data_type TEXT,
        period_type TEXT,
        balance TEXT,
        abstract INTEGER DEFAULT 0,
        substitution_group TEXT,
        is_dimensional INTEGER DEFAULT 0,
        nillable INTEGER DEFAULT 1,
        xsd_file TEXT
    );

    CREATE TABLE IF NOT EXISTS labels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_id TEXT NOT NULL,
        label_role TEXT,
        label_language TEXT DEFAULT 'en',
        label_text TEXT,
        source_file TEXT,
        FOREIGN KEY (concept_id) REFERENCES concepts(concept_id)
    );

    CREATE TABLE IF NOT EXISTS documentation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_id TEXT NOT NULL,
        documentation_text TEXT,
        source_file TEXT,
        FOREIGN KEY (concept_id) REFERENCES concepts(concept_id)
    );

    CREATE TABLE IF NOT EXISTS xbrl_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_id TEXT NOT NULL,
        reference_role TEXT,
        publisher TEXT,
        name TEXT,
        number TEXT,
        paragraph TEXT,
        subparagraph TEXT,
        section TEXT,
        subsection TEXT,
        uri TEXT,
        source_file TEXT,
        FOREIGN KEY (concept_id) REFERENCES concepts(concept_id)
    );

    CREATE TABLE IF NOT EXISTS presentation_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_id TEXT NOT NULL,
        role_uri TEXT,
        role_definition TEXT,
        parent_concept_id TEXT,
        order_index REAL,
        depth INTEGER DEFAULT 0,
        preferred_label TEXT,
        source_file TEXT,
        FOREIGN KEY (concept_id) REFERENCES concepts(concept_id),
        FOREIGN KEY (parent_concept_id) REFERENCES concepts(concept_id)
    );

    CREATE TABLE IF NOT EXISTS calculations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_concept_id TEXT NOT NULL,
        child_concept_id TEXT NOT NULL,
        weight REAL NOT NULL,
        order_index REAL,
        role_uri TEXT,
        role_definition TEXT,
        source_file TEXT,
        FOREIGN KEY (parent_concept_id) REFERENCES concepts(concept_id),
        FOREIGN KEY (child_concept_id) REFERENCES concepts(concept_id)
    );

    CREATE TABLE IF NOT EXISTS dimensions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_id TEXT NOT NULL,
        hypercube_id TEXT,
        axis_id TEXT,
        member_id TEXT,
        is_default INTEGER DEFAULT 0,
        is_typed INTEGER DEFAULT 0,
        relationship_type TEXT,
        role_uri TEXT,
        source_file TEXT,
        FOREIGN KEY (concept_id) REFERENCES concepts(concept_id)
    );

    CREATE TABLE IF NOT EXISTS link_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        role_uri TEXT UNIQUE,
        role_definition TEXT,
        used_on TEXT,
        source_file TEXT
    );

    CREATE TABLE IF NOT EXISTS unresolved_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        namespace TEXT,
        concept_name TEXT,
        context TEXT,
        source_file TEXT
    );

    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(concept_name);
    CREATE INDEX IF NOT EXISTS idx_concepts_source ON concepts(source);
    CREATE INDEX IF NOT EXISTS idx_concepts_namespace ON concepts(namespace);
    CREATE INDEX IF NOT EXISTS idx_labels_concept ON labels(concept_id);
    CREATE INDEX IF NOT EXISTS idx_labels_role ON labels(label_role);
    CREATE INDEX IF NOT EXISTS idx_documentation_concept ON documentation(concept_id);
    CREATE INDEX IF NOT EXISTS idx_xbrl_references_concept ON xbrl_references(concept_id);
    CREATE INDEX IF NOT EXISTS idx_presentation_concept ON presentation_roles(concept_id);
    CREATE INDEX IF NOT EXISTS idx_presentation_parent ON presentation_roles(parent_concept_id);
    CREATE INDEX IF NOT EXISTS idx_presentation_role ON presentation_roles(role_uri);
    CREATE INDEX IF NOT EXISTS idx_calculations_parent ON calculations(parent_concept_id);
    CREATE INDEX IF NOT EXISTS idx_calculations_child ON calculations(child_concept_id);
    CREATE INDEX IF NOT EXISTS idx_calculations_role ON calculations(role_uri);
    CREATE INDEX IF NOT EXISTS idx_dimensions_concept ON dimensions(concept_id);
    CREATE INDEX IF NOT EXISTS idx_dimensions_axis ON dimensions(axis_id);
    CREATE INDEX IF NOT EXISTS idx_dimensions_hypercube ON dimensions(hypercube_id);
    """)
    conn.commit()
    return conn


# -------------------------------------------------
# GLOBAL UTILS & REGISTRIES
# -------------------------------------------------
def gen_id(namespace: str, concept: str) -> str:
    """Generate deterministic UUID for concept identification based on (namespace, name)."""
    namespace = namespace or ""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{namespace}:{concept}"))

def determine_source(path: str) -> str:
    """Determine source (US_GAAP or IFRS) based on file path."""
    if "us-gaap" in path.lower() or "fasb" in path.lower(): return "US_GAAP"
    if "ifrs" in path.lower(): return "IFRS"
    return "US_GAAP"

def find_files(base_dir: str, pattern: str) -> List[str]:
    """Recursively find files matching pattern."""
    files = []
    if not os.path.exists(base_dir): return files
    for root, _, filenames in os.walk(base_dir):
        for f in filenames:
            if re.search(pattern, f, re.IGNORECASE):
                files.append(os.path.join(root, f))
    return files

def normalize_role(role_uri: str) -> str:
    return LABEL_ROLES.get(role_uri, role_uri.split("/")[-1] if role_uri else "unknown")

# -------------------------------------------------
# STEP 1: CONCEPTS & GLOBAL ID MAPPING
# -------------------------------------------------
def build_global_concept_registry(conn: sqlite3.Connection, base_dirs: List[str]) -> Dict[str, str]:
    """
    Parses ALL XSD files to build:
    1. The 'concepts' table (persisted ground truth).
    2. A 'GLOBAL_ID_MAP' (in-memory) mapping XSD 'id' -> 'concept_id'.
    
    This ID map is the KEY to deterministic linking.
    """
    cur = conn.cursor()
    global_id_map = {} # Maps element_id (e.g. 'us-gaap_Assets') -> concept_id (UUID)
    
    xsd_files = []
    for base_dir in base_dirs:
        xsd_files.extend(find_files(base_dir, r"\.xsd$"))
        
    print(f"  Scanning {len(xsd_files)} XSD files...")
    
    batch_data = []
    
    for xsd_path in tqdm(xsd_files, desc="Step 1: Global concepts"):
        try:
            tree = etree.parse(xsd_path)
            root = tree.getroot()
            target_ns = root.get("targetNamespace")
            source = determine_source(xsd_path)
            
            for el in root.findall(".//xsd:element", NS):
                name = el.get("name")
                element_id = el.get("id") # STRICT ID KEY
                
                if not name or not target_ns: continue
                
                # Deterministic Concept ID
                concept_id = gen_id(target_ns, name)
                
                # Populate Global ID Map for Linking
                if element_id:
                    global_id_map[element_id] = concept_id
                    
                # Prepare DB Record
                subst_group = el.get("substitutionGroup", "")
                is_dim = 1 if any(x in subst_group.lower() for x in ["dimension", "hypercube", "domain"]) else 0
                
                batch_data.append((
                    concept_id, 
                    source, 
                    2025, 
                    target_ns, 
                    name,
                    element_id, # ADDED: Ensure this is included!
                    el.get("type"),
                    el.get("{http://www.xbrl.org/2003/instance}periodType"),
                    el.get("{http://www.xbrl.org/2003/instance}balance"),
                    1 if el.get("abstract") == "true" else 0,
                    subst_group,
                    is_dim,
                    1 if el.get("nillable", "true") == "true" else 0,
                    os.path.basename(xsd_path)
                ))
        except Exception:
            continue
            
    # Bulk insert (Ensure 14 placeholders for 14 columns)
    cur.executemany("""
        INSERT OR IGNORE INTO concepts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, batch_data)
    
    conn.commit()
    print(f"  Registered {len(global_id_map)} linkable element IDs.")
    return global_id_map


def resolve_by_id(href: str, global_id_map: Dict[str, str], cur: sqlite3.Cursor, source: str, context: str, file: str) -> Optional[str]:
    """
    Resolves a linkbase href to a concept_id using the GLOBAL_ID_MAP.
    Strictly follows XBRL 2.1: href="..."#element_id
    """
    if not href or "#" not in href:
        return None
    
    element_id = href.split("#")[-1]
    
    if element_id in global_id_map:
        return global_id_map[element_id]
        
    # Log failure
    cur.execute("""
        INSERT INTO unresolved_references (source, namespace, concept_name, context, source_file)
        VALUES (?, 'UNRESOLVED_ID', ?, ?, ?)
    """, (source, element_id, context, os.path.basename(file)))
    return None


# -------------------------------------------------
# STEP 2: LABELS
# -------------------------------------------------
def ingest_labels(conn: sqlite3.Connection, base_dir: str, source: str, global_id_map: Dict[str, str]):
    cur = conn.cursor()
    files = find_files(base_dir, r"lab.*\.xml$|_lab.*\.xml$|-lab.*\.xml$")
                
    for fpath in tqdm(files, desc=f"Step 2: {source} labels"):
        try:
            tree = etree.parse(fpath)
            root = tree.getroot()
            
            # Map locators to Concept IDs
            loc_map = {} 
            for loc in root.findall(".//link:loc", NS):
                label = loc.get("{http://www.w3.org/1999/xlink}label")
                href = loc.get("{http://www.w3.org/1999/xlink}href")
                cid = resolve_by_id(href, global_id_map, cur, source, "label", fpath)
                if label and cid:
                    loc_map[label] = cid
            
            # Map resources
            res_map = {}
            for res in root.findall(".//link:label", NS):
                label = res.get("{http://www.w3.org/1999/xlink}label")
                text = res.text
                if label and text:
                    res_map[label] = (
                        text.strip(),
                        res.get("{http://www.w3.org/1999/xlink}role"),
                        res.get("{http://www.w3.org/XML/1998/namespace}lang", "en")
                    )
            
            # Link Arcs
            for arc in root.findall(".//link:labelArc", NS):
                from_lbl = arc.get("{http://www.w3.org/1999/xlink}from")
                to_lbl = arc.get("{http://www.w3.org/1999/xlink}to")
                
                if from_lbl in loc_map and to_lbl in res_map:
                    cid = loc_map[from_lbl]
                    text, role, lang = res_map[to_lbl]
                    short_role = normalize_role(role)
                    
                    if short_role == "documentation":
                        cur.execute("INSERT INTO documentation (concept_id, documentation_text, source_file) VALUES (?,?,?)",
                                    (cid, text, os.path.basename(fpath)))
                    else:
                        cur.execute("INSERT INTO labels (concept_id, label_role, label_language, label_text, source_file) VALUES (?,?,?,?,?)",
                                    (cid, short_role, lang, text, os.path.basename(fpath)))
        except Exception:
            continue
    conn.commit()


# -------------------------------------------------
# STEP 3: REFERENCES
# -------------------------------------------------
def ingest_references(conn: sqlite3.Connection, base_dir: str, source: str, global_id_map: Dict[str, str]):
    cur = conn.cursor()
    files = find_files(base_dir, r"ref.*\.xml$|_ref.*\.xml$|-ref.*\.xml$")
                
    for fpath in tqdm(files, desc=f"Step 3: {source} references"):
        try:
            tree = etree.parse(fpath)
            root = tree.getroot()
            
            loc_map = {}
            for loc in root.findall(".//link:loc", NS):
                label = loc.get("{http://www.w3.org/1999/xlink}label")
                href = loc.get("{http://www.w3.org/1999/xlink}href")
                cid = resolve_by_id(href, global_id_map, cur, source, "reference", fpath)
                if label and cid:
                    loc_map[label] = cid
            
            res_map = {}
            for res in root.findall(".//link:reference", NS):
                label = res.get("{http://www.w3.org/1999/xlink}label")
                if label:
                    parts = {"role": res.get("{http://www.w3.org/1999/xlink}role")}
                    for child in res:
                        parts[etree.QName(child).localname.lower()] = child.text
                    res_map[label] = parts
            
            for arc in root.findall(".//link:referenceArc", NS):
                from_lbl = arc.get("{http://www.w3.org/1999/xlink}from")
                to_lbl = arc.get("{http://www.w3.org/1999/xlink}to")
                
                if from_lbl in loc_map and to_lbl in res_map:
                    cid = loc_map[from_lbl]
                    p = res_map[to_lbl]
                    cur.execute("""
                        INSERT INTO xbrl_references (concept_id, reference_role, publisher, name, number, paragraph, subparagraph, section, subsection, uri, source_file)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cid, p.get("role"), p.get("publisher"), p.get("name"), p.get("number"), p.get("paragraph"), 
                          p.get("subparagraph"), p.get("section"), p.get("subsection"), p.get("uri"), os.path.basename(fpath)))
        except Exception:
            continue
    conn.commit()


# -------------------------------------------------
# STEP 4: PRESENTATIONS
# -------------------------------------------------
def ingest_presentations(conn: sqlite3.Connection, base_dir: str, source: str, global_id_map: Dict[str, str]):
    cur = conn.cursor()
    files = find_files(base_dir, r"pre.*\.xml$|_pre.*\.xml$|-pre.*\.xml$")
                
    for fpath in tqdm(files, desc=f"Step 4: {source} presentations"):
        try:
            tree = etree.parse(fpath)
            root = tree.getroot()
            
            for plink in root.findall(".//link:presentationLink", NS):
                role_uri = plink.get("{http://www.w3.org/1999/xlink}role")
                role_def = role_uri.split("/")[-1] if role_uri else ""
                
                cur.execute("INSERT OR IGNORE INTO link_roles (source, role_uri, role_definition, used_on, source_file) VALUES (?,?,?,?,?)",
                           (source, role_uri, role_def, "presentationLink", os.path.basename(fpath)))
                
                loc_map = {}
                for loc in plink.findall("link:loc", NS):
                    label = loc.get("{http://www.w3.org/1999/xlink}label")
                    href = loc.get("{http://www.w3.org/1999/xlink}href")
                    cid = resolve_by_id(href, global_id_map, cur, source, "presentation", fpath)
                    if label and cid:
                        loc_map[label] = cid
                
                for arc in plink.findall("link:presentationArc", NS):
                    from_lbl = arc.get("{http://www.w3.org/1999/xlink}from")
                    to_lbl = arc.get("{http://www.w3.org/1999/xlink}to")
                    
                    if from_lbl in loc_map and to_lbl in loc_map:
                        cur.execute("""
                            INSERT INTO presentation_roles (concept_id, role_uri, role_definition, parent_concept_id, order_index, preferred_label, source_file)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            loc_map[to_lbl], # Child
                            role_uri,
                            role_def,
                            loc_map[from_lbl], # Parent
                            arc.get("order", "0"),
                            normalize_role(arc.get("preferredLabel")),
                            os.path.basename(fpath)
                        ))
        except Exception:
            continue
    conn.commit()


# -------------------------------------------------
# STEP 5: CALCULATIONS
# -------------------------------------------------
def ingest_calculations(conn: sqlite3.Connection, base_dir: str, source: str, global_id_map: Dict[str, str]):
    cur = conn.cursor()
    files = find_files(base_dir, r"cal.*\.xml$|_cal.*\.xml$|-cal.*\.xml$")
                
    for fpath in tqdm(files, desc=f"Step 5: {source} calculations"):
        try:
            tree = etree.parse(fpath)
            root = tree.getroot()
            
            for clink in root.findall(".//link:calculationLink", NS):
                role_uri = clink.get("{http://www.w3.org/1999/xlink}role")
                role_def = role_uri.split("/")[-1] if role_uri else ""
                
                cur.execute("INSERT OR IGNORE INTO link_roles (source, role_uri, role_definition, used_on, source_file) VALUES (?,?,?,?,?)",
                           (source, role_uri, role_def, "calculationLink", os.path.basename(fpath)))
                
                loc_map = {}
                for loc in clink.findall("link:loc", NS):
                    label = loc.get("{http://www.w3.org/1999/xlink}label")
                    href = loc.get("{http://www.w3.org/1999/xlink}href")
                    cid = resolve_by_id(href, global_id_map, cur, source, "calculation", fpath)
                    if label and cid:
                        loc_map[label] = cid
                        
                for arc in clink.findall("link:calculationArc", NS):
                    from_lbl = arc.get("{http://www.w3.org/1999/xlink}from")
                    to_lbl = arc.get("{http://www.w3.org/1999/xlink}to")
                    
                    if from_lbl in loc_map and to_lbl in loc_map:
                        cur.execute("""
                            INSERT INTO calculations (parent_concept_id, child_concept_id, weight, order_index, role_uri, role_definition, source_file)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            loc_map[from_lbl], # Parent (Total)
                            loc_map[to_lbl],   # Child (Item)
                            arc.get("weight", "1"),
                            arc.get("order", "0"),
                            role_uri,
                            role_def,
                            os.path.basename(fpath)
                        ))
        except Exception:
            continue
    conn.commit()


# -------------------------------------------------
# STEP 6: DIMENSIONS
# -------------------------------------------------
def ingest_dimensions(conn: sqlite3.Connection, base_dir: str, source: str, global_id_map: Dict[str, str]):
    cur = conn.cursor()
    files = find_files(base_dir, r"def.*\.xml$|_def.*\.xml$|-def.*\.xml$")
                
    for fpath in tqdm(files, desc=f"Step 6: {source} dimensions"):
        try:
            tree = etree.parse(fpath)
            root = tree.getroot()
            
            for dlink in root.findall(".//link:definitionLink", NS):
                role_uri = dlink.get("{http://www.w3.org/1999/xlink}role")
                role_def = role_uri.split("/")[-1] if role_uri else ""
                
                cur.execute("INSERT OR IGNORE INTO link_roles (source, role_uri, role_definition, used_on, source_file) VALUES (?,?,?,?,?)",
                           (source, role_uri, role_def, "definitionLink", os.path.basename(fpath)))
                
                loc_map = {}
                for loc in dlink.findall("link:loc", NS):
                    label = loc.get("{http://www.w3.org/1999/xlink}label")
                    href = loc.get("{http://www.w3.org/1999/xlink}href")
                    cid = resolve_by_id(href, global_id_map, cur, source, "dimension", fpath)
                    if label and cid:
                        loc_map[label] = cid
                
                for arc in dlink.findall("link:definitionArc", NS):
                    from_lbl = arc.get("{http://www.w3.org/1999/xlink}from")
                    to_lbl = arc.get("{http://www.w3.org/1999/xlink}to")
                    arcrole = arc.get("{http://www.w3.org/1999/xlink}arcrole")
                    
                    if from_lbl in loc_map and to_lbl in loc_map:
                        from_id = loc_map[from_lbl]
                        to_id = loc_map[to_lbl]
                        rtype = DIM_ARCROLES.get(arcrole, arcrole.split("/")[-1])
                        
                        dim = {
                            "concept_id": to_id, "hypercube_id": None, "axis_id": None, 
                            "member_id": None, "is_default": 0
                        }
                        
                        if rtype in ["all", "notAll"]:
                            dim["concept_id"] = from_id # Primary Item
                            dim["hypercube_id"] = to_id # Table
                        elif rtype == "hypercube-dimension":
                            dim["hypercube_id"] = from_id
                            dim["axis_id"] = to_id
                        elif rtype == "dimension-domain":
                            dim["axis_id"] = from_id
                            dim["member_id"] = to_id # Domain root
                        elif rtype == "domain-member":
                            dim["concept_id"] = from_id # Parent Member
                            dim["member_id"] = to_id   # Child Member
                        elif rtype == "dimension-default":
                            dim["axis_id"] = from_id
                            dim["member_id"] = to_id
                            dim["is_default"] = 1
                            
                        cur.execute("""
                            INSERT INTO dimensions (concept_id, hypercube_id, axis_id, member_id, is_default, is_typed, relationship_type, role_uri, source_file)
                            VALUES (:concept_id, :hypercube_id, :axis_id, :member_id, :is_default, 0, :relationship_type, :role_uri, :source_file)
                        """, {**dim, "relationship_type": rtype, "role_uri": role_uri, "source_file": os.path.basename(fpath)})
        except Exception:
            continue
    conn.commit()


# -------------------------------------------------
# STATISTICS
# -------------------------------------------------
def save_metadata(conn: sqlite3.Connection, us_gaap_dir: str, ifrs_dir: str):
    """Save ingestion metadata."""
    cur = conn.cursor()
    metadata = {
        "created_at": datetime.now().isoformat(),
        "taxonomy_year": "2025",
        "us_gaap_source": us_gaap_dir,
        "ifrs_source": ifrs_dir,
        "script_version": "3.1.0_ID_RESOLVED"
    }
    for key, value in metadata.items():
        cur.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", (key, value))
    conn.commit()

def print_statistics(conn: sqlite3.Connection):
    cur = conn.cursor()
    print("\n" + "="*60)
    print("INGESTION COMPLETE - SUMMARY STATISTICS")
    print("="*60)
    
    tables = [
        ("concepts", "Concepts"),
        ("labels", "Labels"),
        ("documentation", "Documentation entries"),
        ("xbrl_references", "Authoritative references"),
        ("presentation_roles", "Presentation relationships"),
        ("calculations", "Calculation relationships"),
        ("dimensions", "Dimensional relationships"),
        ("link_roles", "Extended link roles"),
        ("unresolved_references", "Unresolved references")
    ]
    
    for table, desc in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {desc}: {count:,}")
    
    print("\n  By Source:")
    cur.execute("SELECT source, COUNT(*) FROM concepts GROUP BY source")
    for source, count in cur.fetchall():
        print(f"    {source}: {count:,} concepts")
    print("="*60)


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    print("="*60)
    print("XBRL TAXONOMY INGESTION - ID-BASED RESOLUTION")
    print("="*60)
    print(f"Output database: {OUTPUT_DB}")
    
    base_dirs = []
    if os.path.exists(US_GAAP_DIR): base_dirs.append(US_GAAP_DIR)
    if os.path.exists(IFRS_DIR): base_dirs.append(IFRS_DIR)
    
    if not base_dirs:
        print("ERROR: No taxonomy directories found. Exiting.")
        return
    
    conn = create_db()
    
    print("\nStep 1: Building global concept registry (XSD ID Map)...")
    global_id_map = build_global_concept_registry(conn, base_dirs)
    
    if not global_id_map:
        print("CRITICAL ERROR: No concepts found. Check XSD paths.")
        return

    print("\nIngesting linkbases with strict ID resolution...")
    
    for d in base_dirs:
        src = determine_source(d)
        print(f"\n--- {src} Linkbases from {d} ---")
        ingest_labels(conn, d, src, global_id_map)
        ingest_references(conn, d, src, global_id_map)
        ingest_presentations(conn, d, src, global_id_map)
        ingest_calculations(conn, d, src, global_id_map)
        ingest_dimensions(conn, d, src, global_id_map)
    
    save_metadata(conn, US_GAAP_DIR, IFRS_DIR)
    print_statistics(conn)
    conn.close()
    print(f"\nDatabase saved to: {OUTPUT_DB}")

if __name__ == "__main__":
    main()