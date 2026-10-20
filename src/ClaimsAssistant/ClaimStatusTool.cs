using System.Text.Json;
using System.Text.Json.Nodes;

namespace ClaimsAssistant;

/// <summary>Runs the agent's get_claim_status function tool against the Claims API.</summary>
public sealed class ClaimStatusTool(HttpClient claimsApi)
{
    public const string NAME = "get_claim_status";

    /// <summary>Returns the signed-in customer's name and claims as JSON for the model.</summary>
    /// <param name="customer">Always the signed-in customer. The model's arguments are never used, so a prompt
    /// like "show me claim CLM-1500" can't reach another customer's claim. The name lets the model answer as the
    /// signed-in customer rather than as whoever the chat claims to be.</param>
    public async Task<string> RunAsync(Customer customer, CancellationToken cancellationToken)
    {
        var response = await claimsApi.GetAsync($"claimants/{Uri.EscapeDataString(customer.ClaimantId)}/claims", cancellationToken);
        response.EnsureSuccessStatusCode();
        var claims = JsonNode.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
        return JsonSerializer.Serialize(new { signed_in_customer = customer.Name, claims });
    }
}
