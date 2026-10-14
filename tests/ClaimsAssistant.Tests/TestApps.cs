using ClaimsApi;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;

namespace ClaimsAssistant.Tests;

/// <summary>The assistant app wired to an in-memory Claims API. The agent itself is the real one in Foundry.</summary>
public sealed class TestApps : IDisposable
{
    private readonly WebApplicationFactory<ClaimStatus> claimsApi = new();

    public TestApps()
    {
        Assistant = new WebApplicationFactory<AgentChat>().WithWebHostBuilder(host => host.ConfigureTestServices(services =>
            services.AddHttpClient<ClaimStatusTool>(client => client.BaseAddress = claimsApi.Server.BaseAddress)
                .ConfigurePrimaryHttpMessageHandler(() => claimsApi.Server.CreateHandler())));
    }

    public WebApplicationFactory<AgentChat> Assistant { get; }

    /// <summary>A browser-like client signed in as the test customer <paramref name="testUserId"/>.</summary>
    public async Task<HttpClient> SignInAsync(string testUserId)
    {
        var client = Assistant.CreateClient();
        (await client.PostAsync($"/api/sign-in/{testUserId}", null)).EnsureSuccessStatusCode();
        return client;
    }

    public void Dispose()
    {
        Assistant.Dispose();
        claimsApi.Dispose();
    }
}
