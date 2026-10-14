using System.Collections.Concurrent;

namespace ClaimsAssistant;

public enum CallbackStatus
{
    Pending,
    Approved,
    Rejected,
}

/// <summary>A customer's request to be called back, waiting for a claims handler's decision.</summary>
public record CallbackRequest(
    Guid Id,
    string ClaimantId,
    string CustomerName,
    string Reason,
    string PreferredTime,
    DateTimeOffset RequestedAt,
    CallbackStatus Status = CallbackStatus.Pending,
    DateTimeOffset? DecidedAt = null);

/// <summary>The approval queue. In memory, so it empties when the app restarts.</summary>
public sealed class CallbackQueue
{
    private readonly ConcurrentDictionary<Guid, CallbackRequest> requests = new();

    public CallbackRequest Add(string claimantId, string customerName, string reason, string preferredTime)
    {
        var request = new CallbackRequest(Guid.NewGuid(), claimantId, customerName, reason, preferredTime,
            DateTimeOffset.UtcNow);
        requests[request.Id] = request;
        return request;
    }

    public IReadOnlyList<CallbackRequest> All() => requests.Values.OrderByDescending(r => r.RequestedAt).ToList();

    public IReadOnlyList<CallbackRequest> ForClaimant(string claimantId) =>
        All().Where(request => request.ClaimantId == claimantId).ToList();

    /// <summary>Approves or rejects a pending request.</summary>
    /// <returns>The decided request, or null if it doesn't exist or was already decided.</returns>
    public CallbackRequest? Decide(Guid id, bool approve)
    {
        while (requests.TryGetValue(id, out var request) && request.Status == CallbackStatus.Pending)
        {
            var decided = request with
            {
                Status = approve ? CallbackStatus.Approved : CallbackStatus.Rejected,
                DecidedAt = DateTimeOffset.UtcNow,
            };
            if (requests.TryUpdate(id, decided, request))
            {
                return decided;
            }
        }
        return null;
    }

    public bool Exists(Guid id) => requests.ContainsKey(id);
}
