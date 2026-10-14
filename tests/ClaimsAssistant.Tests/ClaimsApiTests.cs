using System.Text.Json;
using ClaimsApi;
using Microsoft.AspNetCore.Mvc.Testing;

namespace ClaimsAssistant.Tests;

public class ClaimsApiTests(WebApplicationFactory<ClaimStatus> claimsApi) : IClassFixture<WebApplicationFactory<ClaimStatus>>
{
    private const string MARIA = "815ef6d1-3b8f-4a18-b7f8-a88b17fc695a";

    [Fact]
    public async Task Returns_only_the_approved_fields()
    {
        var json = await claimsApi.CreateClient().GetStringAsync($"/claimants/{MARIA}/claims");

        var claim = JsonDocument.Parse(json).RootElement.EnumerateArray().Single();
        var fields = claim.EnumerateObject().Select(field => field.Name).Order();
        Assert.Equal(
            ["claimId", "deductible", "incidentDate", "incidentType", "lastUpdated", "missingDocuments", "phase",
             "status", "totalClaimAmount", "vehicle"],
            fields);
        Assert.Equal("CLM-1003", claim.GetProperty("claimId").GetString());
    }

    [Fact]
    public async Task Unknown_claimant_gets_no_claims()
    {
        var json = await claimsApi.CreateClient().GetStringAsync("/claimants/not-a-claimant/claims");

        Assert.Equal("[]", json);
    }
}
