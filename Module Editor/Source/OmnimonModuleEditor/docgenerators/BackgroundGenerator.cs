using OmnipetModuleEditor.Models;
using System.IO;
using System.Text;

namespace OmnipetModuleEditor.docgenerators
{
    internal class BackgroundGenerator
    {
        public static void GenerateBackgroundsPage(string docPath, Module module)
        {
            string template = GeneratorUtils.GetTemplateContent("backgrounds.html");
            var sb = new StringBuilder();

            if (module?.Backgrounds != null)
            {
                foreach (var background in module.Backgrounds)
                {
                    sb.AppendLine("    <div class=\"background-card\">");
                    sb.AppendLine("      <div class=\"background-header\">");
                    sb.AppendLine($"        <h3 class=\"background-name\">{background.Label}</h3>");
                    sb.AppendLine("      </div>");
                    sb.AppendLine("      <div class=\"background-info\">");
                    if (background.DayNight)
                    {
                        sb.AppendLine("        <span class=\"background-type daynight\">Day/Night Cycle</span>");
                    }
                    else
                    {
                        sb.AppendLine("        <span class=\"background-type static\">Static</span>");
                    }
                    sb.AppendLine("      </div>");
                    sb.AppendLine("      <div class=\"background-sprites\">");

                    if (background.DayNight)
                    {
                        // Day/Night backgrounds have multiple sprites
                        var timeStates = new[] { "day", "dusk", "night" };
                        foreach (var timeState in timeStates)
                        {
                            sb.AppendLine("        <div class=\"sprite-section\">");
                            sb.AppendLine($"          <h4>{timeState.ToUpper()}</h4>");
                            sb.AppendLine("          <div class=\"sprite-row\">");

                            // Standard version
                            string standardPath = $"../backgrounds/bg_{background.Name}_{timeState}.png";
                            sb.AppendLine("            <div class=\"sprite-container\">");
                            sb.AppendLine($"              <img src=\"{standardPath}\" alt=\"{background.Name} {timeState}\" class=\"sprite-image\" onerror=\"this.parentElement.innerHTML='&lt;div class=&quot;sprite-missing&quot;&gt;Missing&lt;br&gt;Standard&lt;/div&gt;'; this.parentElement.classList.add('missing');\">");
                            sb.AppendLine("              <div class=\"sprite-label\">Standard</div>");
                            sb.AppendLine("            </div>");

                            // High resolution version
                            string highPath = $"../backgrounds/bg_{background.Name}_{timeState}_high.png";
                            sb.AppendLine("            <div class=\"sprite-container\">");
                            sb.AppendLine($"              <img src=\"{highPath}\" alt=\"{background.Name} {timeState} High\" class=\"sprite-image\" onerror=\"this.parentElement.innerHTML='&lt;div class=&quot;sprite-missing&quot;&gt;Missing&lt;br&gt;High Res&lt;/div&gt;'; this.parentElement.classList.add('missing');\">");
                            sb.AppendLine("              <div class=\"sprite-label\">High Res</div>");
                            sb.AppendLine("            </div>");

                            sb.AppendLine("          </div>");
                            sb.AppendLine("        </div>");
                        }
                    }
                    else
                    {
                        // Static background has only one set of sprites
                        sb.AppendLine("        <div class=\"sprite-section\">");
                        sb.AppendLine("          <h4>BACKGROUND</h4>");
                        sb.AppendLine("          <div class=\"sprite-row\">");

                        // Standard version
                        string standardPath = $"../backgrounds/bg_{background.Name}.png";
                        sb.AppendLine("            <div class=\"sprite-container\">");
                        sb.AppendLine($"              <img src=\"{standardPath}\" alt=\"{background.Name}\" class=\"sprite-image\" onerror=\"this.parentElement.innerHTML='&lt;div class=&quot;sprite-missing&quot;&gt;Missing&lt;br&gt;Standard&lt;/div&gt;'; this.parentElement.classList.add('missing');\">");
                        sb.AppendLine("              <div class=\"sprite-label\">Standard</div>");
                        sb.AppendLine("            </div>");

                        // High resolution version
                        string highPath = $"../backgrounds/bg_{background.Name}_high.png";
                        sb.AppendLine("            <div class=\"sprite-container\">");
                        sb.AppendLine($"              <img src=\"{highPath}\" alt=\"{background.Name} High\" class=\"sprite-image\" onerror=\"this.parentElement.innerHTML='&lt;div class=&quot;sprite-missing&quot;&gt;Missing&lt;br&gt;High Res&lt;/div&gt;'; this.parentElement.classList.add('missing');\">");
                        sb.AppendLine("              <div class=\"sprite-label\">High Res</div>");
                        sb.AppendLine("            </div>");

                        sb.AppendLine("          </div>");
                        sb.AppendLine("        </div>");
                    }

                    sb.AppendLine("      </div>");
                    sb.AppendLine("    </div>");
                }
            }

            string content = template.Replace("#BACKGROUNDSDATA", sb.ToString());
            File.WriteAllText(Path.Combine(docPath, "backgrounds.html"), content);
        }
    }
}
