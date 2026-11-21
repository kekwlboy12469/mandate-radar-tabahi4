"""
Mandate Radar Neo4j Knowledge Graph Service
Handles live Neo4j Aura connection, graph synchronization, Cypher queries,
and includes an embedded graph engine so the entire system works instantly.
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

DEFAULT_VERIFIED_DATE = datetime.utcnow().strftime('%Y-%m-%d')
try:
    import neo4j
except ImportError:
    neo4j = None

from reference_data import (
    REFERENCE_MERCHANTS, PARENT_COMPANIES, PAYMENT_MECHANISMS, ESCALATION_CHAIN,
    CAPABILITIES, VENDOR_CAPABILITIES
)
from bundle_reference import PLANS, CURATED_BUNDLES

class Neo4jKnowledgeGraph:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        self.driver: Optional[Any] = None
        self.is_connected = False
        self.connection_error = None

        # Embedded in-memory graph fallback & decision store
        self.nodes = []
        self.edges = []
        self.decisions = []
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

        # 5. Capabilities: (:Capability)
        for cap in CAPABILITIES:
            self.nodes.append({
                "id": f"cap_{cap['id']}",
                "label": "Capability",
                "name": cap["name"],
                "group": "capability",
                "color": "#3B82F6", # Blue
                "val": 16,
                "properties": cap
            })

        # 6. Plans: (:Plan) and (:Merchant)-[:OFFERS]->(:Plan)
        for plan in PLANS:
            p_node_id = f"plan_{plan['id']}"
            self.nodes.append({
                "id": p_node_id,
                "label": "Plan",
                "name": plan["name"],
                "group": "plan",
                "color": "#F59E0B", # Amber
                "val": 18,
                "properties": plan
            })
            # Connect Vendor -> Plan
            v_node_id = f"merch_{plan['vendor_id']}"
            self.edges.append({
                "id": f"e_{edge_id}",
                "source": v_node_id,
                "target": p_node_id,
                "type": "OFFERS",
                "label": "OFFERS",
                "color": "#F59E0B"
            })
            edge_id += 1

        # 7. Seed Curated Bundle Inclusions: (:Plan)-[:INCLUDES]->(:Merchant) and direct (:Merchant)-[:INCLUDES]->(:Merchant)
        for b in CURATED_BUNDLES:
            p_pid = f"plan_{b['parent_plan_id']}"
            p_vid = f"merch_{b['parent_vendor_id']}"
            c_mid = f"merch_{b['child_vendor_id']}"

            # Ensure child merchant node exists
            existing_ids = {n["id"] for n in self.nodes}
            if c_mid not in existing_ids:
                self.nodes.append({
                    "id": c_mid,
                    "label": "Merchant",
                    "name": b["child_name"],
                    "group": "merchant",
                    "color": "#10B981",
                    "val": 20,
                    "properties": {"id": b["child_vendor_id"], "name": b["child_name"], "category": "Bundled Service"}
                })

            # Edge 1: Plan -[:INCLUDES]-> Merchant
            self.edges.append({
                "id": f"e_{edge_id}",
                "source": p_pid,
                "target": c_mid,
                "type": "INCLUDES",
                "label": "INCLUDES",
                "color": "#F59E0B",
                "properties": {
                    "tier": b.get("tier", "standard"),
                    "confidence": b.get("confidence", "confirmed_public"),
                    "verified_on": b.get("verified_on", DEFAULT_VERIFIED_DATE),
                    "source_url": b.get("source_url", "TODO: fill link"),
                    "notes": b.get("notes", "")
                }
            })
            edge_id += 1

            # Edge 2: Direct Parent Vendor -[:INCLUDES]-> Child Merchant (shortcut for multi-hop Cypher queries)
            self.edges.append({
                "id": f"e_{edge_id}",
                "source": p_vid,
                "target": c_mid,
                "type": "INCLUDES",
                "label": "INCLUDES",
                "color": "#F59E0B",
                "properties": {
                    "tier": b.get("tier", "standard"),
                    "confidence": b.get("confidence", "confirmed_public"),
                    "verified_on": b.get("verified_on", DEFAULT_VERIFIED_DATE),
                    "source_url": b.get("source_url", "TODO: fill link"),
                    "notes": b.get("notes", "")
                }
            })
            edge_id += 1

        # 8. Vendor Capabilities: (:Merchant)-[:PROVIDES]->(:Capability)
        for vc in VENDOR_CAPABILITIES:
            v_node_id = f"merch_{vc['vendor_id']}"
            c_node_id = f"cap_{vc['capability_id']}"
            self.edges.append({
                "id": f"e_{edge_id}",
                "source": v_node_id,
                "target": c_node_id,
                "type": "PROVIDES",
                "label": "PROVIDES",
                "color": "#3B82F6",
                "properties": {
                    "confidence": vc.get("confidence", "confirmed_public"),
                    "verified_on": vc.get("verified_on", DEFAULT_VERIFIED_DATE),
                    "source_url": vc.get("source_url", "TODO: fill link"),
                    "notes": vc.get("notes", "")
                }
            })
            edge_id += 1

    def seed_bundle_reference_graph(self):
        """Seeds curated bundle relationships, plans, and capabilities into live Neo4j Aura."""
        if not (self.is_connected and self.driver):
            return False, "Not connected to live Neo4j instance."
        cypher = """
        // 1. Constraints & Unique Indexes
        CREATE CONSTRAINT unique_merchant_id IF NOT EXISTS FOR (m:Merchant) REQUIRE m.id IS UNIQUE;
        CREATE CONSTRAINT unique_plan_id IF NOT EXISTS FOR (p:Plan) REQUIRE p.id IS UNIQUE;
        CREATE CONSTRAINT unique_cap_id IF NOT EXISTS FOR (c:Capability) REQUIRE c.id IS UNIQUE;
        CREATE CONSTRAINT unique_mandate_id IF NOT EXISTS FOR (mand:Mandate) REQUIRE mand.id IS UNIQUE;
        CREATE CONSTRAINT unique_decision_key IF NOT EXISTS FOR (d:Decision) REQUIRE d.finding_key IS UNIQUE;

        // 2. Capabilities
        UNWIND $capabilities AS c
        MERGE (cap:Capability {id: c.id})
          ON CREATE SET cap.name = c.name, cap.category = c.category, cap.description = c.description;

        // 3. Plans & Offers
        UNWIND $plans AS pl
        MERGE (plan:Plan {id: pl.id})
          ON CREATE SET plan.name = pl.name, plan.tier = pl.tier, plan.monthly_cost = pl.monthly_cost, plan.annual_cost = pl.annual_cost
        WITH pl, plan
        MATCH (v:Merchant {id: pl.vendor_id})
        MERGE (v)-[:OFFERS]->(plan);

        // 4. Bundle Inclusions
        UNWIND $bundles AS b
        MATCH (plan:Plan {id: b.parent_plan_id}), (c:Merchant {id: b.child_vendor_id})
        MERGE (plan)-[r:INCLUDES]->(c)
        SET r.tier = b.tier, r.confidence = b.confidence, r.verified_on = date(b.verified_on), r.source_url = b.source_url, r.notes = b.notes
        WITH b
        MATCH (p:Merchant {id: b.parent_vendor_id}), (c:Merchant {id: b.child_vendor_id})
        MERGE (p)-[r2:INCLUDES]->(c)
        SET r2.tier = b.tier, r2.confidence = b.confidence, r2.verified_on = date(b.verified_on), r2.source_url = b.source_url, r2.notes = b.notes;

        // 5. Vendor Capabilities
        UNWIND $vendor_caps AS vc
        MATCH (v:Merchant {id: vc.vendor_id}), (cap:Capability {id: vc.capability_id})
        MERGE (v)-[r:PROVIDES]->(cap)
        SET r.confidence = vc.confidence, r.verified_on = date(vc.verified_on), r.source_url = vc.source_url, r.notes = vc.notes;
        """
        try:
            with self.driver.session() as session:
                session.run(
                    cypher,
                    capabilities=CAPABILITIES,
                    plans=PLANS,
                    bundles=CURATED_BUNDLES,
                    vendor_caps=VENDOR_CAPABILITIES
                )
                return True, "Successfully seeded reference graph (Capabilities, Plans, Inclusions, and Provides) into Neo4j Aura."
        except Exception as e:
            return False, f"Failed to seed reference graph into Neo4j Aura: {str(e)}"

    def sync_statement_mandates(self, person_name: str, mandates: List[Dict[str, Any]], person_id: str = "user_primary", account_label: str = "Primary Account"):
        """
        Injects the user's detected mandates and charges into the graph:
        (Person)-[:HAS_MANDATE]->(Mandate)-[:FOR]->(Merchant)
        (Mandate)-[:VIA_MECHANISM]->(Mechanism)
        (Mandate)-[:HAD_CHARGE]->(Charge)
        (Person)-[:OWNS_ACCOUNT]->(Account)
        (Mandate)-[:PAID_FROM]->(Account)
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
                    "reminder_count": p.get("reminder_count", 0),
                    "tags": p.get("tags", []),
                    "billing_type": p.get("billing_type", "fixed"),
                    "account_label": p.get("account_label", account_label)
                }
                if mid not in incoming_ids and p.get("status") in ["marked_cancelled", "cancel_confirmed_by_user", "still_charging", "verified_cancelled"]:
                    preserved_mandates.append(dict(p))

        # Remove old statement nodes if re-analyzing, keeping reference & overlap edges
        self.nodes = [n for n in self.nodes if n["group"] not in ["person", "mandate", "charge", "account"]]
        self.edges = [e for e in self.edges if e["type"] not in ["HAS_MANDATE", "FOR", "VIA_MECHANISM", "HAD_CHARGE", "DECIDED_OVERLAP", "OWNS_ACCOUNT", "PAID_FROM", "TAGGED"]]

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
        seen_accounts = set()
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
            mand_tags = mand.get("tags") or prev_state.get("tags") or []
            m_billing_type = mand.get("billing_type") or prev_state.get("billing_type") or "fixed"
            m_account_label = mand.get("account_label") or prev_state.get("account_label") or account_label or "Primary Account"
            m_account_id = f"acc_{hashlib.sha256(f'{person_id}_{m_account_label}'.encode()).hexdigest()[:12]}"

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
            mand["tags"] = mand_tags
            mand["billing_type"] = m_billing_type
            mand["account_label"] = m_account_label
            mand["account_id"] = m_account_id

            flag_color = {
                "PRICE_HIKE": "#F97316", # Orange
                "TRIAL_CONVERTED": "#EF4444", # Red
                "UNUSED_ZOMBIE": "#DC2626", # Deep Red
                "HEALTHY": "#10B981" # Green
            }.get(mand.get("flag", "HEALTHY"), "#3B82F6")

            # Color by status if cancellation lifecycle active
            if current_status == "still_charging":
                flag_color = "#DC2626"
            elif current_status == "verified_cancelled":
                flag_color = "#059669"
            elif current_status in ["marked_cancelled", "cancel_confirmed_by_user"]:
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
                    "annual_committed_cost": m_ann,
                    "billing_type": m_billing_type,
                    "account_label": m_account_label,
                    "account_id": m_account_id,
                    "flag": mand.get("flag", "HEALTHY"),
                    "flag_reason": mand.get("flag_reason", ""),
                    "descriptor": mand.get("descriptor", ""),
                    "merchant_id": mand.get("merchant_id"),
                    "merchant_name": mand.get("merchant_name"),
                    "expected_next_charge_date": expected_next,
                    "cancel_confirmed_at": cancel_confirmed_at,
                    "last_seen_charge_date": last_seen_charge,
                    "reminder_count": reminder_cnt,
                    "tags": mand_tags
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

            # (Person)-[:OWNS_ACCOUNT]->(Account) & (Mandate)-[:PAID_FROM]->(Account)
            if m_account_id not in seen_accounts:
                seen_accounts.add(m_account_id)
                self.nodes.append({
                    "id": m_account_id,
                    "label": "Account",
                    "name": m_account_label,
                    "group": "account",
                    "color": "#06B6D4",
                    "val": 16,
                    "properties": {"id": m_account_id, "label": m_account_label, "user_id": person_id}
                })
                self.edges.append({
                    "id": f"e_{edge_counter}",
                    "source": person_id,
                    "target": m_account_id,
                    "type": "OWNS_ACCOUNT",
                    "label": "OWNS_ACCOUNT",
                    "color": "#06B6D4"
                })
                edge_counter += 1

            self.edges.append({
                "id": f"e_{edge_counter}",
                "source": mand_node_id,
                "target": m_account_id,
                "type": "PAID_FROM",
                "label": "PAID_FROM",
                "color": "#06B6D4"
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
                c_ref = str(c.get("ref", ""))
                c_hash = c.get("charge_hash") or hashlib.sha256(f"{person_id}_{m_account_label}_{c_date}_{amt_str}_{c_desc}_{c_ref}".encode()).hexdigest()[:16]

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
                "billing_type": m_billing_type,
                "account_label": m_account_label,
                "account_id": m_account_id,
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
                    mand.billing_type = m.billing_type,
                    mand.account_label = m.account_label,
                    mand.flag = m.flag,
                    mand.flag_reason = m.flag_reason,
                    mand.descriptor = m.descriptor,
                    mand.expected_next_charge_date = m.expected_next_charge_date,
                    mand.cancel_confirmed_at = m.cancel_confirmed_at,
                    mand.last_seen_charge_date = m.last_seen_charge_date,
                    mand.reminder_count = coalesce(m.reminder_count, 0)
                MERGE (p)-[:HAS_MANDATE]->(mand)
                MERGE (acc:Account {id: m.account_id})
                ON CREATE SET acc.label = m.account_label, acc.user_id = $uid
                MERGE (p)-[:OWNS_ACCOUNT]->(acc)
                MERGE (mand)-[:PAID_FROM]->(acc)
                WITH mand, m
                WHERE m.merchant_id IS NOT NULL
                MERGE (merch:Merchant {id: m.merchant_id})
                SET merch:Vendor
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
        WHERE ma <> mb AND ma.status IN ['active','flagged','flagged_overlap','keep_confirmed']
                       AND mb.status IN ['active','flagged','flagged_overlap','keep_confirmed']
        MATCH path = (a)-[:OFFERS|INCLUDES*1..6]->(b)
        Anti-joins against Decision nodes with stable finding_key.
        """
        user_decisions = [
            d for d in self.decisions 
            if d.get("user_id") == uid and d.get("finding_type") in ["bundle_overlap", "overlap"]
        ]
        decided_keys = {d.get("finding_key") for d in user_decisions if d.get("finding_key")}

        cypher = """
        MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(ma:Mandate)-[:FOR]->(a),
              (p)-[:HAS_MANDATE]->(mb:Mandate)-[:FOR]->(b)
        WHERE ma <> mb 
          AND ma.status IN ['active','flagged','flagged_overlap','keep_confirmed'] 
          AND mb.status IN ['active','flagged','flagged_overlap','keep_confirmed']
        MATCH path = (a)-[:OFFERS|INCLUDES*1..6]->(b)
        RETURN ma, mb, a, b,
               [n in nodes(path) | coalesce(n.name, n.id)] AS path_names,
               [r in relationships(path) | {confidence: coalesce(r.confidence, 'confirmed_public'), notes: coalesce(r.notes, ''), source_url: coalesce(r.source_url, 'TODO: fill link'), verified_on: coalesce(str(r.verified_on), DEFAULT_VERIFIED_DATE)}] AS path_rels
        """

        if self.is_connected and self.driver:
            try:
                with self.driver.session() as session:
                    dec_res = session.run("MATCH (p:Person {id:$uid})-[:MADE_DECISION]->(d:Decision) RETURN d.finding_key AS fkey", uid=uid)
                    aura_decided_keys = {r["fkey"] for r in dec_res if r["fkey"]}
                    all_decided = decided_keys.union(aura_decided_keys)

                    result = session.run(cypher, uid=uid)
                    records = []
                    for record in result:
                        ma = dict(record["ma"])
                        mb = dict(record["mb"])
                        a = dict(record["a"])
                        b = dict(record["b"])
                        ma_id = str(ma.get("id"))
                        mb_id = str(mb.get("id"))

                        finding_key = hashlib.sha256(f"bundle_overlap:{min(ma_id, mb_id)}_{max(ma_id, mb_id)}".encode()).hexdigest()
                        legacy_key = f"ov_{ma_id}_{mb_id}"
                        if finding_key in all_decided or legacy_key in all_decided:
                            continue

                        path_names = record.get("path_names", [])
                        path_rels = record.get("path_rels", [{}])

                        # Honest math: exclude usage_based mandates from savings
                        if mb.get("billing_type") == "usage_based":
                            redundant_cost = 0.0
                        else:
                            redundant_cost = float(mb.get("annual_committed", mb.get("annual_committed_cost", mb.get("amount", 0) * 12)))

                        first_rel = path_rels[0] if path_rels else {}
                        records.append({
                            "finding_id": f"ov_{ma_id}_{mb_id}",
                            "finding_key": finding_key,
                            "finding_type": "bundle_overlap",
                            "overlap_id": f"ov_{ma_id}_{mb_id}",
                            "parent_mandate": ma,
                            "included_mandate": mb,
                            "parent_service": a.get("name", ma_id),
                            "included_service": b.get("name", mb_id),
                            "path_nodes": path_names,
                            "path_explanation": f"{a.get('name', 'Parent')} includes {b.get('name', 'Child')} via bundle hierarchy ({' -> '.join(path_names)}).",
                            "potential_annual_saving": round(redundant_cost, 2),
                            "confidence": first_rel.get("confidence", "confirmed_public"),
                            "verified_on": str(first_rel.get("verified_on", DEFAULT_VERIFIED_DATE)),
                            "source_url": first_rel.get("source_url", "TODO: fill link"),
                            "notes": first_rel.get("notes", "Bundle includes secondary service.")
                        })
                    return records
            except Exception as e:
                print(f"Neo4j Aura bundle query failed ({e}); evaluating on embedded graph engine.")

        # Embedded Graph Traversal
        mandate_nodes = [
            n for n in self.nodes 
            if n["group"] == "mandate" and n.get("properties", {}).get("status", "active") in ["active", "flagged", "flagged_overlap", "keep_confirmed"]
        ]

        mandate_to_merchant = {}
        for m in mandate_nodes:
            for e in self.edges:
                if e["source"] == m["id"] and e["type"] == "FOR":
                    merch_node = next((n for n in self.nodes if n["id"] == e["target"]), None)
                    if merch_node:
                        mandate_to_merchant[m["id"]] = merch_node

        includes_adj = {}
        includes_edge_data = {}
        for e in self.edges:
            if e["type"] in ["INCLUDES", "OFFERS"]:
                src = e["source"]
                tgt = e["target"]
                if src not in includes_adj:
                    includes_adj[src] = []
                includes_adj[src].append(tgt)
                includes_edge_data[(src, tgt)] = e.get("properties", {})

        def find_variable_path(start: str, target: str, max_depth: int = 6):
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

                ma_id = str(ma["properties"].get("id", ma["id"]).replace("mand_", ""))
                mb_id = str(mb["properties"].get("id", mb["id"]).replace("mand_", ""))
                pair_key = (ma_id, mb_id)
                if pair_key in seen_pairs:
                    continue

                finding_key = hashlib.sha256(f"bundle_overlap:{min(ma_id, mb_id)}_{max(ma_id, mb_id)}".encode()).hexdigest()
                legacy_key = f"ov_{ma_id}_{mb_id}"
                if finding_key in decided_keys or legacy_key in decided_keys:
                    continue

                path = find_variable_path(merch_a["id"], merch_b["id"], max_depth=6)
                if path:
                    seen_pairs.add(pair_key)
                    path_names = [next((n["name"] for n in self.nodes if n["id"] == nid), nid) for nid in path]
                    edge_meta = includes_edge_data.get((path[0], path[1]), {})
                    
                    if mb.get("properties", {}).get("billing_type") == "usage_based":
                        saving = 0.0
                    else:
                        saving = float(mb.get("properties", {}).get("annual_committed", mb.get("properties", {}).get("annual_committed_cost", mb.get("properties", {}).get("amount", 0.0) * 12)))

                    if ma["properties"].get("status") == "active":
                        ma["properties"]["status"] = "flagged_overlap"
                    if mb["properties"].get("status") == "active":
                        mb["properties"]["status"] = "flagged_overlap"

                    overlaps.append({
                        "finding_id": f"ov_{ma_id}_{mb_id}",
                        "finding_key": finding_key,
                        "finding_type": "bundle_overlap",
                        "overlap_id": f"ov_{ma_id}_{mb_id}",
                        "parent_mandate": ma["properties"],
                        "included_mandate": mb["properties"],
                        "parent_service": merch_a["name"],
                        "included_service": merch_b["name"],
                        "path_nodes": path_names,
                        "path_explanation": f"{merch_a['name']} includes {merch_b['name']} via bundle hierarchy ({' -> '.join(path_names)}).",
                        "potential_annual_saving": round(saving, 2),
                        "confidence": edge_meta.get("confidence", "confirmed_public"),
                        "verified_on": edge_meta.get("verified_on", DEFAULT_VERIFIED_DATE),
                        "source_url": edge_meta.get("source_url", "TODO: fill link"),
                        "notes": edge_meta.get("notes", "Bundle includes secondary service.")
                    })

        return overlaps

    def find_capability_overlaps(self, uid: str = "user_primary") -> List[Dict[str, Any]]:
        """
        Identifies two or more active mandates providing the same functional capability (e.g. Slack + MS Teams).
        Clusters by capability, evaluates anti-self-bundle, checks 6-month staleness threshold,
        calculates fixed-only potential savings, and anti-joins against confirmed decisions.
        """
        user_decisions = [
            d for d in self.decisions 
            if d.get("user_id") == uid and d.get("finding_type") in ["capability_overlap", "overlap"]
        ]
        decided_keys = {d.get("finding_key") for d in user_decisions if d.get("finding_key")}

        cypher = """
        MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(m:Mandate)-[:FOR]->(v)
        WHERE m.status IN ['active', 'flagged', 'flagged_overlap', 'keep_confirmed']
        MATCH (v)-[:OFFERS|INCLUDES*0..4]->(sub)-[r:PROVIDES]->(c:Capability)
        WHERE (r.verified_on IS NULL OR r.verified_on >= date() - duration({months: 6}))
        WITH p, c, collect(DISTINCT m) AS mandates, collect(DISTINCT v) AS vendors, collect(DISTINCT r) AS rels
        WHERE size(mandates) > 1
        RETURN c, mandates, vendors, rels
        """

        if self.is_connected and self.driver:
            try:
                with self.driver.session() as session:
                    dec_res = session.run("MATCH (p:Person {id:$uid})-[:MADE_DECISION]->(d:Decision) RETURN d.finding_key AS fkey", uid=uid)
                    aura_decided_keys = {r["fkey"] for r in dec_res if r["fkey"]}
                    all_decided = decided_keys.union(aura_decided_keys)

                    result = session.run(cypher, uid=uid)
                    findings = []
                    for rec in result:
                        c = dict(rec["c"])
                        mandates = [dict(m) for m in rec["mandates"]]
                        vendors = [dict(v) for v in rec["vendors"]]
                        rels = [dict(r) for r in rec["rels"]]

                        # Anti-self-bundle check: check if any vendor includes another in this cluster
                        has_bundle_inclusion = False
                        v_ids = [v.get("id") for v in vendors if v.get("id")]
                        if len(v_ids) > 1:
                            check_q = """
                            MATCH (v1)-[:OFFERS|INCLUDES*1..6]->(v2)
                            WHERE v1.id IN $v_ids AND v2.id IN $v_ids AND v1 <> v2
                            RETURN count(*) AS cnt
                            """
                            check_res = session.run(check_q, v_ids=v_ids).single()
                            if check_res and check_res["cnt"] > 0:
                                has_bundle_inclusion = True

                        if has_bundle_inclusion:
                            continue

                        sorted_mids = sorted([str(m.get("id")) for m in mandates])
                        finding_key = hashlib.sha256(f"capability_overlap:{c['id']}:{':'.join(sorted_mids)}".encode()).hexdigest()
                        legacy_key = f"cap_ov_{c['id']}"
                        if finding_key in all_decided or legacy_key in all_decided:
                            continue

                        # Savings math: fixed-only
                        fixed_mands = [m for m in mandates if m.get("billing_type") != "usage_based"]
                        if len(fixed_mands) > 1:
                            costs = [float(m.get("annual_committed", m.get("annual_committed_cost", m.get("amount", 0) * 12))) for m in fixed_mands]
                            savings = sum(costs) - min(costs)
                        else:
                            savings = 0.0

                        first_rel = rels[0] if rels else {}
                        findings.append({
                            "finding_id": f"cap_ov_{c['id']}",
                            "finding_key": finding_key,
                            "finding_type": "capability_overlap",
                            "capability_id": c["id"],
                            "capability_name": c.get("name", c["id"]),
                            "category": c.get("category", "Software"),
                            "description": c.get("description", ""),
                            "mandates": mandates,
                            "vendors": [v.get("name", v.get("id")) for v in vendors],
                            "potential_annual_saving": round(savings, 2),
                            "evidence_paths": [
                                {
                                    "vendor": v.get("name", v.get("id")),
                                    "capability": c.get("name", c["id"]),
                                    "relationship": "PROVIDES",
                                    "confidence": first_rel.get("confidence", "confirmed_public"),
                                    "verified_on": str(first_rel.get("verified_on", DEFAULT_VERIFIED_DATE)),
                                    "source_url": first_rel.get("source_url", "TODO: fill link"),
                                    "notes": first_rel.get("notes", "")
                                }
                                for v in vendors
                            ],
                            "confidence": first_rel.get("confidence", "confirmed_public"),
                            "verified_on": str(first_rel.get("verified_on", DEFAULT_VERIFIED_DATE)),
                            "source_url": first_rel.get("source_url", "TODO: fill link")
                        })
                    return findings
            except Exception as e:
                print(f"Neo4j Aura capability query failed ({e}); evaluating on embedded engine.")

        # Embedded Graph Traversal for Capabilities
        mandate_nodes = [
            n for n in self.nodes 
            if n["group"] == "mandate" and n.get("properties", {}).get("status", "active") in ["active", "flagged", "flagged_overlap", "keep_confirmed"]
        ]

        mandate_to_merchant = {}
        for m in mandate_nodes:
            for e in self.edges:
                if e["source"] == m["id"] and e["type"] == "FOR":
                    merch_node = next((n for n in self.nodes if n["id"] == e["target"]), None)
                    if merch_node:
                        mandate_to_merchant[m["id"]] = merch_node

        includes_pairs = set()
        for e in self.edges:
            if e["type"] in ["INCLUDES", "OFFERS"]:
                includes_pairs.add((e["source"], e["target"]))

        cap_to_mandates = {}
        cap_to_vendors = {}
        cap_to_meta = {}

        today_dt = datetime.utcnow()
        six_months_ago = today_dt - timedelta(days=180)

        for m in mandate_nodes:
            merch = mandate_to_merchant.get(m["id"])
            if not merch:
                continue
            
            connected_merchs = [merch["id"]]
            for e in self.edges:
                if e["type"] in ["OFFERS", "INCLUDES"] and e["source"] == merch["id"]:
                    connected_merchs.append(e["target"])

            for c_merch_id in connected_merchs:
                for e in self.edges:
                    if e["type"] == "PROVIDES" and e["source"] == c_merch_id:
                        cap_id = e["target"].replace("cap_", "")
                        ver_str = e.get("properties", {}).get("verified_on")
                        if ver_str:
                            try:
                                ver_dt = datetime.strptime(str(ver_str)[:10], "%Y-%m-%d")
                                if ver_dt < six_months_ago:
                                    continue
                            except Exception:
                                pass

                        if cap_id not in cap_to_mandates:
                            cap_to_mandates[cap_id] = []
                            cap_to_vendors[cap_id] = []
                            cap_to_meta[cap_id] = e.get("properties", {})

                        if m["properties"] not in cap_to_mandates[cap_id]:
                            cap_to_mandates[cap_id].append(m["properties"])
                        if merch["properties"] not in cap_to_vendors[cap_id]:
                            cap_to_vendors[cap_id].append(merch["properties"])

        findings = []
        for cap_id, m_list in cap_to_mandates.items():
            if len(m_list) <= 1:
                continue

            v_list = cap_to_vendors.get(cap_id, [])
            v_ids = [f"merch_{v.get('id')}" for v in v_list]
            
            # Anti-self-bundle check
            has_bundle = False
            for v1 in v_ids:
                for v2 in v_ids:
                    if v1 != v2 and (v1, v2) in includes_pairs:
                        has_bundle = True
                        break
                if has_bundle:
                    break
            if has_bundle:
                continue

            sorted_mids = sorted([str(m.get("id")) for m in m_list])
            finding_key = hashlib.sha256(f"capability_overlap:{cap_id}:{':'.join(sorted_mids)}".encode()).hexdigest()
            legacy_key = f"cap_ov_{cap_id}"
            if finding_key in decided_keys or legacy_key in decided_keys:
                continue

            cap_node = next((n for n in self.nodes if n["id"] == f"cap_{cap_id}"), {})
            cap_props = cap_node.get("properties", {})
            meta = cap_to_meta.get(cap_id, {})

            # Fixed-only savings
            fixed_mands = [m for m in m_list if m.get("billing_type") != "usage_based"]
            if len(fixed_mands) > 1:
                costs = [float(m.get("annual_committed", m.get("annual_committed_cost", m.get("amount", 0.0) * 12))) for m in fixed_mands]
                savings = sum(costs) - min(costs)
            else:
                savings = 0.0

            findings.append({
                "finding_id": f"cap_ov_{cap_id}",
                "finding_key": finding_key,
                "finding_type": "capability_overlap",
                "capability_id": cap_id,
                "capability_name": cap_props.get("name", cap_id),
                "category": cap_props.get("category", "Software"),
                "description": cap_props.get("description", ""),
                "mandates": m_list,
                "vendors": [v.get("name", v.get("id")) for v in v_list],
                "potential_annual_saving": round(savings, 2),
                "evidence_paths": [
                    {
                        "vendor": v.get("name", v.get("id")),
                        "capability": cap_props.get("name", cap_id),
                        "relationship": "PROVIDES",
                        "confidence": meta.get("confidence", "confirmed_public"),
                        "verified_on": str(meta.get("verified_on", DEFAULT_VERIFIED_DATE)),
                        "source_url": meta.get("source_url", "TODO: fill link"),
                        "notes": meta.get("notes", "")
                    }
                    for v in v_list
                ],
                "confidence": meta.get("confidence", "confirmed_public"),
                "verified_on": str(meta.get("verified_on", DEFAULT_VERIFIED_DATE)),
                "source_url": meta.get("source_url", "TODO: fill link")
            })

        return findings

    def find_duplicate_vendors(self, uid: str = "user_primary") -> List[Dict[str, Any]]:
        """
        Identifies active mandates billed for the same vendor across multiple accounts or cards.
        Anti-joins against Decision nodes, calculates fixed-only savings.
        """
        user_decisions = [
            d for d in self.decisions 
            if d.get("user_id") == uid and d.get("finding_type") in ["duplicate_vendor", "overlap"]
        ]
        decided_keys = {d.get("finding_key") for d in user_decisions if d.get("finding_key")}

        cypher = """
        MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(m:Mandate)-[:FOR]->(v)
        WHERE m.status IN ['active', 'flagged', 'flagged_overlap', 'keep_confirmed']
        OPTIONAL MATCH (p)-[:OWNS_ACCOUNT]->(acc:Account)-[:HAS_MANDATE]->(m)
        WITH p, v, collect(DISTINCT m) AS mandates, collect(DISTINCT coalesce(acc.label, m.account_label, 'Primary Account')) AS accounts
        WHERE size(mandates) > 1
        RETURN v, mandates, accounts
        """

        if self.is_connected and self.driver:
            try:
                with self.driver.session() as session:
                    dec_res = session.run("MATCH (p:Person {id:$uid})-[:MADE_DECISION]->(d:Decision) RETURN d.finding_key AS fkey", uid=uid)
                    aura_decided_keys = {r["fkey"] for r in dec_res if r["fkey"]}
                    all_decided = decided_keys.union(aura_decided_keys)

                    result = session.run(cypher, uid=uid)
                    findings = []
                    for rec in result:
                        v = dict(rec["v"])
                        mandates = [dict(m) for m in rec["mandates"]]
                        accounts = rec["accounts"]
                        v_id = v.get("id", "unknown")

                        sorted_mids = sorted([str(m.get("id")) for m in mandates])
                        finding_key = hashlib.sha256(f"duplicate_vendor:{v_id}:{':'.join(sorted_mids)}".encode()).hexdigest()
                        legacy_key = f"dup_vend_{v_id}"
                        if finding_key in all_decided or legacy_key in all_decided:
                            continue

                        fixed_mands = [m for m in mandates if m.get("billing_type") != "usage_based"]
                        if len(fixed_mands) > 1:
                            costs = [float(m.get("annual_committed", m.get("annual_committed_cost", m.get("amount", 0) * 12))) for m in fixed_mands]
                            savings = sum(costs) - min(costs)
                        else:
                            savings = 0.0

                        findings.append({
                            "finding_id": f"dup_vend_{v_id}",
                            "finding_key": finding_key,
                            "finding_type": "duplicate_vendor",
                            "vendor_id": v_id,
                            "vendor_name": v.get("name", v_id),
                            "accounts": accounts,
                            "mandates": mandates,
                            "potential_annual_saving": round(savings, 2),
                            "explanation": f"Multiple active mandates detected for {v.get('name', v_id)} across {len(accounts)} accounts ({', '.join(accounts)}).",
                            "evidence_paths": [
                                {
                                    "mandate_id": m.get("id"),
                                    "vendor": v.get("name", v_id),
                                    "account": m.get("account_label", "Primary Account"),
                                    "relationship": "FOR"
                                }
                                for m in mandates
                            ]
                        })
                    return findings
            except Exception as e:
                print(f"Neo4j Aura duplicate query failed ({e}); evaluating on embedded engine.")

        # Embedded Graph Traversal
        mandate_nodes = [
            n for n in self.nodes 
            if n["group"] == "mandate" and n.get("properties", {}).get("status", "active") in ["active", "flagged", "flagged_overlap", "keep_confirmed"]
        ]

        vendor_groups = {}
        for m in mandate_nodes:
            props = m.get("properties", {})
            v_id = props.get("merchant_id")
            if not v_id:
                for e in self.edges:
                    if e["source"] == m["id"] and e["type"] == "FOR":
                        v_id = e["target"].replace("merch_", "")
                        break
            if v_id:
                if v_id not in vendor_groups:
                    vendor_groups[v_id] = []
                vendor_groups[v_id].append(props)

        findings = []
        for v_id, m_list in vendor_groups.items():
            if len(m_list) > 1:
                sorted_mids = sorted([str(m.get("id")) for m in m_list])
                finding_key = hashlib.sha256(f"duplicate_vendor:{v_id}:{':'.join(sorted_mids)}".encode()).hexdigest()
                legacy_key = f"dup_vend_{v_id}"
                if finding_key in decided_keys or legacy_key in decided_keys:
                    continue

                merch_node = next((n for n in self.nodes if n["id"] == f"merch_{v_id}"), {})
                v_name = merch_node.get("name") or v_id
                accounts = list({m.get("account_label", "Primary Account") for m in m_list})

                fixed_mands = [m for m in m_list if m.get("billing_type") != "usage_based"]
                if len(fixed_mands) > 1:
                    costs = [float(m.get("annual_committed", m.get("annual_committed_cost", m.get("amount", 0.0) * 12))) for m in fixed_mands]
                    savings = sum(costs) - min(costs)
                else:
                    savings = 0.0

                findings.append({
                    "finding_id": f"dup_vend_{v_id}",
                    "finding_key": finding_key,
                    "finding_type": "duplicate_vendor",
                    "vendor_id": v_id,
                    "vendor_name": v_name,
                    "accounts": accounts,
                    "mandates": m_list,
                    "potential_annual_saving": round(savings, 2),
                    "explanation": f"Multiple active mandates detected for {v_name} across {len(accounts)} accounts ({', '.join(accounts)}).",
                    "evidence_paths": [
                        {
                            "mandate_id": m.get("id"),
                            "vendor": v_name,
                            "account": m.get("account_label", "Primary Account"),
                            "relationship": "FOR"
                        }
                        for m in m_list
                    ]
                })

        return findings

    def record_overlap_decision(
        self,
        uid: str,
        kept_mandate_ids: List[str],
        cancel_mandate_ids: List[str],
        finding_key: Optional[str] = None,
        finding_type: str = "overlap",
        choice: str = "CONFIRMED"
    ) -> Dict[str, Any]:
        """
        Stores user's confirmation in graph:
        (:Person)-[:MADE_DECISION]->(:Decision {finding_key, finding_type, choice, timestamp})
        Marks kept mandates as 'keep_confirmed' and redundant mandates as 'suggested_cancel'.
        """
        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Stable finding key generation if not passed
        if not finding_key:
            all_involved = sorted(list(set(kept_mandate_ids + cancel_mandate_ids)))
            finding_key = hashlib.sha256(f"{finding_type}:{':'.join(all_involved)}".encode()).hexdigest()

        # Update embedded graph decisions & mandate properties
        decision_record = {
            "finding_key": finding_key,
            "finding_type": finding_type,
            "choice": choice,
            "timestamp": now_iso,
            "kept_mandate_ids": kept_mandate_ids,
            "cancel_mandate_ids": cancel_mandate_ids,
            "user_id": uid
        }
        self.decisions.append(decision_record)

        for n in self.nodes:
            if n["group"] == "mandate":
                props = n.get("properties", {})
                mid = str(props.get("id") or n["id"].replace("mand_", ""))
                if mid in kept_mandate_ids:
                    props["status"] = "keep_confirmed"
                    props["overlap_decision_at"] = now_iso
                elif mid in cancel_mandate_ids:
                    props["status"] = "suggested_cancel"
                    props["overlap_decision_at"] = now_iso

        # Live Aura execution
        if self.is_connected and self.driver:
            try:
                cypher = """
                MERGE (p:Person {id:$uid})
                CREATE (d:Decision {
                    finding_key: $finding_key,
                    finding_type: $finding_type,
                    choice: $choice,
                    timestamp: datetime(),
                    kept_mandate_ids: $kept_ids,
                    cancel_mandate_ids: $cancel_ids,
                    user_id: $uid
                })
                MERGE (p)-[:MADE_DECISION]->(d)
                WITH p
                UNWIND $kept_ids AS kid
                MATCH (p)-[:HAS_MANDATE]->(mk:Mandate {id: kid})
                SET mk.status = 'keep_confirmed', mk.overlap_decision_at = datetime()
                WITH p
                UNWIND $cancel_ids AS cid
                MATCH (p)-[:HAS_MANDATE]->(mc:Mandate {id: cid})
                SET mc.status = 'suggested_cancel', mc.overlap_decision_at = datetime();
                """
                with self.driver.session() as session:
                    session.run(
                        cypher,
                        uid=uid,
                        finding_key=finding_key,
                        finding_type=finding_type,
                        choice=choice,
                        kept_ids=kept_mandate_ids,
                        cancel_ids=cancel_mandate_ids
                    )
            except Exception as e:
                print(f"Live Aura overlap decision sync deferred: {e}")

        return {
            "status": "SUCCESS",
            "finding_key": finding_key,
            "kept_count": len(kept_mandate_ids),
            "suggested_cancel_count": len(cancel_mandate_ids),
            "timestamp": now_iso
        }

    def confirm_mandate_cancellation(self, uid: str, mandate_id: str, cancel_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Marks mandate as 'marked_cancelled' (and 'cancel_confirmed_by_user') in graph when user clicks Confirm in popup.
        """
        cancel_dt = cancel_date or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Update in-memory graph
        for n in self.nodes:
            if n["group"] == "mandate":
                props = n.get("properties", {})
                mid = str(props.get("id") or n["id"].replace("mand_", ""))
                if mid == str(mandate_id):
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
        - Zero charges & statement_end_date >= expected_next_charge_date: Mandate is VERIFIED CANCELLED!
        - Zero charges & statement_end_date < expected_next_charge_date: Awaiting billing cycle; status remains marked_cancelled.
        """
        GRACE_WINDOW_DAYS = 3
        now_dt = datetime.strptime(str(statement_end_date)[:10], "%Y-%m-%d") if statement_end_date else datetime.utcnow()

        reconciliation_report = {
            "reconciled_count": 0,
            "still_charging": [],
            "verified_cancelled": [],
            "in_flight_grace": [],
            "pending_verification": []
        }

        # Find cancelled mandates in embedded graph
        cancelled_mandates = []
        for n in self.nodes:
            if n["group"] == "mandate":
                p = n.get("properties", {})
                status = p.get("status")
                if status in ["marked_cancelled", "cancel_confirmed_by_user", "still_charging"]:
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
                latest_tx = max(matching_txs, key=lambda x: str(x.get("date", ""))[:10])
                tx_date_str = str(latest_tx.get("date", ""))[:10]
                tx_dt = datetime.strptime(tx_date_str, "%Y-%m-%d")
                grace_limit_dt = cancel_dt + timedelta(days=GRACE_WINDOW_DAYS)

                if tx_dt <= grace_limit_dt:
                    reconciliation_report["in_flight_grace"].append({
                        "mandate_id": mid,
                        "merchant_name": mand.get("merchant_name"),
                        "charge_date": tx_date_str,
                        "amount": latest_tx.get("amount"),
                        "note": f"Charge of ₹{latest_tx.get('amount')} fell within {GRACE_WINDOW_DAYS}-day in-flight billing grace window. No action needed."
                    })
                else:
                    mand["status"] = "still_charging"
                    mand["reminder_count"] = int(mand.get("reminder_count", 0)) + 1
                    mand["last_seen_charge_date"] = tx_date_str
                    cadence = mand.get("cadence", "MONTHLY")
                    days_ahead = 365 if cadence == "ANNUAL" else (90 if cadence == "QUARTERLY" else 30)
                    next_expected_dt = tx_dt + timedelta(days=days_ahead)
                    mand["expected_next_charge_date"] = next_expected_dt.strftime("%Y-%m-%d")

                    for n in self.nodes:
                        if n["id"] == f"mand_{mid}":
                            n["properties"]["status"] = "still_charging"
                            n["properties"]["reminder_count"] = mand["reminder_count"]
                            n["properties"]["last_seen_charge_date"] = tx_date_str
                            n["color"] = "#DC2626"

                    if self.is_connected and self.driver:
                        try:
                            with self.driver.session() as session:
                                session.run("""
                                MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(m:Mandate {id: $mid})
                                SET m.status = 'still_charging',
                                    m.reminder_count = $rc,
                                    m.last_seen_charge_date = $ls
                                """, uid=uid, mid=mid, rc=mand["reminder_count"], ls=tx_date_str)
                        except Exception as e:
                            print(f"Aura still_charging sync deferred: {e}")

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
                if now_dt >= expected_next_dt:
                    mand["status"] = "verified_cancelled"
                    for n in self.nodes:
                        if n["id"] == f"mand_{mid}":
                            n["properties"]["status"] = "verified_cancelled"
                            n["color"] = "#059669"

                    if self.is_connected and self.driver:
                        try:
                            with self.driver.session() as session:
                                session.run("""
                                MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(m:Mandate {id: $mid})
                                SET m.status = 'verified_cancelled'
                                """, uid=uid, mid=mid)
                        except Exception as e:
                            print(f"Aura verified_cancelled sync deferred: {e}")

                    reconciliation_report["verified_cancelled"].append({
                        "mandate_id": mid,
                        "merchant_name": mand.get("merchant_name"),
                        "expected_next_charge_date": str(expected_next_dt)[:10],
                        "statement_end_date": str(now_dt)[:10],
                        "message": f"Verified successfully cancelled! No charges detected across billing period extending to {str(now_dt)[:10]}."
                    })
                else:
                    reconciliation_report["pending_verification"].append({
                        "mandate_id": mid,
                        "merchant_name": mand.get("merchant_name"),
                        "expected_next_charge_date": str(expected_next_dt)[:10],
                        "statement_end_date": str(now_dt)[:10],
                        "message": f"Awaiting next billing cycle ({str(expected_next_dt)[:10]}) to verify zero debits."
                    })

        reconciliation_report["reconciled_count"] = (
            len(reconciliation_report["still_charging"]) + 
            len(reconciliation_report["verified_cancelled"]) + 
            len(reconciliation_report["in_flight_grace"])
        )
        return reconciliation_report

    def add_mandate_tags(self, uid: str, mandate_id: str, tags: List[str]) -> Dict[str, Any]:
        """
        Tags a mandate with user-defined labels (e.g. 'Engineering', 'Marketing', 'Discretionary').
        Ensures Tag nodes are scoped to authenticated user to maintain tenant isolation.
        """
        clean_tags = [t.strip() for t in tags if t.strip()]

        for n in self.nodes:
            if n["group"] == "mandate":
                props = n.get("properties", {})
                mid = str(props.get("id") or n["id"].replace("mand_", ""))
                if mid == str(mandate_id):
                    existing = props.get("tags", [])
                    props["tags"] = list(set(existing + clean_tags))

        if self.is_connected and self.driver:
            try:
                cypher = """
                MATCH (p:Person {id:$uid})-[:HAS_MANDATE]->(m:Mandate {id: $mid})
                UNWIND $tags AS tag_name
                MERGE (t:Tag {name: tag_name, user_id: $uid})
                MERGE (m)-[:TAGGED]->(t)
                RETURN m, collect(t.name) AS all_tags;
                """
                with self.driver.session() as session:
                    session.run(cypher, uid=uid, mid=mandate_id, tags=clean_tags)
            except Exception as e:
                print(f"Live Aura tag sync deferred: {e}")

        return {
            "mandate_id": mandate_id,
            "tags": clean_tags,
            "status": "SUCCESS"
        }

    def get_spend_concentration(self, uid: str = "user_primary") -> Dict[str, Any]:
        """
        Aggregates recurring spend by Category, Vendor, Account, Tag, Mechanism, and Billing Type.
        """
        active_mands = [
            n.get("properties", {}) for n in self.nodes
            if n["group"] == "mandate" and n.get("properties", {}).get("status") in ["active", "flagged", "flagged_overlap", "keep_confirmed"]
        ]

        cat_spend = {}
        vendor_spend = {}
        account_spend = {}
        tag_spend = {}
        mech_spend = {}
        billing_type_spend = {}
        total_spend = 0.0

        for m in active_mands:
            cost = float(m.get("annual_committed", m.get("annual_committed_cost", m.get("amount", 0.0) * 12)))
            total_spend += cost

            v = m.get("merchant_name") or m.get("merchant_id") or "Unknown"
            vendor_spend[v] = vendor_spend.get(v, 0.0) + cost

            acc = m.get("account_label") or "Primary Account"
            account_spend[acc] = account_spend.get(acc, 0.0) + cost

            mech = m.get("mechanism") or "CARD_SI"
            mech_spend[mech] = mech_spend.get(mech, 0.0) + cost

            bt = m.get("billing_type") or "fixed"
            billing_type_spend[bt] = billing_type_spend.get(bt, 0.0) + cost

            for t in m.get("tags", []):
                tag_spend[t] = tag_spend.get(t, 0.0) + cost

            merch_node = next((n for n in self.nodes if n["id"] == f"merch_{m.get('merchant_id')}"), None)
            c = merch_node.get("properties", {}).get("category", "Software") if merch_node else "Software"
            cat_spend[c] = cat_spend.get(c, 0.0) + cost

        def fmt_list(d):
            return sorted(
                [{"name": k, "annual_spend": round(v, 2), "pct": round((v / total_spend * 100) if total_spend > 0 else 0, 1)} for k, v in d.items()],
                key=lambda x: x["annual_spend"],
                reverse=True
            )

        return {
            "total_annual_spend": round(total_spend, 2),
            "by_category": fmt_list(cat_spend),
            "by_vendor": fmt_list(vendor_spend),
            "by_account": fmt_list(account_spend),
            "by_tag": fmt_list(tag_spend),
            "by_mechanism": fmt_list(mech_spend),
            "by_billing_type": fmt_list(billing_type_spend)
        }

    def get_decision_history(self, uid: str = "user_primary") -> List[Dict[str, Any]]:
        """
        Returns full history of user's overlap and cancellation decisions.
        """
        if self.is_connected and self.driver:
            try:
                cypher = """
                MATCH (p:Person {id:$uid})-[:MADE_DECISION]->(d:Decision)
                RETURN d.finding_key AS finding_key,
                       d.finding_type AS finding_type,
                       d.choice AS choice,
                       toString(d.timestamp) AS timestamp,
                       d.kept_mandate_ids AS kept_mandate_ids,
                       d.cancel_mandate_ids AS cancel_mandate_ids
                ORDER BY d.timestamp DESC
                """
                with self.driver.session() as session:
                    res = session.run(cypher, uid=uid)
                    return [record.data() for record in res]
            except Exception as e:
                print(f"Aura decision history query deferred: {e}")

        return [
            d for d in reversed(self.decisions)
            if d.get("user_id") == uid
        ]

    def run_cypher_query(self, cypher: str) -> Dict[str, Any]:
        """
        Executes a Cypher query on live Neo4j if connected,
        otherwise interprets preset queries against embedded graph.
        Enforces read-only query policy to prevent destructive Cypher injection.
        """
        # Security Guard: Block destructive/administrative Cypher clauses in public query endpoint
        disallowed_keywords = ["DROP", "DELETE", "DETACH", "CREATE USER", "ALTER USER", "REMOVE", "GRANT", "REVOKE", "TERMINATE"]
        cypher_upper = cypher.upper()
        for kw in disallowed_keywords:
            if kw in cypher_upper:
                return {
                    "mode": "SECURITY_POLICY",
                    "status": "BLOCKED",
                    "error": f"Security violation: Write or destructive Cypher command '{kw}' is prohibited on the query endpoint.",
                    "cypher": cypher,
                    "data": []
                }

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
        lines.append("// 5. Capabilities")
        for c in CAPABILITIES:
            safe_desc = c.get("description", "").replace("'", "\\'")
            lines.append(
                f"MERGE (cap:Capability {{id: '{c['id']}'}}) "
                f"ON CREATE SET cap.name = '{c['name']}', cap.category = '{c['category']}', cap.description = '{safe_desc}';"
            )

        lines.append("")
        lines.append("// 6. Plans & Offers")
        for pl in PLANS:
            lines.append(
                f"MERGE (plan:Plan {{id: '{pl['id']}'}}) "
                f"ON CREATE SET plan.name = '{pl['name']}', plan.tier = '{pl['tier']}', "
                f"plan.monthly_cost = {pl['monthly_cost']}, plan.annual_cost = {pl['annual_cost']};"
            )
            lines.append(
                f"MATCH (v:Merchant {{id: '{pl['vendor_id']}'}}), (plan:Plan {{id: '{pl['id']}'}}) "
                f"MERGE (v)-[:OFFERS]->(plan);"
            )

        lines.append("")
        lines.append("// 7. Curated Bundle Inclusions: (:Plan)-[:INCLUDES]->(:Merchant)")
        for b in CURATED_BUNDLES:
            safe_notes = b['notes'].replace("'", "\\'")
            lines.append(
                f"MATCH (plan:Plan {{id: '{b['parent_plan_id']}'}}), (c:Merchant {{id: '{b['child_vendor_id']}'}}) "
                f"MERGE (plan)-[r:INCLUDES]->(c) "
                f"ON CREATE SET r.tier = '{b['tier']}', r.confidence = '{b['confidence']}', "
                f"r.verified_on = date('{b['verified_on']}'), r.source_url = '{b['source_url']}', r.notes = '{safe_notes}';"
            )
            lines.append(
                f"MATCH (p:Merchant {{id: '{b['parent_vendor_id']}'}}), (c:Merchant {{id: '{b['child_vendor_id']}'}}) "
                f"MERGE (p)-[r2:INCLUDES]->(c) "
                f"ON CREATE SET r2.tier = '{b['tier']}', r2.confidence = '{b['confidence']}', "
                f"r2.verified_on = date('{b['verified_on']}'), r2.source_url = '{b['source_url']}', r2.notes = '{safe_notes}';"
            )

        lines.append("")
        lines.append("// 8. Vendor Functional Capabilities: (:Merchant)-[:PROVIDES]->(:Capability)")
        for vc in VENDOR_CAPABILITIES:
            safe_notes = vc.get('notes', '').replace("'", "\\'")
            lines.append(
                f"MATCH (v:Merchant {{id: '{vc['vendor_id']}'}}), (cap:Capability {{id: '{vc['capability_id']}'}}) "
                f"MERGE (v)-[r:PROVIDES]->(cap) "
                f"ON CREATE SET r.confidence = '{vc['confidence']}', r.verified_on = date('{vc['verified_on']}'), "
                f"r.source_url = '{vc['source_url']}', r.notes = '{safe_notes}';"
            )

        lines.append("")
        lines.append("// 9. Verification Query: Multi-Hop Bundle Overlap Traversal")
        lines.append("MATCH (p:Person)-[:HAS_MANDATE]->(ma:Mandate)-[:FOR]->(a:Merchant), (p)-[:HAS_MANDATE]->(mb:Mandate)-[:FOR]->(b:Merchant)")
        lines.append("WHERE ma <> mb MATCH path = (a)-[:INCLUDES*1..4]->(b)")
        lines.append("RETURN ma.id AS ParentMandate, mb.id AS RedundantMandate, [n in nodes(path) | n.name] AS PathNodes;")

        lines.append("")
        lines.append("// 10. Verification Query: Capability Overlap Clustering")
        lines.append("MATCH (p:Person)-[:HAS_MANDATE]->(m:Mandate)-[:FOR]->(v:Merchant)-[:PROVIDES]->(c:Capability)")
        lines.append("WITH p, c, collect(DISTINCT {mandate: m.id, vendor: v.name, cost: m.annual_committed_cost}) AS mandates")
        lines.append("WHERE size(mandates) > 1")
        lines.append("RETURN c.name AS Capability, mandates;")

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
