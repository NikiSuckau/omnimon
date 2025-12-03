using OmnimonModuleEditor.Models;
using System.IO;
using System.Text;

namespace OmnimonModuleEditor.docgenerators
{
    internal class UnlockGenerator
    {
        public static void GenerateUnlocksPage(string docPath, Module module)
        {
            string template = GeneratorUtils.GetTemplateContent("unlocks.html");
            var sb = new StringBuilder();

            if (module?.Unlocks != null)
            {
                foreach (var unlock in module.Unlocks)
                {
                    string description = GenerateUnlockDescription(unlock);
                    
                    sb.AppendLine("<tr>");
                    sb.AppendLine($"  <td>{unlock.Label ?? "Unnamed"}</td>");
                    sb.AppendLine($"  <td>{unlock.Type ?? "unknown"}</td>");
                    sb.AppendLine($"  <td>{description}</td>");
                    sb.AppendLine("</tr>");
                }
            }

            string content = template.Replace("#UNLOCKSDATA", sb.ToString());
            File.WriteAllText(Path.Combine(docPath, "unlocks.html"), content);
        }

        private static string GenerateUnlockDescription(Unlock unlock)
        {
            if (unlock == null) return "Unknown unlock condition";

            switch (unlock.Type?.ToLower())
            {
                case "egg":
                    if (unlock.Version.HasValue && unlock.Version > 0)
                    {
                        return $"Unlocked when hatching an egg from version {unlock.Version} of this module.";
                    }
                    return "Unlocked when hatching any egg from this module.";

                case "evolution":
                    var evolutionDesc = new StringBuilder("Unlocked when a pet evolves");
                    
                    if (!string.IsNullOrEmpty(unlock.Name) && unlock.To != null && unlock.To.Count > 0)
                    {
                        evolutionDesc.Append($" to {string.Join(" or ", unlock.To)}");
                    }
                    else if (!string.IsNullOrEmpty(unlock.Name))
                    {
                        evolutionDesc.Append($" to {unlock.Name}");
                    }
                    
                    if (unlock.Version.HasValue && unlock.Version > 0)
                    {
                        evolutionDesc.Append($" in version {unlock.Version}");
                    }
                    
                    evolutionDesc.Append(".");
                    return evolutionDesc.ToString();

                case "adventure":
                    var adventureDesc = new StringBuilder("Unlocked by completing");
                    
                    if (unlock.Area.HasValue && unlock.Area > 0)
                    {
                        adventureDesc.Append($" area {unlock.Area}");
                    }
                    
                    adventureDesc.Append(".");
                    return adventureDesc.ToString();

                case "digidex":
                    var digidexDesc = new StringBuilder("Unlocked when");
                    
                    if (unlock.Amount > 0)
                    {
                        digidexDesc.Append($" {unlock.Amount} are");
                    }
                    else if (!string.IsNullOrEmpty(unlock.Name))
                    {
                        digidexDesc.Append($" {unlock.Name} is");
                    }
                    else
                    {
                        digidexDesc.Append(" a pet is");
                    }
                    
                    digidexDesc.Append(" registered in the Digidex");
                    
                    
                    digidexDesc.Append(".");
                    return digidexDesc.ToString();

                case "background":
                    var bgDesc = new StringBuilder("Background unlocked by");
                    
                    if (unlock.Area.HasValue && unlock.Area > 0)
                    {
                        bgDesc.Append($" completing area {unlock.Area}");
                    }

                    
                    bgDesc.Append(".");
                    return bgDesc.ToString();

                case "group":
                    var groupDesc = new StringBuilder("Group unlock that triggers when");
                    
                    if (unlock.List != null && unlock.List.Count > 0)
                    {
                        if (unlock.List.Count == 1)
                        {
                            groupDesc.Append($" the following unlock is completed: {unlock.List[0]}");
                        }
                        else
                        {
                            groupDesc.Append($" ALL of the following {unlock.List.Count} unlocks are completed: {string.Join(", ", unlock.List)}");
                        }
                    }
                    else
                    {
                        groupDesc.Append(" all specified unlocks are completed (none currently configured)");
                    }
                    
                    groupDesc.Append(".");
                    return groupDesc.ToString();

                case "pvp":
                    var pvpDesc = new StringBuilder("Unlocked by competing in PVP battles against other devices");
                    if (unlock.Amount.HasValue && unlock.Amount > 0)
                    {
                        pvpDesc.Append($" and completing {unlock.Amount} PVP matches");
                    }
                    pvpDesc.Append(".");
                    return pvpDesc.ToString();

                case "versus":
                    var versusDesc = new StringBuilder("Unlocked by participating in Versus battles between pets of the same owner");
                    if (unlock.Amount.HasValue && unlock.Amount > 0)
                    {
                        versusDesc.Append($" and completing {unlock.Amount} Versus matches");
                    }
                    versusDesc.Append(".");
                    return versusDesc.ToString();

                case "battle":
                    var battleDesc = new StringBuilder("Unlocked by completing");
                    if (unlock.Amount.HasValue && unlock.Amount > 0)
                    {
                        battleDesc.Append($" {unlock.Amount} battles in this module's adventure mode");
                    }
                    else
                    {
                        battleDesc.Append(" battles in this module's adventure mode");
                    }
                    battleDesc.Append(".");
                    return battleDesc.ToString();

                default:
                    var genericDesc = new StringBuilder($"Unlocked not yet available");
                    
                    genericDesc.Append(".");
                    return genericDesc.ToString();
            }
        }
    }
}
