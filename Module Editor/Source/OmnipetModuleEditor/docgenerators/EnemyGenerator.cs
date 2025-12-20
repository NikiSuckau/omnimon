using OmnipetModuleEditor.Models;
using OmnipetModuleEditor.Utils;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Text;

namespace OmnipetModuleEditor.docgenerators
{
    internal class EnemyGenerator
    {
        public static void GenerateEnemiesPage(string docPath, List<BattleEnemy> enemies, Module module, string modulePath)
        {
            string template = GeneratorUtils.GetTemplateContent("enemies.html");
            var sb = new StringBuilder();

            // Create assets folder in documentation and copy sprites
            var assetsPath = Path.Combine(docPath, "assets");
            Directory.CreateDirectory(assetsPath);
            CopyEnemySprites(enemies, modulePath, assetsPath, module);

            var enemiesByArea = enemies.GroupBy(e => e.Area).OrderBy(g => g.Key);

            foreach (var areaGroup in enemiesByArea)
            {
                sb.AppendLine("<div class=\"area-section\">");
                sb.AppendLine($"  <h2>Area {areaGroup.Key}</h2>");

                var enemiesByRound = areaGroup.GroupBy(e => e.Round).OrderBy(g => g.Key);
                var maxRound = areaGroup.Max(e => e.Round);

                foreach (var roundGroup in enemiesByRound)
                {
                    bool isBossRound = roundGroup.Key == maxRound;
                    string roundClass = isBossRound ? "round-section boss-round" : "round-section";

                    sb.AppendLine($"    <div class=\"{roundClass}\">");
                    sb.AppendLine($"      <h3>Round {roundGroup.Key}{(isBossRound ? " - Boss Round" : "")}</h3>");
                    sb.AppendLine("      <div class=\"enemies-grid\">");

                    // Group enemies by version and display them side by side
                    var enemiesByVersion = roundGroup.OrderBy(e => e.Version);

                    foreach (var enemy in enemiesByVersion)
                    {
                        string attributeColor = GeneratorUtils.GetAttributeBackgroundColor(enemy.Attribute ?? "");
                        string cardClass = isBossRound ? "enemy-card boss-enemy" : "enemy-card";
                        string spriteFileName = GetSafeFileName(enemy.Name) + ".png";

                        sb.AppendLine($"        <div class=\"{cardClass}\">");
                        sb.AppendLine("          <div class=\"enemy-sprite-container\">");
                        sb.AppendLine($"            <div class=\"enemy-sprite\" style=\"background-color:{attributeColor}\">");
                        sb.AppendLine($"              <img src=\"assets/{spriteFileName}\" alt=\"{enemy.Name}\" onerror=\"this.src='../missing.png'\">");
                        sb.AppendLine("            </div>");
                        sb.AppendLine("          </div>");
                        sb.AppendLine($"          <div class=\"enemy-name\">{enemy.Name}</div>");
                        sb.AppendLine($"          <div class=\"enemy-version\">Version {enemy.Version}</div>");
                        sb.AppendLine($"          <div class=\"enemy-stats\">Power: {enemy.Power} | HP: {enemy.Hp}</div>");
                        if (!string.IsNullOrEmpty(enemy.Prize))
                            sb.AppendLine($"          <div class=\"enemy-prize\">Prize: {enemy.Prize}</div>");
                        if (!string.IsNullOrEmpty(enemy.Unlock))
                            sb.AppendLine($"          <div class=\"enemy-unlock\">Unlock: {enemy.Unlock}</div>");
                        sb.AppendLine("        </div>");
                    }

                    sb.AppendLine("      </div>");
                    sb.AppendLine("    </div>");
                }

                sb.AppendLine("</div>");
            }

            string content = template.Replace("#ENEMIESDATA", sb.ToString());
            File.WriteAllText(Path.Combine(docPath, "enemies.html"), content);
        }

        /// <summary>
        /// Copies enemy sprites to the documentation assets folder.
        /// </summary>
        private static void CopyEnemySprites(List<BattleEnemy> enemies, string modulePath, string assetsPath, Module module)
        {
            // Create a missing.png placeholder
            CreateMissingSpritePlaceholder(assetsPath);

            var uniqueEnemyNames = enemies.Select(e => e.Name).Distinct();
            var nameFormat = module?.NameFormat ?? SpriteUtils.DefaultNameFormat;

            foreach (var enemyName in uniqueEnemyNames)
            {
                try
                {
                    // Use new sprite loading system with high definition support
                    bool moduleHighDefinitionSprites = module?.HighDefinitionSprites ?? false;
                    var sprite = SpriteUtils.LoadSingleSprite(enemyName, modulePath, nameFormat, moduleHighDefinitionSprites);
                    if (sprite != null)
                    {
                        string safeFileName = GetSafeFileName(enemyName) + ".png";
                        string outputPath = Path.Combine(assetsPath, safeFileName);
                        
                        // Save the sprite to the assets folder
                        sprite.Save(outputPath, ImageFormat.Png);
                        System.Diagnostics.Debug.WriteLine($"[EnemyGenerator] Copied sprite for {enemyName} to {outputPath}");
                    }
                    else
                    {
                        System.Diagnostics.Debug.WriteLine($"[EnemyGenerator] No sprite found for enemy {enemyName}");
                    }
                }
                catch (System.Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[EnemyGenerator] Error copying sprite for {enemyName}: {ex.Message}");
                }
            }
        }

        /// <summary>
        /// Creates a simple missing sprite placeholder.
        /// </summary>
        private static void CreateMissingSpritePlaceholder(string assetsPath)
        {
            try
            {
                string missingPath = Path.Combine(assetsPath, "missing.png");
                if (!File.Exists(missingPath))
                {
                    // Create a simple 48x48 gray square with "?" text
                    using (var bitmap = new Bitmap(48, 48))
                    using (var graphics = Graphics.FromImage(bitmap))
                    {
                        graphics.FillRectangle(Brushes.LightGray, 0, 0, 48, 48);
                        graphics.DrawRectangle(Pens.Gray, 0, 0, 47, 47);
                        
                        using (var font = new Font("Arial", 20, FontStyle.Bold))
                        {
                            var textSize = graphics.MeasureString("?", font);
                            var x = (48 - textSize.Width) / 2;
                            var y = (48 - textSize.Height) / 2;
                            graphics.DrawString("?", font, Brushes.DarkGray, x, y);
                        }
                        
                        bitmap.Save(missingPath, ImageFormat.Png);
                    }
                }
            }
            catch (System.Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[EnemyGenerator] Error creating missing.png: {ex.Message}");
            }
        }

        /// <summary>
        /// Converts a pet name to a safe filename.
        /// </summary>
        private static string GetSafeFileName(string petName)
        {
            return petName.Replace(" ", "_")
                         .Replace("(", "")
                         .Replace(")", "")
                         .Replace(":", "_")
                         .Replace("/", "_")
                         .Replace("\\", "_")
                         .Replace("?", "_")
                         .Replace("*", "_")
                         .Replace("\"", "_")
                         .Replace("<", "_")
                         .Replace(">", "_")
                         .Replace("|", "_");
        }
    }
}
