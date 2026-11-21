"""
Mandate Radar Neo4j Knowledge Graph Service
Handles live Neo4j Aura connection, graph synchronization, Cypher queries,
and includes an embedded graph engine so the entire system works instantly.
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import neo4j
from reference_data import REFERENCE_MERCHANTS, PARENT_COMPANIES, PAYMENT_MECHANISMS, ESCALATION_CHAIN
from bundle_reference import CURATED_BUNDLES

class Neo4jKnowledgeGraph:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        self.driver: Optional[neo4j.Driver] = None
        self.is_connected = False
        self.connection_error = None

        # Embedded in-memory graph fallback
        self.nodes = []
        self.edges = []
        self._build_embedded_reference_graph()

        # Try connecting if uri is supplied
        if self.uri and self.password:
            self.connect()

    def connect(self, uri: str = None, user: str = None, password: str = None):
        if uri: self.uri = uri
        if user: self.user = user
        if password: self.password = password

        if not self.uri or not self.password:
            self.is_connected = False
            self.connection_error = "Neo4j URI or Password not provided. Operating in Embedded Graph Mode."
            return False, self.connection_error

        try:
            self.driver = neo4j.GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=300
            )
            self.driver.verify_connectivity()
            self.is_connected = True
            self.connection_error = None
            return True, "Successfully connected to Neo4j instance!"
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)
            return False, f"Neo4j Connection Failed: {str(e)}"

    def close(self):
        if self.driver:
            self.driver.close()

    def _build_embedded_reference_graph(self):
        """Constructs the base in-memory graph of reference nodes and relationships."""
        self.nodes = []
        self.edges = []
        edge_id = 1

        # 1. Parents
        for pid, pdata in PARENT_COMPANIES.items():
            self.nodes.append({
                "id": f"parent_{pid}",
                "label": "Parent",
                "name": pdata["name"],
                "group": "parent",
                "color": "#6366F1", # Indigo
                "val": 28,
                "properties": pdata
            })

        # 2. Mechanisms
        for mcode, mdata in PAYMENT_MECHANISMS.items():
            self.nodes.append({
                "id": f"mech_{mcode}",
                "label": "Mechanism",
                "name": mdata["name"],
                "group": "mechanism",
                "color": "#EC4899", # Pink
                "val": 22,
                "properties": mdata
            })

        # 3. Escalation Steps
        for esc in ESCALATION_CHAIN:
            self.nodes.append({
                "id": f"esc_tier_{esc['tier']}",
                "label": "EscalationStep",
                "name": f"Tier {esc['tier']}: {esc['name']}",
                "group": "escalation",
                "color": "#EF4444", # Red
                "val": 18,
                "properties": esc
            })

        # 4. Merchants & Edges
        for m in REFERENCE_MERCHANTS:
            m_node_id = f"merch_{m['id']}"
            self.nodes.append({
                "id": m_node_id,
                "label": "Merchant",
                "name": m["name"],
                "group": "merchant",
                "color": "#10B981", # Emerald
                "val": 20,
                "properties": {
                    "id": m["id"],
                    "name": m["name"],
                    "category": m["category"],
                    "website": m.get("official_website", ""),
                    "default_amount": m.get("default_amount", 0.0),
                    "pitfall": m.get("cancellation_pitfall", "")
                }
            })

            # Edge to Parent: (Merchant)-[:OWNED_BY]->(Parent)
            if m.get("parent_id") and f"parent_{m['parent_id']}" in [n["id"] for n in self.nodes]:
                self.edges.append({
                    "id": f"e_{edge_id}",
                    "source": m_node_id,
                    "target": f"parent_{m['parent_id']}",
                    "type": "OWNED_BY",
                    "label": "OWNED_BY",
                    "color": "#6366F1"
                })
                edge_id += 1

            # Edge to Default Mechanism: (Merchant)-[:BILLED_VIA]->(Mechanism)
            mech = m.get("default_mechanism", "CARD_SI")
            if f"mech_{mech}" in [n["id"] for n in self.nodes]:
                self.edges.append({
                    "id": f"e_{edge_id}",
                    "source": m_node_id,
                    "target": f"mech_{mech}",
                    "type": "BILLED_VIA",
                    "label": "BILLED_VIA",
                    "color": "#EC4899"
                })
                edge_id += 1

            # Descriptors: (Descriptor)-[:RESOLVES_TO]->(Merchant)
            for pat in m.get("descriptors", [])[:2]: # include top 2 representative patterns
                d_id = f"desc_{hash(pat) % 10000000}"
                self.nodes.append({
                    "id": d_id,
                    "label": "Descriptor",
                    "name": pat.replace(r"\s+", " ").replace(r"\d+", "###"),
                    "group": "descriptor",
                    "color": "#8B5CF6", # Purple
                    "val": 12,
                    "properties": {"pattern": pat}
                })
                self.edges.append({
                    "id": f"e_{edge_id}",
                    "source": d_id,
                    "target": m_node_id,
                    "type": "RESOLVES_TO",
                    "label": "RESOLVES_TO",
                    "color": "#8B5CF6"
                })
                edge_id += 1

        # 5. Seed Curated Bundle Inclusions: (:Merchant)-[:INCLUDES]->(:Merchant)
        for b in CURATED_BUNDLES:
            p_mid = f"merch_{b['parent_id']}"
            c_mid = f"merch_{b['child_id']}"
            # Ensure merchant nodes exist
            existing_ids = {n["id"] for n in self.nodes}
            if p_mid not in existing_ids:
                self.nodes.append({
                    "id": p_mid,
                    "label": "Merchant",
                    "name": b["parent_name"],
                    "group": "merchant",
                    "color": "#10B981",
                    "val": 20,
                    "properties": {"id": b["parent_id"], "name": b["parent_name"], "category": "Bundle Subscription"}
                })
            if c_mid not in existing_ids:
                self.nodes.append({
                    "id": c_mid,
                    "label": "Merchant",
                    "name": b["child_name"],
                    "group": "merchant",
                    "color": "#10B981",
                    "val": 20,
                    "properties": {"id": b["child_id"], "name": b["child_name"], "category": "Bundled Service"}
                })
            self.edges.append({
                "id": f"e_{edge_id}",
                "source": p_mid,
                "target": c_mid,
                "type": "INCLUDES",
                "label": "INCLUDES",
                "color": "#F59E0B",
                "properties": {
                    "confidence": b.get("confidence", "confirmed_public"),
                    "verified_on": b.get("verified_on", "2026-01-01"),
                    "source_url": b.get("source_url", "TODO: fill link"),
                    "notes": b.get("notes", "")
                }
            })
            edge_id += 1

    def seed_bundle_reference_graph(self):
        """Seeds curated bundle relationships into live Neo4j Aura."""
        if not (self.is_connected and self.driver):
            return False, "Not connected to live Neo4j instance."
        cypher = """
        UNWIND $bundles AS b
        MERGE (p:Merchant {id: b.parent_id})
          ON CREATE SET p.name = b.parent_name
        MERGE (c:Merchant {id: b.child_id})
          ON CREATE SET c.name = b.child_name
        MERGE (p)-[r:INCLUDES]->(c)
        SET r.confidence = b.confidence,
            r.verified_on = date(b.verified_on),
            r.source_url = b.source_url,
            r.notes = b.notes
        RETURN count(r) AS created_edges;
        """
        try:
            with self.driver.session() as session:
                res = session.run(cypher, bundles=CURATED_BUNDLES)
                record = res.single()
                return True, f"Successfully seeded {record['created_edges']} INCLUDES relationships into Neo4j Aura."
        except Exception as e:
            return False, f"Failed to seed bundles into Neo4j Aura: {str(e)}"

    def sync_statement_mandates(self, person_name: str, mandates: List[Dict[str, Any]], person_id: str = "user_primary"):
        """
        Injects the user's detected mandates and charges into the graph:
        (Person)-[:HAS_MANDATE]->(Mandate)-[:FOR]->(Merchant)
        (Mandate)-[:VIA_MECHANISM]->(Mechanism)
        (Mandate)-[:HAD_CHARGE]->(Charge)
        """
        # Preserve status & cancel metadata if mandate was already present in graph
        existing_mandate_states = {}
        preserved_mandates = []
        incoming_ids = {m["id"] for m in mandates}

        for n in self.nodes:
            if n.get("label") == "Mandate":
                p = n.get("properties", {})
                mid = p.get("id") or n["id"].replace("mand_", "")
                existing_mandate_states[mid] = {
                    "status": p.get("status", "active"),
                    "cancel_confirmed_at": p.get("cancel_confirmed_at"),
                    "last_seen_charge_date": p.get("last_seen_charge_date"),
                    "expected_next_charge_date": p.get("expected_next_charge_date"),
                    "reminder_count": p.get("reminder_count", 0)
                }
                if mid not in incoming_ids and p.get("status") in ["cancel_confirmed_by_user", "still_charging", "verified_cancelled"]:
                    preserved_mandates.append(dict(p))

        # Remove old statement nodes if re-analyzing, keeping reference & overlap edges
        self.nodes = [n for n in self.nodes if n["group"] not in ["person", "mandate", "charge"]]
        self.edges = [e for e in self.edges if e["type"] not in ["HAS_MANDATE", "FOR", "VIA_MECHANISM", "HAD_CHARGE", "DECIDED_OVERLAP"]]

        self.nodes.append({
            "id": person_id,
            "label": "Person",
            "name": person_name,
            "group": "person",
            "color": "#F59E0B", # Amber
            "val": 32,
            "properties": {"id": person_id, "name": person_name, "account_type": "Primary Account Holder"}
        })

        edge_counter = len(self.edges) + 100
        seen_charge_hashes = set()
        aura_mandates = []
        aura_charges = []

        all_mandates = list(mandates) + preserved_mandates
        for mand in all_mandates:
            raw_id = mand["id"]
            mand_node_id = f"mand_{raw_id}"
            
            # Restore state if previously confirmed
            prev_state = existing_mandate_states.get(raw_id, {})
            current_status = mand.get("status") or prev_state.get("status") or "active"
            cancel_confirmed_at = mand.get("cancel_confirmed_at") or prev_state.get("cancel_confirmed_at")
            last_seen_charge = mand.get("last_seen_charge_date") or prev_state.get("last_seen_charge_date") or mand.get("last_charged")
            reminder_cnt = mand.get("reminder_count") if mand.get("reminder_count") is not None else prev_state.get("reminder_count", 0)

            # Compute next expected debit date if missing
            expected_next = mand.get("expected_next_charge_date") or prev_state.get("expected_next_charge_date")
            if not expected_next and mand.get("last_charged"):
                try:
                    last_dt = datetime.strptime(str(mand["last_charged"])[:10], "%Y-%m-%d")
                    days_add = 30 if "MONTH" in mand.get("cadence", "MONTHLY") else (90 if "QUART" in mand.get("cadence", "") else 365)
                    expected_next = (last_dt + timedelta(days=days_add)).strftime("%Y-%m-%d")
                except Exception:
                    expected_next = None

            mand["status"] = current_status
            mand["cancel_confirmed_at"] = cancel_confirmed_at
            mand["expected_next_charge_date"] = expected_next
            mand["last_seen_charge_date"] = last_seen_charge
            mand["reminder_count"] = reminder_cnt

            flag_color = {
                "PRICE_HIKE": "#F97316", # Orange
                "TRIAL_CONVERTED": "#EF4444", # Red
                "UNUSED_ZOMBIE": "#DC2626", # Deep Red
                "HEALTHY": "#10B981" # Green
            }.get(mand["flag"], "#3B82F6")

            # Color by status if cancellation lifecycle active
            if current_status == "still_charging":
                flag_color = "#DC2626"
            elif current_status == "verified_cancelled":
                flag_color = "#059669"
            elif current_status == "cancel_confirmed_by_user":
                flag_color = "#6B7280"

            m_amt = float(mand.get("latest_amount") or mand.get("amount") or 0.0)
            m_ann = float(mand.get("annual_committed_cost") or mand.get("annual_committed") or 0.0)
            m_cad = str(mand.get("cadence") or "MONTHLY")

            self.nodes.append({
                "id": mand_node_id,
                "label": "Mandate",
                "name": f"₹{m_amt:.0f} / {m_cad[0]}",
                "group": "mandate",
                "color": flag_color,
                "val": 22,
                "properties": {
                    "id": raw_id,
                    "status": current_status,
                    "cadence": m_cad,
                    "amount": m_amt,
                    "annual_committed": m_ann,
                    "flag": mand.get("flag", "HEALTHY"),
                    "flag_reason": mand.get("flag_reason", ""),
                    "descriptor": mand.get("descriptor", ""),
                    "merchant_id": mand.get("merchant_id"),
                    "merchant_name": mand.get("merchant_name"),
                    "expected_next_charge_date": expected_next,
                    "cancel_confirmed_at": cancel_confirmed_at,
                    "last_seen_charge_date": last_seen_charge,
                    "reminder_count": reminder_cnt
                }
            })

            # (Person)-[:HAS_MANDATE]->(Mandate)
            self.edges.append({
                "id": f"e_{edge_counter}",
                "source": person_id,
                "target": mand_node_id,
                "type": "HAS_MANDATE",
                "label": "HAS_MANDATE",
                "color": "#F59E0B"
            })
            edge_counter += 1

            # (Mandate)-[:FOR]->(Merchant)
            m_id = f"merch_{mand.get('merchant_id')}"
            if m_id in [n["id"] for n in self.nodes]:
                self.edges.append({
                    "id": f"e_{edge_counter}",
                    "source": mand_node_id,
                    "target": m_id,
                    "type": "FOR",
                    "label": "FOR",
                    "color": "#10B981"
                })
                edge_counter += 1

            # (Mandate)-[:VIA_MECHANISM]->(Mechanism)
            mech_id = f"mech_{mand.get('mechanism')}"
            if mech_id in [n["id"] for n in self.nodes]:
                self.edges.append({
                    "id": f"e_{edge_counter}",
                    "source": mand_node_id,
                    "target": mech_id,
                    "type": "VIA_MECHANISM",
                    "label": "VIA_MECHANISM",
                    "color": "#EC4899"
                })
                edge_counter += 1

            # Deduplicated charges: (Mandate)-[:HAD_CHARGE]->(Charge)
            for c in mand.get("history", []):
                amt_str = f"{float(c.get('amount', 0)):.2f}"
                c_desc = str(c.get("descriptor", ""))
                c_date = str(c.get("date", ""))[:10]
                hash_input = f"{c_date}_{amt_str}_{c_desc}_{person_id}"
                c_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

                charge_node_id = f"charge_{c_hash}"
                if charge_node_id not in seen_charge_hashes:
                    seen_charge_hashes.add(charge_node_id)
                    self.nodes.append({
                        "id": charge_node_id,
                        "label": "Charge",
                        "name": f"₹{float(amt_str):.0f} ({c_date})",
                        "group": "charge",
                        "color": "#94A3B8",
                        "val": 10,
                        "properties": {
                            "hash": c_hash,
                            "date": c_date,
                            "amount": float(amt_str),
                            "descriptor": c_desc
                        }
                    })

                self.edges.append({
                    "id": f"e_{edge_counter}",
                    "source": mand_node_id,
                    "target": charge_node_id,
                    "type": "HAD_CHARGE",
                    "label": "HAD_CHARGE",
                    "color": "#94A3B8"
                })
                edge_counter += 1

                aura_charges.append({
                    "mandate_id": raw_id,
                    "charge_hash": c_hash,
                    "date": c_date,
                    "amount": float(amt_str),
                    "descriptor": c_desc
                })

            aura_mandates.append({
                "id": raw_id,
                "status": current_status,
                "cadence": mand.get("cadence", "MONTHLY"),
                "latest_amount": float(mand.get("latest_amount", 0.0)),
                "annual_committed_cost": float(mand.get("annual_committed_cost", 0.0)),
                "flag": mand.get("flag", "HEALTHY"),
                "flag_reason": mand.get("flag_reason", ""),
                "descriptor": mand.get("descriptor", ""),
                "merchant_id": mand.get("merchant_id"),
                "mechanism": mand.get("mechanism", "CARD_SI"),
                "expected_next_charge_date": expected_next,
                "cancel_confirmed_at": cancel_confirmed_at,
                "last_seen_charge_date": last_seen_charge,
                "reminder_count": reminder_cnt
            })

        # Sync to live Neo4j Aura if connected
        if self.is_connected and self.driver:
            try:
                sync_cypher = """
                MERGE (p:Person {id: $uid})
                ON CREATE SET p.name = $person_name
                WITH p
                UNWIND $mandates AS m
                MERGE (mand:Mandate {id: m.id})
                SET mand.status = coalesce(m.status, 'active'),
                    mand.cadence = m.cadence,
                    mand.amount = m.latest_amount,
                    mand.annual_committed = m.annual_committed_cost,
                    mand.flag = m.flag,
                    mand.flag_reason = m.flag_reason,
                    mand.descriptor = m.descriptor,
                    mand.expected_next_charge_date = m.expected_next_charge_date,
                    mand.cancel_confirmed_at = m.cancel_confirmed_at,
                    mand.last_seen_charge_date = m.last_seen_charge_date,
                    mand.reminder_count = coalesce(m.reminder_count, 0)
                MERGE (p)-[:HAS_MANDATE]->(mand)
                WITH mand, m
                WHERE m.merchant_id IS NOT NULL
                MERGE (merch:Merchant {id: m.merchant_id})
                MERGE (mand)-[:FOR]->(merch);
                """
                with self.driver.session() as session:
                    session.run(sync_cypher, uid=person_id, person_name=person_name, mandates=aura_mandates)
                    if aura_charges:
                        charge_cypher = """
                        UNWIND $charges AS c
                        MATCH (mand:Mandate {id: c.mandate_id})
                        MERGE (ch:Charge {id: c.charge_hash})
                        ON CREATE SET ch.date = c.date, ch.amount = c.amount, ch.descriptor = c.descriptor
                        MERGE (mand)-[:HAD_CHARGE]->(ch);
                        """
                        session.run(charge_cypher, charges=aura_charges)
            except Exception as e:
                print(f"Warning: Live Neo4j mandate sync deferred: {e}")

    def find_bundle_overlaps(self, uid: str = "user_primary") -> List[Dict[str, Any]]:
        """
        Executes multi-hop variable-length path Cypher query to identify bundled service overlaps:
        MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(ma:Mandate)-[:FOR]->(a),
              (p)-[:HAS_MANDATE]->(mb:Mandate)-[:FOR]->(b)
        WHERE ma <> mb AND ma.status IN ['active','flagged_overlap'] AND mb.status IN ['active','flagged_overlap']
        MATCH path = (a)-[:INCLUDES*1..4]->(b)
        RETURN ma, mb, path
        """
        cypher = """
        MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(ma:Mandate)-[:FOR]->(a),
              (p)-[:HAS_MANDATE]->(mb:Mandate)-[:FOR]->(b)
        WHERE ma <> mb AND ma.status IN ['active','flagged_overlap'] AND mb.status IN ['active','flagged_overlap']
        MATCH path = (a)-[:INCLUDES*1..4]->(b)
        RETURN ma, mb, a, b,
               [n in nodes(path) | coalesce(n.name, n.id)] AS path_names,
               [r in relationships(path) | {confidence: r.confidence, notes: r.notes, source_url: r.source_url}] AS path_rels
        """

        if self.is_connected and self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, uid=uid)
                    records = []
                    for record in result:
                        ma = record["ma"]
                        mb = record["mb"]
                        a = record["a"]
                        b = record["b"]
                        path_names = record.get("path_names", [])
                        path_rels = record.get("path_rels", [{}])
                        redundant_cost = float(mb.get("annual_committed", mb.get("amount", 0) * 12))
                        first_rel = path_rels[0] if path_rels else {}
                        records.append({
                            "overlap_id": f"ov_{ma['id']}_{mb['id']}",
                            "parent_mandate": dict(ma),
                            "included_mandate": dict(mb),
                            "parent_service": a.get("name", ma.get("id")),
                            "included_service": b.get("name", mb.get("id")),
                            "path_nodes": path_names,
                            "path_explanation": f"{a.get('name', 'Parent')} includes {b.get('name', 'Child')} via bundle hierarchy.",
                            "potential_annual_saving": redundant_cost,
                            "confidence": first_rel.get("confidence", "confirmed_public"),
                            "verified_on": str(first_rel.get("verified_on", "2026-01-01")),
                            "source_url": first_rel.get("source_url", "TODO: fill link"),
                            "notes": first_rel.get("notes", "Bundle includes secondary service.")
                        })
                    return records
            except Exception as e:
                print(f"Neo4j Aura bundle query failed ({e}); evaluating on embedded graph engine.")

        # Embedded Graph Traversal: Emulates variable-length Cypher query (a)-[:INCLUDES*1..4]->(b)
        mandate_nodes = [
            n for n in self.nodes 
            if n["group"] == "mandate" and n.get("properties", {}).get("status", "active") in ["active", "flagged_overlap"]
        ]

        # Map each mandate to its merchant node
        mandate_to_merchant = {}
        for m in mandate_nodes:
            for e in self.edges:
                if e["source"] == m["id"] and e["type"] == "FOR":
                    merch_node = next((n for n in self.nodes if n["id"] == e["target"]), None)
                    if merch_node:
                        mandate_to_merchant[m["id"]] = merch_node

        # Build adjacency graph of INCLUDES edges
        includes_adj = {}
        includes_edge_data = {}
        for e in self.edges:
            if e["type"] == "INCLUDES":
                src = e["source"]
                tgt = e["target"]
                if src not in includes_adj:
                    includes_adj[src] = []
                includes_adj[src].append(tgt)
                includes_edge_data[(src, tgt)] = e.get("properties", {})

        def find_variable_path(start: str, target: str, max_depth: int = 4):
            queue = [[start]]
            while queue:
                path = queue.pop(0)
                node = path[-1]
                if node == target and len(path) > 1:
                    return path
                if len(path) <= max_depth:
                    for neighbor in includes_adj.get(node, []):
                        if neighbor not in path:
                            queue.append(path + [neighbor])
            return None

        overlaps = []
        seen_pairs = set()

        for ma in mandate_nodes:
            merch_a = mandate_to_merchant.get(ma["id"])
            if not merch_a:
                continue
            for mb in mandate_nodes:
                if ma["id"] == mb["id"]:
                    continue
                merch_b = mandate_to_merchant.get(mb["id"])
                if not merch_b:
                    continue

                pair_key = (ma["id"], mb["id"])
                if pair_key in seen_pairs:
                    continue

                path = find_variable_path(merch_a["id"], merch_b["id"], max_depth=4)
                if path:
                    seen_pairs.add(pair_key)
                    # Get path node names
                    path_names = [next((n["name"] for n in self.nodes if n["id"] == nid), nid) for nid in path]
                    edge_meta = includes_edge_data.get((path[0], path[1]), {})
                    saving = float(mb.get("properties", {}).get("annual_committed", 0.0))

                    # Update mandate status in embedded graph
                    if ma["properties"].get("status") == "active":
                        ma["properties"]["status"] = "flagged_overlap"
                    if mb["properties"].get("status") == "active":
                        mb["properties"]["status"] = "flagged_overlap"

                    overlaps.append({
                        "overlap_id": f"ov_{ma['properties'].get('id', ma['id'])}_{mb['properties'].get('id', mb['id'])}",
                        "parent_mandate": ma["properties"],
                        "included_mandate": mb["properties"],
                        "parent_service": merch_a["name"],
                        "included_service": merch_b["name"],
                        "path_nodes": path_names,
                        "path_explanation": f"{merch_a['name']} includes {merch_b['name']} via bundle hierarchy ({' ➔ '.join(path_names)}).",
                        "potential_annual_saving": saving,
                        "confidence": edge_meta.get("confidence", "confirmed_public"),
                        "verified_on": edge_meta.get("verified_on", "2026-01-01"),
                        "source_url": edge_meta.get("source_url", "TODO: fill link"),
                        "notes": edge_meta.get("notes", "Bundle includes secondary service.")
                    })

        return overlaps

    def record_overlap_decision(self, uid: str, kept_mandate_ids: List[str], cancel_mandate_ids: List[str]) -> Dict[str, Any]:
        """
        Stores user's overlap confirmation in graph:
        (:Person)-[:DECIDED_OVERLAP {decision: 'KEEP'|'SUGGESTED_CANCEL', timestamp}]->(:Mandate)
        Marks kept mandates as 'keep_confirmed' and redundant mandates as 'suggested_cancel'.
        """
        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Update in-memory graph
        for n in self.nodes:
            if n["group"] == "mandate":
                props = n.get("properties", {})
                mid = props.get("id") or n["id"].replace("mand_", "")
                if mid in kept_mandate_ids:
                    props["status"] = "keep_confirmed"
                    props["overlap_decision_at"] = now_iso
                elif mid in cancel_mandate_ids:
                    props["status"] = "suggested_cancel"
                    props["overlap_decision_at"] = now_iso

        # Live Aura execution
        if self.is_connected and self.driver:
            try:
                cypher_keep = """
                UNWIND $kept_ids AS kid
                MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(m:Mandate {id: kid})
                SET m.status = 'keep_confirmed', m.overlap_decision_at = datetime()
                MERGE (p)-[r:DECIDED_OVERLAP]->(m)
                SET r.decision = 'KEEP', r.timestamp = datetime();
                """
                cypher_cancel = """
                UNWIND $cancel_ids AS cid
                MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(m:Mandate {id: cid})
                SET m.status = 'suggested_cancel', m.overlap_decision_at = datetime()
                MERGE (p)-[r:DECIDED_OVERLAP]->(m)
                SET r.decision = 'SUGGESTED_CANCEL', r.timestamp = datetime();
                """
                with self.driver.session() as session:
                    if kept_mandate_ids:
                        session.run(cypher_keep, uid=uid, kept_ids=kept_mandate_ids)
                    if cancel_mandate_ids:
                        session.run(cypher_cancel, uid=uid, cancel_ids=cancel_mandate_ids)
            except Exception as e:
                print(f"Live Aura overlap decision sync deferred: {e}")

        return {
            "status": "SUCCESS",
            "kept_count": len(kept_mandate_ids),
            "suggested_cancel_count": len(cancel_mandate_ids),
            "timestamp": now_iso
        }

    def confirm_mandate_cancellation(self, uid: str, mandate_id: str, cancel_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Marks mandate as cancel_confirmed_by_user in graph when user clicks Confirm in popup.
        """
        cancel_dt = cancel_date or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Update in-memory graph
        for n in self.nodes:
            if n["group"] == "mandate":
                props = n.get("properties", {})
                mid = props.get("id") or n["id"].replace("mand_", "")
                if mid == mandate_id:
                    props["status"] = "cancel_confirmed_by_user"
                    props["cancel_confirmed_at"] = cancel_dt
                    props["reminder_count"] = 0
                    n["color"] = "#6B7280"

        # Update Live Aura
        if self.is_connected and self.driver:
            try:
                cypher = """
                MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(m:Mandate {id: $mid})
                SET m.status = 'cancel_confirmed_by_user',
                    m.cancel_confirmed_at = datetime($cancel_dt),
                    m.reminder_count = 0
                RETURN m;
                """
                with self.driver.session() as session:
                    session.run(cypher, uid=uid, mid=mandate_id, cancel_dt=cancel_dt.replace(" ", "T"))
            except Exception as e:
                print(f"Live Aura cancellation confirm deferred: {e}")

        return {
            "mandate_id": mandate_id,
            "status": "cancel_confirmed_by_user",
            "cancel_confirmed_at": cancel_dt
        }

    def reconcile_cancelled_mandates(self, uid: str, transactions: List[Dict[str, Any]], statement_end_date: str) -> Dict[str, Any]:
        """
        Reconciles mandates marked cancelled against new bank statement:
        - GRACE_WINDOW_DAYS = 3: Charges <= cancel_confirmed_at + 3 days are in-flight; do NOT flag.
        - Charges > cancel_confirmed_at + 3 days: Mandate is STILL CHARGING! Increment reminder_count, flag action required.
        - Zero charges & statement_end_date > expected_next_charge_date: Mandate is VERIFIED CANCELLED!
        """
        GRACE_WINDOW_DAYS = 3
        now_dt = datetime.strptime(str(statement_end_date)[:10], "%Y-%m-%d") if statement_end_date else datetime.utcnow()

        reconciliation_report = {
            "reconciled_count": 0,
            "still_charging": [],
            "verified_cancelled": [],
            "in_flight_grace": []
        }

        # Find cancelled mandates in embedded graph
        cancelled_mandates = []
        for n in self.nodes:
            if n["group"] == "mandate":
                p = n.get("properties", {})
                status = p.get("status")
                if status in ["cancel_confirmed_by_user", "still_charging"]:
                    cancelled_mandates.append(p)

        for mand in cancelled_mandates:
            mid = mand.get("id")
            cancel_str = mand.get("cancel_confirmed_at")
            if not cancel_str:
                continue

            try:
                cancel_dt = datetime.strptime(str(cancel_str)[:10], "%Y-%m-%d")
            except Exception:
                cancel_dt = now_dt - timedelta(days=30)

            expected_next_str = mand.get("expected_next_charge_date")
            try:
                expected_next_dt = datetime.strptime(str(expected_next_str)[:10], "%Y-%m-%d") if expected_next_str else cancel_dt + timedelta(days=30)
            except Exception:
                expected_next_dt = cancel_dt + timedelta(days=30)

            # Match incoming transactions using deterministic reference merchant resolution
            mand_desc = mand.get("descriptor", "").strip().lower()
            mand_merchant = mand.get("merchant_id", "")
            matching_txs = []
            for t in transactions:
                t_desc = str(t.get("descriptor", "")).strip()
                m_match = None
                try:
                    from detector import resolve_merchant_from_descriptor
                    m_match = resolve_merchant_from_descriptor(t_desc)
                except Exception:
                    m_match = None

                if m_match and mand_merchant and m_match.get("id") == mand_merchant:
                    matching_txs.append(t)
                elif mand_desc and mand_desc == t_desc.lower():
                    matching_txs.append(t)

            if matching_txs:
                # Charges detected! Check if in-flight grace or still charging
                latest_tx = max(matching_txs, key=lambda x: str(x.get("date", ""))[:10])
                tx_date_str = str(latest_tx.get("date", ""))[:10]
                tx_dt = datetime.strptime(tx_date_str, "%Y-%m-%d")

                grace_limit_dt = cancel_dt + timedelta(days=GRACE_WINDOW_DAYS)

                if tx_dt <= grace_limit_dt:
                    # In-flight charge within grace window
                    reconciliation_report["in_flight_grace"].append({
                        "mandate_id": mid,
                        "merchant_name": mand.get("merchant_name"),
                        "charge_date": tx_date_str,
                        "amount": latest_tx.get("amount"),
                        "note": f"Charge of ₹{latest_tx.get('amount')} fell within {GRACE_WINDOW_DAYS}-day in-flight billing grace window. No action needed."
                    })
                else:
                    # Charged after grace window: STILL CHARGING!
                    mand["status"] = "still_charging"
                    mand["reminder_count"] = int(mand.get("reminder_count", 0)) + 1
                    mand["last_seen_charge_date"] = tx_date_str

                    # Update node
                    for n in self.nodes:
                        if n["id"] == f"mand_{mid}":
                            n["properties"]["status"] = "still_charging"
                            n["properties"]["reminder_count"] = mand["reminder_count"]
                            n["properties"]["last_seen_charge_date"] = tx_date_str
                            n["color"] = "#DC2626"

                    reconciliation_report["still_charging"].append({
                        "mandate_id": mid,
                        "merchant_name": mand.get("merchant_name"),
                        "descriptor": mand.get("descriptor"),
                        "latest_charge_date": tx_date_str,
                        "amount": latest_tx.get("amount"),
                        "cancel_confirmed_at": str(cancel_str)[:10],
                        "reminder_count": mand["reminder_count"],
                        "message": f"ALERT: Auto-debit occurred on {tx_date_str} after you confirmed cancellation on {str(cancel_str)[:10]}."
                    })

            else:
                # No charges seen in this statement!
                if now_dt >= expected_next_dt:
                    # Billing cycle covered and zero debits: VERIFIED CANCELLED!
                    mand["status"] = "verified_cancelled"
                    for n in self.nodes:
                        if n["id"] == f"mand_{mid}":
                            n["properties"]["status"] = "verified_cancelled"
                            n["color"] = "#059669"

                    reconciliation_report["verified_cancelled"].append({
                        "mandate_id": mid,
                        "merchant_name": mand.get("merchant_name"),
                        "expected_next_charge_date": str(expected_next_dt)[:10],
                        "statement_end_date": str(now_dt)[:10],
                        "message": f"Verified successfully cancelled! No charges detected across billing period extending to {str(now_dt)[:10]}."
                    })

        reconciliation_report["reconciled_count"] = len(reconciliation_report["still_charging"]) + len(reconciliation_report["verified_cancelled"]) + len(reconciliation_report["in_flight_grace"])
        return reconciliation_report

    def run_cypher_query(self, cypher: str) -> Dict[str, Any]:
        """
        Executes a Cypher query on live Neo4j if connected,
        otherwise interprets preset queries against embedded graph.
        """
        if self.is_connected and self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher)
                    records = [record.data() for record in result]
                    return {
                        "mode": "NEO4J_AURA_LIVE",
                        "status": "SUCCESS",
                        "cypher": cypher,
                        "count": len(records),
                        "data": records
                    }
            except Exception as e:
                return {
                    "mode": "NEO4J_AURA_LIVE",
                    "status": "ERROR",
                    "error": str(e),
                    "cypher": cypher,
                    "data": []
                }

        # Embedded Cypher emulation
        cypher_upper = cypher.upper()

        # 1. Multi-merchant parent footprint query
        if "OWNED_BY" in cypher_upper or "PARENT" in cypher_upper:
            parent_groups = {}
            for e in self.edges:
                if e["type"] == "OWNED_BY":
                    m_node = next((n for n in self.nodes if n["id"] == e["source"]), None)
                    p_node = next((n for n in self.nodes if n["id"] == e["target"]), None)
                    if m_node and p_node:
                        p_name = p_node["name"]
                        if p_name not in parent_groups:
                            parent_groups[p_name] = {"parent": p_name, "merchants": [], "total_subs": 0}
                        parent_groups[p_name]["merchants"].append(m_node["name"])
                        parent_groups[p_name]["total_subs"] += 1
            return {
                "mode": "EMBEDDED_GRAPH_ENGINE",
                "status": "SUCCESS",
                "cypher": cypher,
                "count": len(parent_groups),
                "data": list(parent_groups.values())
            }

        # 2. Bundle Overlap / Variable-length path query (a)-[:INCLUDES*1..4]->(b)
        if "INCLUDES" in cypher_upper:
            overlaps = self.find_bundle_overlaps()
            return {
                "mode": "EMBEDDED_GRAPH_ENGINE",
                "status": "SUCCESS",
                "cypher": cypher,
                "count": len(overlaps),
                "data": overlaps
            }

        # 2. Cancellation route by mechanism query
        if "MECHANISM" in cypher_upper or "BILLED_VIA" in cypher_upper or "CANCELLED_BY" in cypher_upper:
            mech_routes = []
            for m in REFERENCE_MERCHANTS:
                mech_code = m.get("default_mechanism", "CARD_SI")
                mech_info = PAYMENT_MECHANISMS.get(mech_code, PAYMENT_MECHANISMS["CARD_SI"])
                mech_routes.append({
                    "merchant": m["name"],
                    "mechanism": mech_info["name"],
                    "turnaround": mech_info["turnaround_time"],
                    "primary_cancellation_step": mech_info["cancellation_steps"][0]
                })
            return {
                "mode": "EMBEDDED_GRAPH_ENGINE",
                "status": "SUCCESS",
                "cypher": cypher,
                "count": len(mech_routes),
                "data": mech_routes
            }

        # 3. High risk flags or price hike query
        if "FLAG" in cypher_upper or "PRICE_HIKE" in cypher_upper or "MANDATE" in cypher_upper:
            flagged = []
            for n in self.nodes:
                if n["label"] == "Mandate":
                    props = n.get("properties", {})
                    flagged.append({
                        "mandate_id": n["id"],
                        "amount": props.get("amount"),
                        "cadence": props.get("cadence"),
                        "annual_cost": props.get("annual_committed"),
                        "flag": props.get("flag"),
                        "flag_reason": props.get("flag_reason")
                    })
            return {
                "mode": "EMBEDDED_GRAPH_ENGINE",
                "status": "SUCCESS",
                "cypher": cypher,
                "count": len(flagged),
                "data": flagged
            }

        # Default fallback: return all nodes summary
        counts = {}
        for n in self.nodes:
            lbl = n.get("label", "Unknown")
            counts[lbl] = counts.get(lbl, 0) + 1
        return {
            "mode": "EMBEDDED_GRAPH_ENGINE",
            "status": "SUCCESS",
            "cypher": cypher,
            "count": len(self.nodes),
            "data": [{"node_label": k, "count": v} for k, v in counts.items()]
        }

    def generate_cypher_seed_script(self) -> str:
        """
        Generates full declarative Cypher DDL & Seed Script (.cql)
        ready to load into Neo4j Aura or Neo4j Desktop.
        """
        lines = [
            "// =================================================================",
            "// MANDATE RADAR: REFERENCE KNOWLEDGE GRAPH SEED SCRIPT (CYPHER)",
            "// Track: Neo4j (Best Use of Neo4j)",
            "// Theme: Fintech - The Auto Debits Nobody Can Find",
            "// =================================================================",
            "",
            "// 1. Constraints & Unique Indexes",
            "CREATE CONSTRAINT unique_merchant_id IF NOT EXISTS FOR (m:Merchant) REQUIRE m.id IS UNIQUE;",
            "CREATE CONSTRAINT unique_parent_id IF NOT EXISTS FOR (p:Parent) REQUIRE p.id IS UNIQUE;",
            "CREATE CONSTRAINT unique_mechanism_code IF NOT EXISTS FOR (mech:Mechanism) REQUIRE mech.code IS UNIQUE;",
            "CREATE CONSTRAINT unique_mandate_id IF NOT EXISTS FOR (mand:Mandate) REQUIRE mand.id IS UNIQUE;",
            "",
            "// 2. Parent Conglomerates",
        ]

        for pid, pdata in PARENT_COMPANIES.items():
            lines.append(
                f"MERGE (p:Parent {{id: '{pid}'}}) "
                f"ON CREATE SET p.name = '{pdata['name']}', p.ticker = '{pdata['ticker']}', "
                f"p.country = '{pdata['country']}', p.headquarters = '{pdata['headquarters']}';"
            )

        lines.append("")
        lines.append("// 3. Payment Mechanisms & Legal Rails")
        for mcode, mdata in PAYMENT_MECHANISMS.items():
            lines.append(
                f"MERGE (mech:Mechanism {{code: '{mcode}'}}) "
                f"ON CREATE SET mech.name = '{mdata['name']}', mech.authority = '{mdata['authority']}', "
                f"mech.turnaround = '{mdata['turnaround_time']}';"
            )

        lines.append("")
        lines.append("// 4. Merchants, Parent Hierarchy & Descriptors")
        for m in REFERENCE_MERCHANTS:
            mid = m["id"]
            mname = m["name"].replace("'", "\\'")
            cat = m["category"].replace("'", "\\'")
            amt = m.get("default_amount", 0.0)
            pid = m.get("parent_id")
            mech = m.get("default_mechanism", "CARD_SI")

            lines.append(
                f"MERGE (m:Merchant {{id: '{mid}'}}) "
                f"ON CREATE SET m.name = '{mname}', m.category = '{cat}', m.default_amount = {amt};"
            )

            if pid:
                lines.append(f"MATCH (m:Merchant {{id: '{mid}'}}), (p:Parent {{id: '{pid}'}}) MERGE (m)-[:OWNED_BY]->(p);")
            if mech:
                lines.append(f"MATCH (m:Merchant {{id: '{mid}'}}), (mech:Mechanism {{code: '{mech}'}}) MERGE (m)-[:BILLED_VIA]->(mech);")

            for pat in m.get("descriptors", [])[:2]:
                escaped_pat = pat.replace("\\", "\\\\").replace("'", "\\'")
                desc_key = f"desc_{abs(hash(pat)) % 1000000}"
                lines.append(
                    f"MERGE (d:Descriptor {{pattern: '{escaped_pat}'}}) "
                    f"MERGE (m:Merchant {{id: '{mid}'}}) "
                    f"MERGE (d)-[:RESOLVES_TO]->(m);"
                )

        lines.append("")
        lines.append("// 5. Curated Bundle Inclusions: (:Merchant)-[:INCLUDES]->(:Merchant)")
        for b in CURATED_BUNDLES:
            safe_notes = b['notes'].replace("'", "\\'")
            lines.append(
                f"MERGE (p:Merchant {{id: '{b['parent_id']}'}}) "
                f"MERGE (c:Merchant {{id: '{b['child_id']}'}}) "
                f"MERGE (p)-[r:INCLUDES]->(c) "
                f"ON CREATE SET r.confidence = '{b['confidence']}', r.verified_on = date('{b['verified_on']}'), "
                f"r.source_url = '{b['source_url']}', r.notes = '{safe_notes}';"
            )

        lines.append("")
        lines.append("// 6. Verification Query: Multi-Hop Bundle Overlap Traversal")
        lines.append("MATCH (p:Person)-[:HAS_MANDATE]->(ma:Mandate)-[:FOR]->(a:Merchant), (p)-[:HAS_MANDATE]->(mb:Mandate)-[:FOR]->(b:Merchant)")
        lines.append("WHERE ma <> mb MATCH path = (a)-[:INCLUDES*1..4]->(b)")
        lines.append("RETURN ma.id AS ParentMandate, mb.id AS RedundantMandate, [n in nodes(path) | n.name] AS PathNodes;")

        return "\n".join(lines)

    def get_graph_visualization_data(self, filter_mode: str = "portfolio") -> Dict[str, Any]:
        """
        Returns node/link payload for interactive Graph Visualizer.
        Filters by 'portfolio' (default, user's active mandates), 'alphabet', 'amazon',
        'streaming', or 'all' to prevent cluttered 270-node hairballs.
        """
        if filter_mode == "portfolio":
            # 1. Start with Person and Mandate nodes
            person_id = "user_primary"
            portfolio_mandate_ids = {n["id"] for n in self.nodes if n["group"] == "mandate"}
            active_ids = {person_id}.union(portfolio_mandate_ids)

            # 2. Find merchants and rails linked directly to user mandates
            merchant_ids = set()
            rail_ids = set()
            mandate_edges = []

            for e in self.edges:
                if e["source"] in portfolio_mandate_ids or e["target"] in portfolio_mandate_ids or e["source"] == person_id:
                    mandate_edges.append(e)
                    active_ids.add(e["source"])
                    active_ids.add(e["target"])
                    if e["type"] == "FOR":
                        merchant_ids.add(e["target"])
                    if e["type"] == "VIA_MECHANISM":
                        rail_ids.add(e["target"])

            # 3. From ONLY the active merchants, find their parents (OUTGOING ONLY, so unrelated merchants aren't pulled in)
            parent_edges = []
            for e in self.edges:
                if e["source"] in merchant_ids and e["type"] == "OWNED_BY":
                    parent_edges.append(e)
                    active_ids.add(e["target"])

            all_portfolio_edges = mandate_edges + parent_edges
            filtered_nodes = [n for n in self.nodes if n["id"] in active_ids]
            filtered_edges = all_portfolio_edges

        elif filter_mode == "alphabet":
            target_parent = "parent_alphabet"
            sub_ids = {target_parent}
            for e in self.edges:
                if e["target"] == target_parent or e["source"] == target_parent:
                    sub_ids.add(e["source"])
                    sub_ids.add(e["target"])
            for e in self.edges:
                if e["source"] in sub_ids or e["target"] in sub_ids:
                    sub_ids.add(e["source"])
                    sub_ids.add(e["target"])
            filtered_nodes = [n for n in self.nodes if n["id"] in sub_ids]
            filtered_edges = [e for e in self.edges if e["source"] in sub_ids and e["target"] in sub_ids]

        elif filter_mode == "amazon":
            target_parent = "parent_amazon"
            sub_ids = {target_parent}
            for e in self.edges:
                if e["target"] == target_parent or e["source"] == target_parent:
                    sub_ids.add(e["source"])
                    sub_ids.add(e["target"])
            for e in self.edges:
                if e["source"] in sub_ids or e["target"] in sub_ids:
                    sub_ids.add(e["source"])
                    sub_ids.add(e["target"])
            filtered_nodes = [n for n in self.nodes if n["id"] in sub_ids]
            filtered_edges = [e for e in self.edges if e["source"] in sub_ids and e["target"] in sub_ids]

        elif filter_mode == "streaming":
            streaming_mids = {"merch_youtube_premium", "merch_netflix_india", "merch_spotify_india", "merch_disney_hotstar", "merch_sony_liv", "merch_zee5", "merch_jiocinema_premium"}
            sub_ids = set(streaming_mids)
            for e in self.edges:
                if e["source"] in streaming_mids or e["target"] in streaming_mids:
                    sub_ids.add(e["source"])
                    sub_ids.add(e["target"])
            filtered_nodes = [n for n in self.nodes if n["id"] in sub_ids]
            filtered_edges = [e for e in self.edges if e["source"] in sub_ids and e["target"] in sub_ids]

        else: # "all"
            filtered_nodes = self.nodes
            filtered_edges = self.edges

        return {
            "filter_mode": filter_mode,
            "nodes": filtered_nodes,
            "edges": filtered_edges,
            "stats": {
                "total_nodes": len(filtered_nodes),
                "total_edges": len(filtered_edges),
                "parents": sum(1 for n in filtered_nodes if n["label"] == "Parent"),
                "merchants": sum(1 for n in filtered_nodes if n["label"] == "Merchant"),
                "mechanisms": sum(1 for n in filtered_nodes if n["label"] == "Mechanism"),
                "descriptors": sum(1 for n in filtered_nodes if n["label"] == "Descriptor"),
                "mandates": sum(1 for n in filtered_nodes if n["label"] == "Mandate")
            }
        }
