using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace ClaimsAssistant.Tests;

public class CallbackQueueTests
{
    [Fact]
    public void A_request_is_decided_only_once()
    {
        var queue = new CallbackQueue();
        var request = queue.Add("claimant", "Maria Lopez", "Missing police report", "any time");

        Assert.Equal(CallbackStatus.Approved, queue.Decide(request.Id, approve: true)!.Status);
        Assert.Null(queue.Decide(request.Id, approve: false));
    }
}

public class HandlerAccessTests : IDisposable
{
    private readonly TestApps apps = new();

    [Fact]
    public async Task A_customer_cannot_see_or_approve_the_queue()
    {
        var maria = await apps.SignInAsync("maria");

        Assert.Equal(HttpStatusCode.Unauthorized, (await maria.GetAsync("/api/handler/callbacks")).StatusCode);
        Assert.Equal(HttpStatusCode.Unauthorized,
            (await maria.PostAsync($"/api/handler/callbacks/{Guid.NewGuid()}/approve", null)).StatusCode);
    }

    public void Dispose() => apps.Dispose();
}

/// <summary>The whole loop with the real agent: ask, wait for the handler, approve. Needs the Azure resources up.</summary>
[Trait("Category", "Live")]
public class CallbackFlowTests : IDisposable
{
    private static readonly JsonSerializerOptions JSON = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() },
    };

    private readonly TestApps apps = new();

    [Fact]
    public async Task A_callback_waits_for_the_handler()
    {
        var maria = await apps.SignInAsync("maria");

        var reply = await maria.PostAsJsonAsync("/api/chat",
            new { message = "Please ask someone to call me back tomorrow morning about my missing police report." });
        reply.EnsureSuccessStatusCode();

        var waiting = Assert.Single((await maria.GetFromJsonAsync<CallbackRequest[]>("/api/callbacks", JSON))!);
        Assert.Equal(CallbackStatus.Pending, waiting.Status);

        // The handler signs in with their own cookie in the same browser and approves.
        (await maria.PostAsync("/api/handler/sign-in", null)).EnsureSuccessStatusCode();
        (await maria.PostAsync($"/api/handler/callbacks/{waiting.Id}/approve", null)).EnsureSuccessStatusCode();

        var decided = Assert.Single((await maria.GetFromJsonAsync<CallbackRequest[]>("/api/callbacks", JSON))!);
        Assert.Equal(CallbackStatus.Approved, decided.Status);
    }

    public void Dispose() => apps.Dispose();
}
