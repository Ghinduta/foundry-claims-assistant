# Azure resources

Everything `infra/main.bicep` deploys into `rg-claims-assistant`, as of M2 (2026-10-12). The prices are approximate pay-as-you-go list prices; check the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/) for exact numbers. All of it is paid from the free trial credit, and `infra/down.ps1` deletes everything at the end of each session.

| Resource | Name | Region | Tier / version | Costs money? |
|---|---|---|---|---|
| Resource group | rg-claims-assistant | Sweden Central | n/a | No, it's just a folder |
| Foundry resource | claims-foundry-<suffix> | Sweden Central | AIServices S0 | No fixed cost; you pay only for model use (below) |
| Foundry project | claims-assistant | Sweden Central | n/a | No |
| Chat model deployment | gpt-5-mini | Sweden Central (GlobalStandard: requests may be processed in any region) | gpt-5-mini 2025-08-07, 50K TPM | **Per use:** ~$0.25 per 1M input tokens, ~$2 per 1M output tokens. Cents per session |
| Embedding model deployment | text-embedding-3-small | Sweden Central (GlobalStandard) | version 1, 50K TPM | **Per use:** ~$0.02 per 1M tokens. Indexing our 15 docs costs a fraction of a cent |
| Storage account | claimsst<suffix> | Sweden Central | StorageV2, Standard LRS | **Per GB:** ~$0.02 per GB per month; our few MB cost < $0.01 |
| AI Search | claims-search-<suffix> | **North Europe** | **Basic**, 1 replica, 1 partition; semantic ranker free plan (1,000 queries/month) | **Yes, by the hour: ~$0.10/hour (~$74/month if left on).** The only real cost, so run `down.ps1` after each session |
| Log Analytics workspace | claims-logs-<suffix> | Sweden Central | PerGB2018, 30-day retention | First 5 GB/month free, then ~$2.30+ per GB; we stay well under 5 GB |
| Application Insights | claims-appi-<suffix> | Sweden Central | Workspace-based | Billed through Log Analytics (above), so free for us |
| Role assignments (6) | n/a | n/a | n/a | No |

**In short:** AI Search Basic is the only resource billed by the hour (~$0.10/hour while it's up); everything else costs cents or nothing at our usage.
