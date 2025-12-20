
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

public class HTMLGenerator
{
    public static void GenerateChartsHTML(List<Pet> pets, string outputPath)
    {
        var sb = new StringBuilder();
        sb.AppendLine("<!DOCTYPE html>");
        sb.AppendLine("<html lang="en">");
        sb.AppendLine("<head>");
        sb.AppendLine("  <meta charset="UTF-8">");
        sb.AppendLine("  <title>Pet Evolution Charts</title>");
        sb.AppendLine("  <link rel="stylesheet" href="../module.css">");
        sb.AppendLine("</head>");
        sb.AppendLine("<body>");
        sb.AppendLine("  <div class="chart">");

        var stages = new Dictionary<int, List<Pet>>();
        foreach (var pet in pets)
        {
            if (!stages.ContainsKey(pet.Stage))
                stages[pet.Stage] = new List<Pet>();
            stages[pet.Stage].Add(pet);
        }

        foreach (var stage in stages)
        {
            sb.AppendLine($"    <div class="column stage-column stage-{stage.Key}">");
            sb.AppendLine("      <div class="stage-header">" + GetStageName(stage.Key) + "</div>");
            foreach (var pet in stage.Value)
            {
                sb.AppendLine("      <div class="pet-container">");
                sb.AppendLine("        <div class="pet-card">");
                sb.AppendLine("          <div class="pet-sprite">");
                sb.AppendLine($"            <img src="../../monster/{pet.Folder}/0.png" alt="{pet.Name}">");
                sb.AppendLine("          </div>");
                sb.AppendLine($"          <div class="pet-name">{pet.Name}</div>");
                sb.AppendLine("        </div>");
                sb.AppendLine("      </div>");
            }
            sb.AppendLine("    </div>");
        }

        sb.AppendLine("  </div>");
        sb.AppendLine("</body>");
        sb.AppendLine("</html>");

        File.WriteAllText(outputPath, sb.ToString());
    }

    private static string GetStageName(int stage)
    {
        return stage switch
        {
            0 => "Egg",
            1 => "Fresh",
            2 => "In-Training",
            3 => "Rookie",
            4 => "Champion",
            5 => "Ultimate",
            6 => "Mega",
            7 => "Super Ultimate",
            _ => "Unknown"
        };
    }
}

public class Pet
{
    public string Name { get; set; }
    public string Folder { get; set; }
    public int Stage { get; set; }
    public string Attribute { get; set; }
}
