"""
generate_mock.py
----------------
Generates all mock data for the Retail Loss Intelligence Platform.
Run once from the project root: python scripts/generate_mock.py

Output: data/ directory with all files needed by the application.
In a real deployment this layer is replaced by connectors to the
client's POS system, inventory management system, and incident
reporting platform. See README for full data schema documentation.
"""

import csv
import json
import os
import random
from datetime import datetime, timedelta

from faker import Faker

# ── Reproducibility ────────────────────────────────────────────────────────────
random.seed(42)
fake = Faker()
Faker.seed(42)

# ── Output paths ───────────────────────────────────────────────────────────────
BASE_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
CRIME_DIR = os.path.join(BASE_DIR, "crime_reports")

# ── Store constants ────────────────────────────────────────────────────────────
STORE_ID   = "store_001"
STORE_NAME = "TJX Retail — Downtown Location"

ALL_REGISTERS    = ["R01", "R02", "R03", "R04", "R05", "R06"]
ACTIVE_REGISTERS = ["R01", "R02", "R03"]

ASSOCIATE_IDS = [f"A{str(i).zfill(3)}" for i in range(1, 41)]

# ── Real shift names ───────────────────────────────────────────────────────────
# These match what appears on the actual store schedule
SHIFT_NAMES = [
    "womens",
    "mens_and_kids",
    "home",
    "returns",
    "jewelry",        # covers accessories, travel, purses; always has key
    "non_apparel",    # covers beauty, travel, accessories crossover; key depends on coordinator status
    "markdowns",      # floats entire store
    "fitting_room",
    "backroom",
]

# Which zones each shift covers
SHIFT_TO_ZONES = {
    "womens":       ["womens", "lingerie"],
    "mens_and_kids":["mens", "kids"],
    "home":         ["home"],
    "returns":      ["register"],
    "jewelry":      ["accessories", "travel", "purses", "beauty"],
    "non_apparel":  ["beauty", "travel", "accessories", "purses"],
    "markdowns":    ["womens","mens","kids","home","beauty","accessories","purses",
                     "lingerie","shoes","travel","tech_gifts"],
    "fitting_room": ["fitting_room"],
    "backroom":     ["backroom"],
}

# ── Coordinator definitions ────────────────────────────────────────────────────
# One coordinator per area. Permanent title on the associate profile.
# Beauty coordinator holds the master key for jewelry case + perfume case.
# Front end coordinator holds master keys that unlock all other coordinator keys.
COORDINATORS = {
    "A001": {
        "title":       "Beauty Coordinator",
        "shift":       "jewelry",          # typically scheduled jewelry shift
        "zones":       ["accessories","travel","purses","beauty","shoes","lingerie"],
        "key_access":  ["jewelry_case","perfume_case"],
    },
    "A002": {
        "title":       "Home Coordinator",
        "shift":       "home",
        "zones":       ["home"],
        "key_access":  [],
    },
    "A003": {
        "title":       "Mens & Kids Coordinator",
        "shift":       "mens_and_kids",
        "zones":       ["mens","kids"],
        "key_access":  [],
    },
    "A004": {
        "title":       "Womens Coordinator",
        "shift":       "womens",
        "zones":       ["womens","lingerie"],
        "key_access":  [],
    },
    "A005": {
        "title":       "Backroom Coordinator",
        "shift":       "backroom",
        "zones":       ["backroom"],
        "key_access":  [],
    },
    "A006": {
        "title":       "Front End Coordinator",
        "shift":       "returns",
        "zones":       ["register"],
        # Holds master keys — grants other coordinators access to their keys
        "key_access":  ["master_key","register_safe","returns_desk"],
    },
}

COORDINATOR_IDS = set(COORDINATORS.keys())

# ── Scenario anchors ───────────────────────────────────────────────────────────
SCENARIO_A_ASSOCIATE = "A012"   # part-time, 4 months, returns/register shift
SCENARIO_A_REGISTER  = "R02"

SCENARIO_B_ZONE  = "accessories"
SCENARIO_B_DATES = [
    datetime(2024, 3, 8),
    datetime(2024, 3, 22),
    datetime(2024, 4, 5),
    datetime(2024, 4, 19),
]
SCENARIO_B_SHIFT = "jewelry"    # organized group hits during jewelry shift window

PURSES_LOSS_DATE = datetime(2024, 5, 14)

