import os
import sys
import pytest
 
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from search import search
 
 
 
def test_jewelry_case_incidents():
    results = search("incidents where jewelry was taken out of case", index_name="incidents", k=5)
    top = results[0]
    assert top["metadata"]["zone"] in ("accessories", "purses")
 
 
def test_purse_alarm_incidents():
    results = search("incidents of purse alarm going off", index_name="incidents", k=5)
    top = results[0]
    assert (
        top["metadata"]["zone"] == "purses" or
        top["metadata"]["incident_type"] == "alarm_activation"
    )
 
 
def test_visible_merchandise_stolen():
    results = search(
        "incidents of people walking out of the store with visible merchandise being stolen",
        index_name="incidents", k=5
    )
    top = results[0]
    assert any(
        word in top["text"].lower()
        for word in ("exit", "exited", "entrance", "fled", "main entrance")
    )
 
 
def test_beauty_concealment():
    results = search("incidents where beauty items were seen to be concealed", index_name="incidents", k=5)
    top = results[0]
    assert top["metadata"]["zone"] == "beauty"
 
 
def test_large_bags():
    results = search("incidents where customers seen with large bags filled", index_name="incidents", k=5)
    top = results[0]
    assert any(
        word in top["text"].lower()
        for word in ("bag", "tote", "shopping bag", "reusable", "personal bag")
    )
 
 
def test_security_sticker_removal():
    results = search("incidents where customer seen removing security stickers", index_name="incidents", k=5)
    top = results[0]
    assert any(
        word in top["text"].lower()
        for word in ("security", "tag", "wrap", "sticker", "removed")
    )
 
 
def test_clothing_tag_removal():
    results = search("incidents where customer seen removing clothing security tag", index_name="incidents", k=5)
    top = results[0]
    assert (
        top["metadata"]["incident_type"] == "tag_removal" or
        "tag" in top["text"].lower()
    )
 
 
def test_wearing_clothing_out():
    results = search("incident where customer seen wearing and leaving with clothing", index_name="incidents", k=5)
    top = results[0]
    assert any(
        word in top["text"].lower()
        for word in ("wearing", "layering", "dressed", "under own clothing")
    )
 
 
def test_childrens_clothing_concealment():
    results = search("incident where customer seen concealing childrens clothing in bag", index_name="incidents", k=5)
    top = results[0]
    assert top["metadata"]["zone"] == "kids"
 
 
def test_associate_concealment_suspicion():
    results = search("incident where associate has been suspected of concealing items", index_name="incidents", k=5)
    top = results[0]
    assert (
        top["metadata"]["zone"] == "backroom" or
        "associate" in top["text"].lower()
    )
 
 
 
def test_orc_activity_in_crime_reports():
    results = search("organized retail crime targeting accessories", index_name="crime", k=3)
    top = results[0]
    assert any(
        word in top["text"].lower()
        for word in ("organized", "orc", "accessories", "distraction")
    )
 
 
def test_internal_theft_in_crime_reports():
    results = search("internal theft register discrepancies", index_name="crime", k=3)
    top = results[0]
    assert any(
        word in top["text"].lower()
        for word in ("internal", "register", "discrepan", "cash")
    )