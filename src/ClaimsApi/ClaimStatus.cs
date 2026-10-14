namespace ClaimsApi;

/// <summary>The fields of a claim the insurer allows the assistant to see.</summary>
/// <param name="MissingDocuments">Document codes the claim still waits for, as in data/scripts/catalog.py.</param>
public record ClaimStatus(
    string ClaimId,
    string Status,
    string Phase,
    string[] MissingDocuments,
    string LastUpdated,
    string IncidentType,
    string IncidentDate,
    string Vehicle,
    int Deductible,
    int TotalClaimAmount);
