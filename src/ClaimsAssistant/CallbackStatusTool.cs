using System.Text.Json;

namespace ClaimsAssistant;

/// <summary>Runs the agent's get_callback_status function tool: the signed-in customer's callbacks as they are now.</summary>
public sealed class CallbackStatusTool(CallbackQueue queue)
{
    public const string NAME = "get_callback_status";

    /// <summary>Returns the callback requests of <paramref name="customer"/>, newest first, as JSON for the model.</summary>
    public string Run(Customer customer) => JsonSerializer.Serialize(new
    {
        callbacks = queue.ForClaimant(customer.ClaimantId).Select(request => new
        {
            reason = request.Reason,
            preferred_time = request.PreferredTime,
            requested_at = request.RequestedAt,
            status = request.Status.ToString().ToLowerInvariant(),
            decided_at = request.DecidedAt,
        }),
    });
}
