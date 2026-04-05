# Research Methodology Improvements

Items identified during the Platform Foundation conversations that should be addressed when refactoring the research and detection logic. These are implementation improvements, not foundation-level decisions.

---

## Lab Platform Detection

### Product-level compete query is incomplete
**File:** `backend/researcher.py` line 431
**Issue:** The product-level query only searches for CloudShare, Instruqt, and Appsembler. Missing: Skytap, Kyndryl, GoDeploy, Vocareum, ReadyTech, Immersive Labs, Hack The Box, TryHackMe, ACI Learning, DIY signals, and all Skillable domains.
**Fix:** Align the product-level compete query with the full company-level competitor list.

### Discovery prompt doesn't extract Skillable as a lab partner
**File:** `backend/prompts/discovery.txt` line 98
**Issue:** The `existing_lab_partner` extraction instructions list competitors (CloudShare, Instruqt, Skytap, Appsembler, DIY) but do not include Skillable, labondemand.com, or learnondemandsystems.com as values to extract. Even though Phase 1 research queries look for Skillable signals, the structured extraction in Phase 2 may not capture it in the right field.
**Fix:** Add Skillable (and legacy brand signals) to the `existing_lab_partner` extraction instructions.

### Domain-based detection for stronger evidence
**Concept:** When researching a company, look for outbound links from the company's own properties (website, support docs, training pages) that point to lab platform domains — labondemand.com, learnondemandsystems.com, instruqt.com, cloudshare.com, etc. An actual URL link is stronger evidence than a name mention.
**Status:** Not currently implemented. Explore feasibility during refactor.

---

## Single Canonical Lab Platform List

### One list, referenced everywhere
**Issue:** The company-level and product-level research queries maintain separate, inconsistent lists of competitors. The company-level query has the full set; the product-level query has only three. This guarantees drift.
**Principle:** One canonical list of all lab platform providers (Skillable + all competitors + DIY), maintained in a single location (likely constants.py or a config file), referenced by both company-level and product-level research queries, by the discovery extraction prompt, and by the badging framework. When a new competitor is identified, add it once, and it propagates everywhere.
**Applies to GP4 (Self-Evident Design) and GP5 (Intelligence compounds).**

---

## LMS / LXP Detection

### Surface the specific LMS platform name
**Current:** The badging framework has a generic "LMS / LXP" badge.
**Improvement:** Badge should display the specific platform name (Docebo, Cornerstone, Moodle, etc.) — same variable-driven principle as lab platform badges. Docebo and Cornerstone are Skillable partners and should be green.
