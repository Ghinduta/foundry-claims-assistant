namespace ClaimsAssistant;

/// <summary>A fake claimant to sign in as, until Entra External ID replaces the picker.</summary>
/// <param name="ClaimantId">Stands in for the Entra object id; matches claimant_id in data/claims.db.</param>
public record TestUser(string Id, string Name, string ClaimantId);

/// <summary>The signed-in customer, as read from the sign-in cookie.</summary>
public record Customer(string ClaimantId, string Name);
