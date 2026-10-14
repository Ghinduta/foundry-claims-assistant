using System.ClientModel;
using System.Security.Claims;
using System.Text.Json.Serialization;
using Azure.AI.Projects;
using Azure.Identity;
using ClaimsAssistant;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;

const string CLAIMANT_ID = "claimant_id";
const string CONVERSATION_ID = "conversation_id";
const string CONTENT_FILTERED = "CONTENT_FILTERED";
const string CALLBACK_NOT_FOUND = "CALLBACK_NOT_FOUND";
const string CALLBACK_ALREADY_DECIDED = "CALLBACK_ALREADY_DECIDED";
// Customers and claims handlers sign in with separate cookies, so one browser can test both sides at once.
const string CUSTOMER = "customer";
const string HANDLER = "handler";

var builder = WebApplication.CreateBuilder(args);

void UseApiCookie(CookieAuthenticationOptions options, string name)
{
    options.Cookie.Name = name;
    options.Cookie.SameSite = SameSiteMode.Strict;
    options.Events.OnRedirectToLogin = context =>
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        return Task.CompletedTask;
    };
    options.Events.OnRedirectToAccessDenied = context =>
    {
        context.Response.StatusCode = StatusCodes.Status403Forbidden;
        return Task.CompletedTask;
    };
}

builder.Services.AddAuthentication(CUSTOMER)
    .AddCookie(CUSTOMER, options => UseApiCookie(options, "claims.customer"))
    .AddCookie(HANDLER, options => UseApiCookie(options, "claims.handler"));
builder.Services.AddAuthorizationBuilder()
    .AddPolicy(CUSTOMER, policy => policy.AddAuthenticationSchemes(CUSTOMER).RequireClaim(CLAIMANT_ID))
    .AddPolicy(HANDLER, policy => policy.AddAuthenticationSchemes(HANDLER).RequireRole(HANDLER));
builder.Services.AddDistributedMemoryCache();
builder.Services.AddSession(options => options.Cookie.SameSite = SameSiteMode.Strict);
builder.Services.ConfigureHttpJsonOptions(options => options.SerializerOptions.Converters.Add(new JsonStringEnumConverter()));

// Your az login locally, the app's managed identity in Azure. It needs only to run the agent, not to change it.
// The tenant is set explicitly because an AZURE_TENANT_ID on the machine would override it. Visual Studio is
// skipped: it may be signed in to another tenant, and a failed sign-in there stops the chain.
builder.Services.AddSingleton(new AIProjectClient(
    new Uri(builder.Configuration["Foundry:ProjectEndpoint"]!),
    new DefaultAzureCredential(new DefaultAzureCredentialOptions
    {
        TenantId = builder.Configuration["Foundry:TenantId"],
        ExcludeVisualStudioCredential = true,
    })));
builder.Services.AddHttpClient<ClaimStatusTool>(client =>
    client.BaseAddress = new Uri(builder.Configuration["ClaimsApi:BaseUrl"]!));
builder.Services.AddSingleton<CallbackQueue>();
builder.Services.AddSingleton<RequestCallbackTool>();
builder.Services.AddScoped<AgentChat>();

var testUsers = builder.Configuration.GetSection("TestUsers").Get<TestUser[]>()!;
var testHandlerName = builder.Configuration["TestHandlerName"]!;

var app = builder.Build();

app.UseDefaultFiles();
app.UseStaticFiles();
app.UseAuthentication();
app.UseAuthorization();
app.UseSession();

// ---------- Customer

app.MapGet("/api/test-users", () => testUsers.Select(user => new { user.Id, user.Name }));

app.MapPost("/api/sign-in/{testUserId}", async (string testUserId, HttpContext context) =>
{
    var user = testUsers.FirstOrDefault(user => user.Id == testUserId);
    if (user is null)
    {
        return Results.NotFound();
    }
    context.Session.Clear();
    var identity = new ClaimsIdentity(
        [new Claim(ClaimTypes.Name, user.Name), new Claim(CLAIMANT_ID, user.ClaimantId)], CUSTOMER);
    await context.SignInAsync(CUSTOMER, new ClaimsPrincipal(identity));
    return Results.Ok(new { user.Name });
});

app.MapPost("/api/sign-out", async (HttpContext context) =>
{
    context.Session.Clear();
    await context.SignOutAsync(CUSTOMER);
    return Results.NoContent();
});

app.MapGet("/api/me", (ClaimsPrincipal user) => new { Name = user.Identity!.Name }).RequireAuthorization(CUSTOMER);

app.MapPost("/api/chat", async (ChatRequest request, ClaimsPrincipal user, HttpContext context, AgentChat chat,
    CancellationToken cancellationToken) =>
{
    var conversationId = context.Session.GetString(CONVERSATION_ID);
    if (conversationId is null)
    {
        conversationId = await chat.StartConversationAsync(cancellationToken);
        context.Session.SetString(CONVERSATION_ID, conversationId);
    }
    // The customer comes from the sign-in cookie, never from the request or the model.
    var customer = new Customer(user.FindFirstValue(CLAIMANT_ID)!, user.Identity!.Name!);
    try
    {
        return Results.Ok(await chat.AskAsync(conversationId, request.Message, customer, cancellationToken));
    }
    catch (ClientResultException e) when (e.Status == StatusCodes.Status400BadRequest && e.Message.Contains("content_filter"))
    {
        // Foundry's guardrails (content filters, Prompt Shields) rejected the message or the answer.
        return Results.BadRequest(new { error = CONTENT_FILTERED });
    }
}).RequireAuthorization(CUSTOMER);

app.MapGet("/api/callbacks", (ClaimsPrincipal user, CallbackQueue queue) =>
    queue.ForClaimant(user.FindFirstValue(CLAIMANT_ID)!).Select(request =>
        new { request.Id, request.Reason, request.PreferredTime, request.RequestedAt, request.Status }))
    .RequireAuthorization(CUSTOMER);

// ---------- Claims handler: approves or rejects the callbacks the agent asked for.

app.MapPost("/api/handler/sign-in", async (HttpContext context) =>
{
    var identity = new ClaimsIdentity(
        [new Claim(ClaimTypes.Name, testHandlerName), new Claim(ClaimTypes.Role, HANDLER)], HANDLER);
    await context.SignInAsync(HANDLER, new ClaimsPrincipal(identity));
    return Results.Ok(new { Name = testHandlerName });
});

app.MapPost("/api/handler/sign-out", async (HttpContext context) =>
{
    await context.SignOutAsync(HANDLER);
    return Results.NoContent();
});

app.MapGet("/api/handler/me", (ClaimsPrincipal user) => new { Name = user.Identity!.Name }).RequireAuthorization(HANDLER);

app.MapGet("/api/handler/callbacks", (CallbackQueue queue) => queue.All()).RequireAuthorization(HANDLER);

app.MapPost("/api/handler/callbacks/{id:guid}/{decision:regex(^(approve|reject)$)}",
    (Guid id, string decision, CallbackQueue queue) =>
    {
        if (!queue.Exists(id))
        {
            return Results.NotFound(new { error = CALLBACK_NOT_FOUND });
        }
        var decided = queue.Decide(id, approve: decision == "approve");
        return decided is null ? Results.Conflict(new { error = CALLBACK_ALREADY_DECIDED }) : Results.Ok(decided);
    }).RequireAuthorization(HANDLER);

app.Run();

record ChatRequest(string Message);