# ── Department → Zone mapping ──────────────────────────────────────────────────
DEPT_TO_ZONE = {
    1:"womens",2:"womens",3:"womens",4:"womens",5:"womens",
    7:"womens",8:"womens",9:"womens",15:"womens",16:"womens",
    17:"womens",30:"womens",35:"womens",38:"womens",66:"womens",
    18:"accessories",19:"accessories",
    20:"mens",21:"mens",22:"mens",23:"mens",24:"mens",
    26:"mens",63:"mens",64:"mens",65:"mens",
    25:"shoes",27:"shoes",
    40:"kids",42:"kids",45:"kids",70:"kids",71:"kids",72:"kids",
    73:"beauty",87:"beauty",88:"beauty",89:"beauty",
    60:"home",61:"home",62:"home",67:"home",
    80:"home",81:"home",82:"home",83:"home",
    84:"home",85:"home",86:"home",
    74:"travel",
    50:"lingerie",53:"lingerie",55:"lingerie",
    59:"tech_gifts",
}

ZONE_DEPTS = {
    "womens":     [1,2,3,4,5,7,8,9,15,16,17,30,35,38,66],
    "accessories":[18,19],
    "mens":       [20,21,22,23,24,26,63,64,65],
    "shoes":      [25,27],
    "kids":       [40,42,45,70,71,72],
    "beauty":     [73,87,88,89],
    "home":       [60,61,62,67,80,81,82,83,84,85,86],
    "travel":     [74],
    "purses":     [19],
    "lingerie":   [50,53,55],
    "tech_gifts": [59],
    "register":   [],
    "backroom":   [],
    "fitting_room":[],
}

ZONE_WEIGHTS = {
    "accessories": 0.20,
    "beauty":      0.17,
    "kids":        0.15,
    "womens":      0.12,
    "mens":        0.10,
    "purses":      0.05,
    "lingerie":    0.05,
    "tech_gifts":  0.04,
    "register":    0.04,
    "shoes":       0.03,
    "home":        0.02,
    "travel":      0.01,
    "backroom":    0.01,
    "fitting_room":0.01,
}

ZONES       = list(ZONE_WEIGHTS.keys())
ZONE_W_LIST = [ZONE_WEIGHTS[z] for z in ZONES]

# ── Date helpers ───────────────────────────────────────────────────────────────
START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 12, 31)

def random_date(start=START_DATE, end=END_DATE):
    return start + timedelta(days=random.randint(0, (end - start).days))

def random_time():
    return f"{random.randint(9,21):02d}:{random.randint(0,59):02d}"

def fmt_date(dt):
    return dt.strftime("%Y-%m-%d")

# LP officers who file incident reports
LP_ASSOCIATES = list(COORDINATOR_IDS)   # coordinators file most LP reports


# ── 1. Employees ───────────────────────────────────────────────────────────────
def generate_employees():
    rows = []

    for aid in ASSOCIATE_IDS:
        is_coordinator  = aid in COORDINATOR_IDS
        is_scenario_a   = aid == SCENARIO_A_ASSOCIATE

        # ── Coordinators ──
        # Only permanent attributes — scheduling lives in a separate platform
        if is_coordinator:
            coord         = COORDINATORS[aid]
            emp_type      = "full_time"
            tenure        = random.randint(24, 96)
            hire_date     = (datetime(2024, 1, 1) - timedelta(days=tenure*30)).strftime("%Y-%m-%d")
            title         = coord["title"]
            key_access    = "|".join(coord["key_access"]) if coord["key_access"] else ""
            perf          = round(random.uniform(3.8, 5.0), 1)
            is_coord_flag = True

        # ── Scenario A associate ──
        elif is_scenario_a:
            emp_type      = "part_time"
            tenure        = 4
            hire_date     = (datetime(2024, 1, 1) - timedelta(days=4*30)).strftime("%Y-%m-%d")
            title         = "Sales Associate"
            key_access    = ""
            perf          = round(random.uniform(2.8, 3.2), 1)
            is_coord_flag = False

        # ── Regular associates ──
        else:
            emp_type      = "part_time" if random.random() < 0.95 else "full_time"
            tenure        = random.randint(1, 96)
            hire_date     = (datetime(2024, 1, 1) - timedelta(days=tenure*30)).strftime("%Y-%m-%d")
            title         = "Sales Associate"
            key_access    = ""
            perf          = round(random.uniform(3.0, 5.0), 1)
            is_coord_flag = False

        rows.append({
            "associate_id":       aid,
            "hire_date":          hire_date,
            "tenure_months":      tenure,
            "employment_type":    emp_type,
            "title":              title,
            "is_coordinator":     is_coord_flag,
            "key_access":         key_access,
            "performance_rating": perf,
            "termination_date":   "",
            "termination_reason": "",
        })

    path = os.path.join(BASE_DIR, "employees.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ employees.csv ({len(rows)} associates, 6 coordinators)")


