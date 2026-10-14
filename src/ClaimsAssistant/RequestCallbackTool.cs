using System.Text.Json;

namespace ClaimsAssistant;

/// <summary>Runs the agent's request_callback function tool: queues the request for a claims handler.</summary>
public sealed class RequestCallbackTool(CallbackQueue queue)
{
    public const string NAME = "request_callback";

    /// <summary>Queues a callback for the signed-in customer. Nobody is called until a handler approves it.</summary>
    /// <param name="arguments">The model's JSON arguments: only the reason and preferred time are taken from it.</param>
    public string Run(Customer customer, string arguments)
    {
        using var json = JsonDocument.Parse(arguments);
        var request = queue.Add(customer.ClaimantId, customer.Name,
            json.RootElement.GetProperty("reason").GetString()!,
            json.RootElement.GetProperty("preferred_time").GetString()!);
        return JsonSerializer.Serialize(new { status = "waiting_for_handler_approval", request_id = request.Id });
    }
}
