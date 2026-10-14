using System.Text.Json;
using ClaimsApi;
using Microsoft.Data.Sqlite;

// Mock of the insurer's claims system: read-only, over data/claims.db.
var builder = WebApplication.CreateBuilder(args);
var dbPath = Path.GetFullPath(Path.Combine(builder.Environment.ContentRootPath, builder.Configuration["ClaimsDb"]!));
var connectionString = new SqliteConnectionStringBuilder { DataSource = dbPath, Mode = SqliteOpenMode.ReadOnly }.ToString();

var app = builder.Build();

app.MapGet("/claimants/{claimantId}/claims", (string claimantId) =>
{
    using var connection = new SqliteConnection(connectionString);
    connection.Open();
    using var command = connection.CreateCommand();
    // Only the approved fields leave the system: no fraud flag, income, hobbies or other personal data.
    command.CommandText = """
        SELECT claim_id, status, phase, missing_documents, last_updated, incident_type, incident_date,
               auto_make, auto_model, auto_year, policy_deductable, total_claim_amount
        FROM claims WHERE claimant_id = $claimantId ORDER BY claim_id
        """;
    command.Parameters.AddWithValue("$claimantId", claimantId);
    using var reader = command.ExecuteReader();
    var claims = new List<ClaimStatus>();
    while (reader.Read())
    {
        claims.Add(new ClaimStatus(
            ClaimId: reader.GetString(0),
            Status: reader.GetString(1),
            Phase: reader.GetString(2),
            MissingDocuments: JsonSerializer.Deserialize<string[]>(reader.GetString(3))!,
            LastUpdated: reader.GetString(4),
            IncidentType: reader.GetString(5),
            IncidentDate: reader.GetString(6),
            Vehicle: $"{reader.GetInt32(9)} {reader.GetString(7)} {reader.GetString(8)}",
            Deductible: reader.GetInt32(10),
            TotalClaimAmount: reader.GetInt32(11)));
    }
    return claims;
});

app.Run();