# ── 2. POS Transactions ────────────────────────────────────────────────────────
def generate_pos_transactions():
    """
    ~95,000 transactions across 365 days.

    Scenario A pattern:
      A012 on R02 performs suspicious no-sale → void sequences.
      A no-sale (drawer open, no transaction) followed within 1-2 mins
      by a void on the same login is the flag — suggests drawer opened
      to remove cash then sale voided to cover it.
      Also has elevated standalone voids at 3x store average.
    """
    rows             = []
    tx_id            = 1
    daily_avg        = round(95_000 / 365)
    BASELINE_VOID    = 0.015
    SCENARIO_A_VOID  = 0.045

    current = START_DATE
    while current <= END_DATE:
        is_weekend  = current.weekday() >= 5
        day_volume  = int(daily_avg * (1.3 if is_weekend else 1.0))
        day_volume += random.randint(-30, 30)

        for _ in range(day_volume):
            register  = (random.choice(ALL_REGISTERS)
                         if is_weekend and random.random() < 0.25
                         else random.choice(ACTIVE_REGISTERS))
            associate = random.choice(ASSOCIATE_IDS)
            is_a_tx   = (associate == SCENARIO_A_ASSOCIATE
                         and register == SCENARIO_A_REGISTER)
            void_rate = SCENARIO_A_VOID if is_a_tx else BASELINE_VOID

            r = random.random()
            if r < void_rate:
                tx_type = "void"
                amount  = round(random.uniform(8.99, 89.99), 2)
            elif r < void_rate + 0.03:
                tx_type = "refund"
                amount  = round(random.uniform(5.99, 149.99), 2)
            elif r < void_rate + 0.035:
                # Scenario A: no_sale followed immediately by void sequence
                if is_a_tx and random.random() < 0.4:
                    # Insert no_sale row
                    t_hour   = random.randint(10, 19)
                    t_minute = random.randint(0, 57)
                    rows.append({
                        "transaction_id":   f"TX{tx_id:07d}",
                        "date":             fmt_date(current),
                        "time":             f"{t_hour:02d}:{t_minute:02d}",
                        "register_id":      register,
                        "associate_id":     associate,
                        "transaction_type": "no_sale",
                        "amount":           0.00,
                        "department":       0,
                        "zone":             "register",
                        "payment_method":   "",
                        "sequence_flag":    "no_sale_before_void",
                    })
                    tx_id += 1
                    # Void 1-2 minutes later same login
                    rows.append({
                        "transaction_id":   f"TX{tx_id:07d}",
                        "date":             fmt_date(current),
                        "time":             f"{t_hour:02d}:{t_minute+random.randint(1,2):02d}",
                        "register_id":      register,
                        "associate_id":     associate,
                        "transaction_type": "void",
                        "amount":           round(random.uniform(8.99, 59.99), 2),
                        "department":       0,
                        "zone":             "register",
                        "payment_method":   "cash",
                        "sequence_flag":    "void_after_no_sale",
                    })
                    tx_id += 1
                    continue
                tx_type = "no_sale"
                amount  = 0.00
            else:
                tx_type = "sale"
                amount  = round(random.uniform(3.99, 299.99), 2)

            dept = random.choice(list(DEPT_TO_ZONE.keys()))
            rows.append({
                "transaction_id":   f"TX{tx_id:07d}",
                "date":             fmt_date(current),
                "time":             random_time(),
                "register_id":      register,
                "associate_id":     associate,
                "transaction_type": tx_type,
                "amount":           amount,
                "department":       dept,
                "zone":             DEPT_TO_ZONE.get(dept, "unknown"),
                "payment_method":   random.choice(["cash","credit","debit","gift_card", "store_credit"]),
                "sequence_flag":    "",
            })
            tx_id += 1

        current += timedelta(days=1)

    path = os.path.join(BASE_DIR, "pos_transactions.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ pos_transactions.csv ({len(rows):,} transactions)")


# ── 3. Cash Control ────────────────────────────────────────────────────────────
def generate_cash_control():
    """
    Records end-of-day cash variance per register. No associate ID —
    multiple associates touch a register in a day.
    Investigation flow: find the short register → query POS transactions
    for that register/date → identify which associate logins show anomalous
    void or no-sale patterns → cross-reference with employee records.
    """
    rows    = []
    current = START_DATE
    while current <= END_DATE:
        for reg in ACTIVE_REGISTERS:
            expected = round(random.uniform(800, 2400), 2)
            # Scenario A: R02 shows consistent shorts because A012
            # is logging in on R02 and running no-sale/void sequences
            if reg == SCENARIO_A_REGISTER:
                variance = round(random.uniform(-35, -15), 2)
            else:
                variance = round(random.uniform(-5, 5), 2)
            rows.append({
                "date":          fmt_date(current),
                "register_id":   reg,
                "expected_cash": expected,
                "actual_cash":   round(expected + variance, 2),
                "variance":      variance,
                "note":          "Short — review POS logins for this register/date" if variance < -20 else "",
            })
        current += timedelta(days=1)

    path = os.path.join(BASE_DIR, "cash_control.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ cash_control.csv ({len(rows):,} shift records)")


