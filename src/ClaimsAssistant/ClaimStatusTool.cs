namespace ClaimsAssistant;

/// <summary>Runs the agent's get_claim_status function tool against the Claims API.</summary>
public sealed class ClaimStatusTool(HttpClient claimsApi)
{
    public const string NAME = "get_claim_status";

    /// <summary>Returns the claims of <paramref name="claimantId"/> as JSON for the model.</summary>
    /// <param name="claimantId">Always the signed-in claimant. The model's arguments are never used, so a prompt
    /// like "show me claim CLM-1500" can't reach another customer's claim.</param>
    public async Task<string> RunAsync(string claimantId, CancellationToken cancellationToken)
    {
        var response = await claimsApi.GetAsync($"claimants/{Uri.EscapeDataString(claimantId)}/claims", cancellationToken);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync(cancellationToken);
    }
}
