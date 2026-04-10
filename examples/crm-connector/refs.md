# CRM Connector – References

## Field Mapping

| Lumina Field | Salesforce | HubSpot | Zoho |
|-------------|------------|---------|------|
| customer_name | Account.Name | company.name | Accounts.Account_Name |
| contact_email | Contact.Email | contact.email | Contacts.Email |
| deal_value | Opportunity.Amount | deal.amount | Deals.Amount |
| deal_stage | Opportunity.StageName | deal.dealstage | Deals.Stage |

## API Rate Limits

- Salesforce: 100 requests/15 min
- HubSpot: 100 requests/10 sec
- Zoho: 100 requests/min