# ── 4. Shrinkage / Stock Audits ────────────────────────────────────────────────
def generate_shrinkage():
    rows             = []
    scenario_b_months = {d.month for d in SCENARIO_B_DATES}

    for month in range(1, 13):
        audit_date = datetime(2024, month, random.randint(20, 28))
        for zone, depts in ZONE_DEPTS.items():
            if zone in ("register", "backroom", "fitting_room"):
                continue
            expected = random.randint(80, 400)

            if zone == "accessories" and month in scenario_b_months:
                variance = random.randint(-14, -8)
            elif zone == "purses" and month == PURSES_LOSS_DATE.month:
                variance = random.randint(-3, -1)
            else:
                variance = random.randint(-4, 1)

            actual = max(0, expected + variance)
            rows.append({
                "audit_date":        fmt_date(audit_date),
                "month":             month,
                "zone":              zone,
                "departments":       "|".join(str(d) for d in depts),
                "expected_quantity": expected,
                "actual_quantity":   actual,
                "variance":          actual - expected,
                "audit_type":        "cycle",
            })

    # Full annual audit
    for zone in ZONE_DEPTS:
        if zone in ("register", "backroom", "fitting_room"):
            continue
        expected = random.randint(500, 1200)
        actual   = expected + random.randint(-6, 1)
        rows.append({
            "audit_date":        "2024-12-28",
            "month":             12,
            "zone":              zone,
            "departments":       "|".join(str(d) for d in ZONE_DEPTS[zone]),
            "expected_quantity": expected,
            "actual_quantity":   actual,
            "variance":          actual - expected,
            "audit_type":        "full_annual",
        })

    path = os.path.join(BASE_DIR, "shrinkage.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ shrinkage.csv ({len(rows)} audit records)")


# ── 5. Incident Reports ────────────────────────────────────────────────────────
INCIDENT_TEMPLATES = {
    "accessories": [
        "Subject observed selecting multiple {items} from the accessories wall near dept {dept}. Placed items inside personal bag while facing away from camera. Exited through main entrance without purchasing.",
        "Noticed subject spending extended time at jewelry counter dept {dept}. Upon floor check found {items} missing from display. No transaction on record.",
        "Subject selected {items} from accessories display. Concealed in waistband area near fitting room entrance. Proceeded to exit without making payment.",
        "Two subjects distracted associate at accessories counter dept {dept} while third individual removed {items} from unlocked display case.",
    ],
    "beauty": [
        "Subject concealed {items} from beauty dept {dept} inside jacket pocket while browsing fragrance section. Exited without purchase.",
        "Observed subject switching price tags on {items} in dept {dept}. Purchased at lower price. Reviewed by LP after associate flagged transaction.",
        "Multiple {items} missing from beauty end-cap dept {dept} after subject spent approx 4 mins in aisle. No transaction found.",
        "Subject removed security wrap from {items} in beauty aisle dept {dept}. Abandoned wrap behind display. Item not recovered.",
    ],
    "kids": [
        "Subject placed {items} from childrens dept {dept} into stroller basket underneath child. Proceeded to exit without purchasing.",
        "Observed juvenile remove {items} from kids dept {dept} and conceal in backpack. Parent present but unaware. Both exited without purchase.",
        "Group of three entered kids section dept {dept}. Two acted as lookout while third concealed {items} in oversized shopping bag.",
        "Subject removed tags from {items} in infant section dept {dept}. Dressed child in unpurchased item. Exited through main entrance.",
    ],
    "womens": [
        "Subject took {items} from womens dept {dept} into fitting room. Returned with fewer items than taken in. One item unaccounted for.",
        "Observed subject layering {items} from dept {dept} under own clothing in fitting room area. Exited without purchasing.",
        "Subject selected high-value {items} from dept {dept}. Removed security tag using unknown tool near rear of store. Exited main entrance.",
    ],
    "mens": [
        "Subject removed {items} from mens dept {dept}. Placed in unmarked bag brought into store. Exited through main entrance.",
        "Associate reported {items} missing from mens outerwear dept {dept} after subject tried on multiple coats and left only one.",
        "Observed subject cut security tag from {items} in dept {dept} using scissors. Concealed item and exited.",
    ],
    "purses": [
        "Alarm activated on handbag display dept {dept}. Subject attempted to remove security tag from {items}. Subject fled before apprehension.",
        "High-value {items} missing from locked display dept {dept}. No transaction found. Camera review pending. Associate states display was found unlocked during floor check.",
    ],
    "register": [
        "Customer reported receiving incorrect change at register. Reviewed transaction log. Discrepancy noted on associate login.",
        "Associate performed no-sale on register then voided prior transaction within two minutes. Cash drawer variance noted end of shift.",
        "Refund processed without receipt. Cash returned to customer. Associate login flagged for review.",
    ],
    "backroom": [
        "Shipment discrepancy noted during receiving. Vendor invoice shows {dept} units. Physical count shows fewer. Backroom coordinator notified.",
        "Associate observed removing {items} from receiving area without scan. Not logged in system. Under review.",
    ],
    "default": [
        "Subject observed acting suspiciously in dept {dept} area. Floor associate notified LP. Subject left store before approach.",
        "Merchandise {items} found discarded in dept {dept} without tags. Believed to be related to concealment activity.",
    ],
}

