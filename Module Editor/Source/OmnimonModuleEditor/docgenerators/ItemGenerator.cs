using OmnimonModuleEditor.Models;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace OmnimonModuleEditor.docgenerators
{
    internal class ItemGenerator
    {
        public static void GenerateItemsPage(string docPath, List<Item> items)
        {
            string template = GeneratorUtils.GetTemplateContent("items.html");
            var sb = new StringBuilder();

            if (items != null && items.Count > 0)
            {
                foreach (var item in items)
                {
                    sb.AppendLine("<tr>");
                    sb.AppendLine("  <td>");
                    sb.AppendLine("    <div class=\"item-name-container\">");
                    if (!string.IsNullOrEmpty(item.SpriteName))
                    {
                        sb.AppendLine($"      <img src=\"../items/{item.SpriteName}.png\" alt=\"{item.Name}\" class=\"item-icon\" onerror=\"this.style.display='none'\">");
                    }
                    sb.AppendLine($"      <span class=\"item-name\">{item.Name}</span>");
                    sb.AppendLine("    </div>");
                    sb.AppendLine("  </td>");
                    sb.AppendLine($"  <td>{item.Description ?? ""}</td>");
                    sb.AppendLine($"  <td>{item.Effect ?? ""}</td>");
                    sb.AppendLine($"  <td>{item.Status ?? ""}</td>");
                    sb.AppendLine($"  <td>{item.Amount}</td>");
                    sb.AppendLine($"  <td>{item.WeightGain}</td>");
                    sb.AppendLine("</tr>");
                }
            }

            string content = template.Replace("#ITEMSDATA", sb.ToString());
            File.WriteAllText(Path.Combine(docPath, "items.html"), content);
        }
    }
}
