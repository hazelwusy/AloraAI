"""SAMHSA / findtreatment.gov source notes / process record.

NOT a runnable fetcher. findtreatment.gov's facility locator is a single-page
app with no public anonymous bulk export; a real pull requires registering for
API access at https://findtreatment.gov/api-request-form. That step was not
completed in this session (no credential to register with), so SAMHSA-tagged
records in data/facilities.json were populated from general knowledge of named
organizations known to serve SF/San Mateo/Alameda counties, then individually
re-verified against each org's own public site/contact page in a follow-up pass
(see data/facilities_collection_notes.md, "Post-collection verification pass").

## If re-attempting with API access
```bash
# once you have an API key from the request form above:
curl -H "Authorization: Bearer $SAMHSA_API_KEY" \
  "https://findtreatment.gov/api/v1/facilities?state=CA&county=San+Francisco"
```
Then filter results to behavioral-health-relevant `services` codes and map into
the facilities.json schema (see scripts/merge_facilities.py for the schema
this project uses).
"""