ITEMS_BY_ZONE = {
    "accessories": ["sunglasses","scarves","belts","hair accessories","jewelry set","watch","earrings"],
    "beauty":      ["perfume","skincare set","makeup palette","hair treatment","nail kit","fragrance"],
    "kids":        ["childrens outfit","toy set","infant clothing","kids shoes","backpack","books"],
    "womens":      ["blouse","dress","coat","activewear set","cardigan","jeans"],
    "mens":        ["dress shirt","outerwear jacket","polo","trousers","suit jacket"],
    "purses":      ["designer handbag","leather tote","crossbody bag","clutch"],
    "register":    ["misc merchandise","gift card","bagged items"],
    "backroom":    ["shipment units","receiving stock","tagged merchandise"],
    "default":     ["merchandise","items","clothing"],
}

OUTCOMES = [
    "Subject exited store. No apprehension. Incident documented.",
    "Subject apprehended at exit. Police notified. Report filed.",
    "Subject returned merchandise upon LP approach. No further action.",
    "Subject fled before approach. Description recorded for future reference.",
    "Under investigation. Camera footage requested.",
    "No further action. Insufficient evidence.",
]

ZONE_ALIASES = {
    "accessories": ["accessories","accessories wall","accessories area","accessories/jewelry","acc wall"],
    "beauty":      ["beauty","beauty dept","beauty section","beauty/fragrance","beauty aisle"],
    "kids":        ["kids","childrens","kids section","children's dept","infant section"],
    "womens":      ["womens","womens floor","womens section","ladies dept","womens clothing"],
    "mens":        ["mens","mens dept","menswear","mens section","mens floor"],
    "purses":      ["purses","handbags","purse wall","bag display","purses/handbags"],
    "register":    ["register","checkout","POS","front register","checkout lane", "cashier"],
    "lingerie":    ["lingerie","intimates","lingerie section", "pajamas"],
    "home":        ["home","home dept","home goods","housewares"],
    "shoes":       ["shoes","footwear","shoe dept","shoe section"],
    "travel":      ["travel","luggage","travel dept"],
    "tech_gifts":  ["tech","gifts","mens accessories","tech/gifts"],
    "backroom":    ["backroom","stockroom","receiving","back of store"],
    "fitting_room":["fitting room","dressing room","fitting rooms"],
}

def zone_alias(zone):
    return random.choice(ZONE_ALIASES.get(zone, [zone]))

def build_description(zone, dept_num):
    templates = INCIDENT_TEMPLATES.get(zone, INCIDENT_TEMPLATES["default"])
    items     = random.choice(ITEMS_BY_ZONE.get(zone, ITEMS_BY_ZONE["default"]))
    return random.choice(templates).format(items=items, dept=dept_num)

