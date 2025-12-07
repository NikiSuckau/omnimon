using OmnipetModuleEditor.Models;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;

namespace OmnipetModuleEditor.docgenerators
{
    internal class QuestEventGenerator
    {
        public static void GenerateQuestEventPage(string docPath, string modulePath)
        {
            string template = GeneratorUtils.GetTemplateContent("questevents.html");
            
            var quests = LoadQuests(modulePath);
            var events = LoadEvents(modulePath);

            var questsContent = GenerateQuestsTable(quests);
            var eventsContent = GenerateEventsTable(events);

            string content = template
                .Replace("#QUESTSDATA", questsContent)
                .Replace("#EVENTSDATA", eventsContent);

            File.WriteAllText(Path.Combine(docPath, "questevents.html"), content);
        }

        private static List<Quest> LoadQuests(string modulePath)
        {
            if (string.IsNullOrEmpty(modulePath))
                return new List<Quest>();

            string questPath = Path.Combine(modulePath, "quests.json");
            if (!File.Exists(questPath))
                return new List<Quest>();

            try
            {
                string json = File.ReadAllText(questPath);
                using (JsonDocument doc = JsonDocument.Parse(json))
                {
                    var root = doc.RootElement;
                    if (root.TryGetProperty("quests", out var questsElement))
                    {
                        return JsonSerializer.Deserialize<List<Quest>>(questsElement.GetRawText()) ?? new List<Quest>();
                    }
                }
            }
            catch { }

            return new List<Quest>();
        }

        private static List<Event> LoadEvents(string modulePath)
        {
            if (string.IsNullOrEmpty(modulePath))
                return new List<Event>();

            string eventPath = Path.Combine(modulePath, "events.json");
            if (!File.Exists(eventPath))
                return new List<Event>();

            try
            {
                string json = File.ReadAllText(eventPath);
                using (JsonDocument doc = JsonDocument.Parse(json))
                {
                    var root = doc.RootElement;
                    if (root.TryGetProperty("events", out var eventsElement))
                    {
                        return JsonSerializer.Deserialize<List<Event>>(eventsElement.GetRawText()) ?? new List<Event>();
                    }
                }
            }
            catch { }

            return new List<Event>();
        }

        private static string GenerateQuestsTable(List<Quest> quests)
        {
            var sb = new StringBuilder();

            if (quests != null && quests.Count > 0)
            {
                foreach (var quest in quests)
                {
                    sb.AppendLine("<tr>");
                    sb.AppendLine($"  <td><strong>{quest.Name ?? "Unknown Quest"}</strong></td>");
                    sb.AppendLine($"  <td>{quest.QuestType}</td>");
                    
                    // Target Amount Range
                    string targetAmount = "1";
                    if (quest.TargetAmountRange?.Length >= 2)
                    {
                        if (quest.TargetAmountRange[0] == quest.TargetAmountRange[1])
                            targetAmount = quest.TargetAmountRange[0].ToString();
                        else
                            targetAmount = $"{quest.TargetAmountRange[0]}-{quest.TargetAmountRange[1]}";
                    }
                    sb.AppendLine($"  <td>{targetAmount}</td>");
                    
                    sb.AppendLine($"  <td>{quest.RewardType}</td>");
                    sb.AppendLine($"  <td>{quest.RewardValue ?? ""}</td>");
                    sb.AppendLine($"  <td>{quest.RewardQuantity}</td>");
                    sb.AppendLine("</tr>");
                }
            }

            return sb.ToString();
        }

        private static string GenerateEventsTable(List<Event> events)
        {
            var sb = new StringBuilder();

            if (events != null && events.Count > 0)
            {
                foreach (var eventItem in events)
                {
                    sb.AppendLine("<tr>");
                    sb.AppendLine($"  <td><strong>{eventItem.Name ?? "Unknown Event"}</strong></td>");
                    
                    // Global
                    string globalClass = eventItem.Global ? "boolean-true" : "boolean-false";
                    string globalText = eventItem.Global ? "Yes" : "No";
                    sb.AppendLine($"  <td class=\"{globalClass}\">{globalText}</td>");
                    
                    sb.AppendLine($"  <td>{eventItem.Type}</td>");
                    sb.AppendLine($"  <td>{eventItem.ChancePercent:F1}%</td>");
                    sb.AppendLine($"  <td>{eventItem.Area?.ToString() ?? "-"}</td>");
                    sb.AppendLine($"  <td>{eventItem.Round?.ToString() ?? "-"}</td>");
                    sb.AppendLine($"  <td>{eventItem.Item ?? ""}</td>");
                    sb.AppendLine($"  <td>{eventItem.ItemQuantity?.ToString() ?? "-"}</td>");
                    sb.AppendLine("</tr>");
                }
            }

            return sb.ToString();
        }
    }
}