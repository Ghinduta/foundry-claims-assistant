using System.Text.Json;
using System.Text.RegularExpressions;
using Azure.AI.Extensions.OpenAI;
using Azure.AI.Projects;
using OpenAI.Responses;

#pragma warning disable OPENAI001 // the Responses API types are marked experimental in the OpenAI SDK

namespace ClaimsAssistant;

/// <summary>The agent's answer, with citation markers removed and the cited documents listed.</summary>
public record ChatReply(string Answer, IReadOnlyList<string> Sources);

/// <summary>Talks to the Foundry agent and runs the function tools it asks for.</summary>
public sealed partial class AgentChat(AIProjectClient project, ClaimStatusTool claimStatus,
    RequestCallbackTool requestCallback, CallbackStatusTool callbackStatus, IConfiguration configuration)
{
    private const int MAX_TOOL_ROUNDS = 5;

    private readonly string agentName = configuration["Foundry:AgentName"]!;

    /// <summary>Creates a Foundry conversation, which keeps the history so each turn sends only the new message.</summary>
    public async Task<string> StartConversationAsync(CancellationToken cancellationToken)
    {
        ProjectConversation conversation = await project.ProjectOpenAIClient.GetProjectConversationsClient()
            .CreateProjectConversationAsync(cancellationToken: cancellationToken);
        return conversation.Id;
    }

    public async Task<ChatReply> AskAsync(string conversationId, string message, Customer customer,
        CancellationToken cancellationToken)
    {
        ProjectResponsesClient responses = project.ProjectOpenAIClient.GetProjectResponsesClientForAgent(agentName);
        List<ResponseItem> input = [ResponseItem.CreateUserMessageItem(message)];
        for (var round = 0; round <= MAX_TOOL_ROUNDS; round++)
        {
            CreateResponseOptions options = new() { AgentConversationId = conversationId };
            foreach (var item in input)
            {
                options.InputItems.Add(item);
            }
            ResponseResult response = await responses.CreateResponseAsync(options, cancellationToken);

            // A function tool doesn't run in Foundry: the response stops at the call, and we send back its output.
            var calls = response.OutputItems.OfType<FunctionCallResponseItem>().ToList();
            if (calls.Count == 0)
            {
                return ToReply(response);
            }
            input = [];
            foreach (var call in calls)
            {
                var output = call.FunctionName switch
                {
                    ClaimStatusTool.NAME => await claimStatus.RunAsync(customer, cancellationToken),
                    RequestCallbackTool.NAME => requestCallback.Run(customer, call.FunctionArguments.ToString()),
                    CallbackStatusTool.NAME => callbackStatus.Run(customer),
                    _ => JsonSerializer.Serialize(new { error = "UNKNOWN_TOOL" }),
                };
                input.Add(ResponseItem.CreateFunctionCallOutputItem(call.CallId, output));
            }
        }
        throw new InvalidOperationException($"The agent asked for tools more than {MAX_TOOL_ROUNDS} times in one turn.");
    }

    private static ChatReply ToReply(ResponseResult response)
    {
        var sources = response.OutputItems.OfType<MessageResponseItem>()
            .SelectMany(message => message.Content)
            .SelectMany(part => part.OutputTextAnnotations)
            .OfType<UriCitationMessageAnnotation>()
            .Select(citation => citation.Title)
            .Distinct()
            .ToList();
        return new ChatReply(CitationMarker().Replace(response.GetOutputText(), "").Trim(), sources);
    }

    /// <summary>Markers like 【4:0†source】 that the search tool puts in the text where a passage is used.</summary>
    [GeneratedRegex(@"\s?【[^】]*】")]
    private static partial Regex CitationMarker();
}