def generate_incidents():
    rows = []

    # ── Background incidents ──
    BACKGROUND_COUNT = 61
    for i in range(BACKGROUND_COUNT):
        zone     = random.choices(ZONES, weights=ZONE_W_LIST)[0]
        depts    = ZONE_DEPTS.get(zone, [0])
        dept_num = random.choice(depts) if depts else 0
        date     = random_date()
        # Determine which shift would be working this zone
        zone_shifts = [s for s, zs in SHIFT_TO_ZONES.items() if zone in zs]
        shift = random.choice(zone_shifts) if zone_shifts else random.choice(SHIFT_NAMES)

        rows.append({
            "report_id":    f"INC{str(i+1).zfill(4)}",
            "date":         fmt_date(date),
            "time":         random_time(),
            "zone":         zone,
            "zone_alias":   zone_alias(zone),
            "department":   dept_num,
            "shift":        shift,
            "lp_associate": random.choice(LP_ASSOCIATES),
            "incident_type":random.choice(["concealment","tag_removal","refund_abuse","distraction","other"]),
            "description":  build_description(zone, dept_num),
            "outcome":      random.choice(OUTCOMES),
        })

    # ── Scenario B: 4 hits, accessories zone, jewelry shift window ──
    # Filed by DIFFERENT LP associates — why the pattern isn't caught manually
    scenario_b_lp = random.sample(LP_ASSOCIATES, 4)
    scenario_b_descriptions = [
        "Two subjects entered accessories area. One engaged associate with questions about dept 19 items while second subject concealed multiple scarves and jewelry in tote bag. Both subjects exited through main entrance quickly. Description: both wearing dark clothing, one with large shoulder bag.",
        "Subject spent approx 6 mins at acc wall near dept 18. Selected several items and placed directly into personal shopping bag without browsing further. Exited main entrance without purchasing. Wearing grey hoodie, black jeans.",
        "Observed group of two near accessories/jewelry dept 19. Classic distraction technique — one asked associate to retrieve item from case while second removed items from open display. Exited rapidly toward main entrance. Similar MO to recent area incidents per local crime report.",
        "Subject concealed items from accessories area dept 18-19 in reusable shopping bag. Moved quickly through womens section toward main entrance. Did not stop at register. Dark jacket, baseball cap. Second individual waited near entrance.",
    ]

    for i, (b_date, lp, desc) in enumerate(zip(SCENARIO_B_DATES, scenario_b_lp, scenario_b_descriptions)):
        rows.append({
            "report_id":    f"INC{str(BACKGROUND_COUNT + i + 1).zfill(4)}",
            "date":         fmt_date(b_date),
            "time":         f"{random.randint(14,18):02d}:{random.randint(0,59):02d}",
            "zone":         "accessories",
            "zone_alias":   zone_alias("accessories"),
            "department":   random.choice([18,19]),
            "shift":        SCENARIO_B_SHIFT,
            "lp_associate": lp,
            "incident_type":"concealment",
            "description":  desc,
            "outcome":      random.choice([
                "Subjects exited before apprehension. Descriptions recorded.",
                "Subjects fled through main entrance. Police report filed.",
                "Under review. Camera footage requested for time window.",
            ]),
        })

    # ── Purses single event ──
    rows.append({
        "report_id":    f"INC{str(BACKGROUND_COUNT + 5 + 1).zfill(4)}",
        "date":         fmt_date(PURSES_LOSS_DATE),
        "time":         "15:22",
        "zone":         "purses",
        "zone_alias":   "handbags",
        "department":   19,
        "shift":        "jewelry",
        "lp_associate": random.choice(LP_ASSOCIATES),
        "incident_type":"alarm_activation",
        "description":  "Alarm activated on designer handbag display dept 19. Subject attempted to remove security tag from high-value item. Subject fled toward main entrance before LP arrival. Item recovered but damaged. Display found unlocked — unclear how access was obtained. Beauty coordinator scheduled jewelry shift. Key access log under review.",
        "outcome":      "Subject fled. Item recovered. Access method under investigation. Camera review pending.",
    })

    random.shuffle(rows)
    for idx, row in enumerate(rows):
        row["report_id"] = f"INC{str(idx+1).zfill(4)}"

    path = os.path.join(BASE_DIR, "incidents.jsonl")
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print(f"  ✓ incidents.jsonl ({len(rows)} reports)")


# ── 6. Fitting Room Audits ─────────────────────────────────────────────────────
def generate_fitting_room_audits():
    rows = []
    audit_events = [
        {"audit_id":"FRA001","audit_date":"2024-04-15","observer_id":"A004"},  # Womens coordinator
        {"audit_id":"FRA002","audit_date":"2024-10-08","observer_id":"A004"},
    ]

    for event in audit_events:
        for window in range(1, 5):
            hour_start = random.randint(10, 17)
            items_in   = random.randint(4, 8)

            if event["audit_id"] == "FRA002":
                items_out  = items_in - random.randint(1, 2)
                associate  = "A022"
                shift      = "fitting_room"
                notes = random.choice([
                    "Associate did not verbally count items on entry.",
                    "Items in count not confirmed with customer verbally.",
                    "Associate occupied with other customer during room entry.",
                    "Count discrepancy noted. Associate did not recount on exit.",
                ])
            else:
                items_out  = items_in - random.randint(0, 1)
                associate  = random.choice(ASSOCIATE_IDS)
                shift      = "fitting_room"
                notes = random.choice([
                    "No issues observed.",
                    "Standard procedure followed.",
                    "Associate counted items correctly.",
                    "Minor delay in count — corrected.",
                ])

            rows.append({
                "audit_id":          event["audit_id"],
                "audit_date":        event["audit_date"],
                "observer_id":       event["observer_id"],
                "time_window_start": f"{hour_start:02d}:00",
                "time_window_end":   f"{hour_start+1:02d}:00",
                "items_in":          items_in,
                "items_out":         items_out,
                "variance":          items_out - items_in,
                "associate_on_duty": associate,
                "shift":             shift,
                "notes":             notes,
            })

    path = os.path.join(BASE_DIR, "fitting_room_audits.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ fitting_room_audits.csv ({len(rows)} audit windows)")


# ── 7. Crime Reports ───────────────────────────────────────────────────────────
CRIME_REPORTS = {
    "q1_crime_report.txt": """
QUARTERLY CRIME SUMMARY — Q1 2024
Local Police Department — Retail District
Prepared: April 2, 2024

OVERVIEW
Retail theft incidents in the district increased 8% compared to Q1 2023.
Organized retail crime (ORC) groups remain the primary driver of high-value losses.
Small accessories, cosmetics, and fragrance items continue to be primary targets
due to high resale value and ease of concealment.

NOTABLE PATTERNS
- Several reports of two-person distraction teams operating in accessories and
  jewelry departments across multiple retailers in the district.
- Incidents typically occur during mid-afternoon to early evening shifts,
  consistent with jewelry and non-apparel shift coverage hours.
- Subjects described as wearing dark, concealing clothing with large personal bags.

RECOMMENDATIONS
Retailers are advised to review staffing levels in high-value departments during
peak afternoon hours. Coordinated surveillance across neighboring stores recommended
for pattern identification. Ensure locked display cases are checked at shift start.
""",
    "q2_crime_report.txt": """
QUARTERLY CRIME SUMMARY — Q2 2024
Local Police Department — Retail District
Prepared: July 5, 2024

OVERVIEW
Q2 saw a continuation of organized retail crime activity from Q1.
Three arrests made in April related to a known ORC group targeting
accessories and beauty departments across the district.

NOTABLE PATTERNS
- Same MO reported across 6 retailers: distraction technique at accessories
  counters, rapid exit toward main entrance, use of reusable shopping bags
  for concealment.
- One high-value handbag theft reported at a district retailer in May.
  Security tag removal attempted. Display case found unlocked. Subject fled.
- Gift card fraud uptick — fraudulent returns exchanged for gift cards
  across multiple stores. Returns desk associates flagged for review.
- Internal register discrepancies reported at two district retailers.
  No-sale followed by void sequences identified in POS exception reports.

CASE UPDATES
Two individuals from Q1 ORC group identified. Active investigation ongoing.
Retailers with incidents in March-April requested to submit camera footage.
""",
    "q3_crime_report.txt": """
QUARTERLY CRIME SUMMARY — Q3 2024
Local Police Department — Retail District
Prepared: October 1, 2024

OVERVIEW
Retail crime activity stabilized in Q3 following Q2 arrests.
Back-to-school period (August) saw elevated activity in children's clothing
and accessories departments district-wide.

NOTABLE PATTERNS
- Kids and childrens departments reported highest incident frequency during
  August, consistent with seasonal back-to-school theft patterns.
- Beauty and fragrance departments continue to see concealment activity,
  particularly in stores with open-floor fragrance displays.
- Internal theft investigations ongoing at two district retailers.
  Cash register discrepancies flagged by LP teams. No-sale abuse pattern
  identified at one location during returns shift hours.

RECOMMENDATIONS
Year-end holiday season preparation advised. Historically Q4 brings
30-40% increase in external theft incidents. Review staffing and key
access protocols before November. Ensure jewelry coordinator coverage
is not left to non-coordinator associates during peak hours.
""",
}

def generate_crime_reports():
    os.makedirs(CRIME_DIR, exist_ok=True)
    for filename, content in CRIME_REPORTS.items():
        with open(os.path.join(CRIME_DIR, filename), "w") as f:
            f.write(content.strip())
    print(f"  ✓ crime_reports/ ({len(CRIME_REPORTS)} quarterly reports)")


# ── 8. Store Profile ───────────────────────────────────────────────────────────
def generate_store_profile():
    profile = {
        "store_id":   STORE_ID,
        "name":       STORE_NAME,
        "type":       "street",
        "size_sqft":  28000,
        "floors":     1,
        "entrances":  ["main_entrance"],
        "registers":  {
            "total":            6,
            "typically_active": 3,
            "ids":              ALL_REGISTERS,
            "active_ids":       ACTIVE_REGISTERS,
            "access_note":      "Associates sign in with associate ID. No-sale button opens drawer. No physical register key. Front end coordinator oversees register access.",
        },
        "key_access_chain": {
            "note":             "Front end coordinator holds master keys. All coordinator keys are obtained through front end coordinator.",
            "front_end_coord":  "A006",
            "beauty_coord":     "A001",
            "locked_cases":     ["jewelry_case","perfume_case"],
            "key_rules": {
                "jewelry_shift_present":     "Beauty coordinator always has key.",
                "no_jewelry_non_apparel_present": "Non-apparel associate takes jewelry shift and has key.",
                "both_present_coord":        "Non-apparel coordinator also gets key.",
                "both_present_non_coord":    "Non-apparel associate does NOT get key.",
            },
        },
        "shift_definitions": SHIFT_TO_ZONES,
        "layout_notes":      "Main entrance slightly left of center. Register and queue immediately inside entrance. Travel and purses to the left. Accessories and beauty slightly down on the left. Womens clothing center. Mens and kids far right. Backroom between home and kids at rear.",
        "zones": {
            "accessories":  {"risk_level":"high",   "departments":[18,19],                      "near_entrance":True,  "shift":"jewelry"},
            "beauty":       {"risk_level":"high",   "departments":[73,87,88,89],                "near_entrance":True,  "shift":"non_apparel", "locked_case":"perfume_case"},
            "kids":         {"risk_level":"high",   "departments":[40,42,45,70,71,72],          "near_entrance":False, "shift":"mens_and_kids"},
            "womens":       {"risk_level":"medium", "departments":[1,2,3,4,5,7,8,9,15,16,17,30,35,38,66],"near_entrance":False,"shift":"womens"},
            "mens":         {"risk_level":"medium", "departments":[20,21,22,23,24,26,63,64,65], "near_entrance":False, "shift":"mens_and_kids"},
            "purses":       {"risk_level":"medium", "departments":[19],                         "near_entrance":True,  "shift":"jewelry", "security":"alarmed_displays","locked_case":"jewelry_case"},
            "lingerie":     {"risk_level":"medium", "departments":[50,53,55],                   "near_entrance":False, "shift":"womens"},
            "tech_gifts":   {"risk_level":"medium", "departments":[59],                         "near_entrance":False, "shift":"mens_and_kids"},
            "register":     {"risk_level":"medium", "departments":[],                           "near_entrance":True,  "shift":"returns"},
            "shoes":        {"risk_level":"low",    "departments":[25,27],                      "near_entrance":False, "shift":"jewelry"},
            "home":         {"risk_level":"low",    "departments":[60,61,62,67,80,81,82,83,84,85,86],"near_entrance":False,"shift":"home"},
            "travel":       {"risk_level":"low",    "departments":[74],                         "near_entrance":True,  "shift":"jewelry"},
            "backroom":     {"risk_level":"low",    "departments":[],                           "near_entrance":False, "shift":"backroom","notes":"Between home and kids at rear. Separate physical space."},
            "fitting_room": {"risk_level":"medium", "departments":[],                           "near_entrance":False, "shift":"fitting_room","notes":"Single fitting room. Monitored via twice-yearly camera audit."},
        },
        "coordinators":     COORDINATORS,
        "lp_notes":         "Street location. Elevated ORC activity in accessories/beauty Q1-Q2. Back-to-school elevates kids risk. Key access chain through front end coordinator is critical investigative context for locked-case incidents.",
        "fitting_rooms":    {"count":1,"monitoring":"periodic_camera_audit","audit_frequency":"twice_yearly"},
    }

    path = os.path.join(BASE_DIR, "store_profile.json")
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"  ✓ store_profile.json")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(BASE_DIR,  exist_ok=True)
    os.makedirs(CRIME_DIR, exist_ok=True)

    print(f"\nGenerating mock data for: {STORE_NAME}")
    print(f"Output directory: {os.path.abspath(BASE_DIR)}\n")

    generate_employees()
    generate_pos_transactions()
    generate_cash_control()
    generate_shrinkage()
    generate_incidents()
    generate_fitting_room_audits()
    generate_crime_reports()
    generate_store_profile()

    print(f"\n✓ All data files generated successfully.")
    print(f"  Run this script once. Commit the data/ folder.")
    print(f"  The application reads from data/ — never calls this script.\n")

if __name__ == "__main__":
    main()