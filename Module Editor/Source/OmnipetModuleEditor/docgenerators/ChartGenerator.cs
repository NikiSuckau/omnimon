using OmnipetModuleEditor.Models;
using OmnipetModuleEditor.Utils;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Text;

namespace OmnipetModuleEditor.docgenerators
{
    internal class ChartGenerator
    {
        public static void GenerateChartsPage(string docPath, List<Pet> pets, Module module, string modulePath)
        {
            string template = GeneratorUtils.GetTemplateContent("charts.html");
            var sb = new StringBuilder();

            // Create assets folder in documentation and copy sprites
            var assetsPath = Path.Combine(docPath, "assets");
            Directory.CreateDirectory(assetsPath);
            CopyPetSprites(pets, modulePath, assetsPath, module);

            var petsByVersion = pets.GroupBy(p => p.Version).OrderBy(g => g.Key);
            var versionColors = new[] { "chartYellow", "chartBlue", "chartViolet", "chartRed", "chartGreen" };
            int colorIndex = 0;

            foreach (var versionGroup in petsByVersion)
            {
                string colorClass = versionColors[colorIndex % versionColors.Length];
                colorIndex++;

                sb.AppendLine($"<div id=\"c{versionGroup.Key}_anchor\" class=\"anchor {colorClass}\">");
                sb.AppendLine("  <div class=\"family\">");

                // Digitama header section - use the actual egg sprite from stage 0
                sb.AppendLine("    <div class=\"digitama\">");
                var eggPet = versionGroup.FirstOrDefault(p => p.Stage == 0);
                if (eggPet != null)
                {
                    string spriteFileName = GetSafeFileName(eggPet.Name) + ".png";
                    sb.AppendLine($"      <img src=\"assets/{spriteFileName}\" title=\"Ver.{versionGroup.Key} {eggPet.Name}\" onerror=\"this.src='../missing.png'\">");
                }
                else
                {
                    sb.AppendLine($"      <img src=\"../missing.png\" title=\"Ver.{versionGroup.Key} Egg\" onerror=\"this.src='../missing.png'\">");
                }
                sb.AppendLine("      <div>");
                sb.AppendLine($"        <h4 class=\"rdisplay\">Ver.{versionGroup.Key}</h4>");
                sb.AppendLine($"        <p>Version {versionGroup.Key} Roster</p>");
                sb.AppendLine("      </div>");
                sb.AppendLine("    </div>");

                sb.AppendLine($"    <div id=\"c{versionGroup.Key}\" class=\"chart\">");
                GenerateEvolutionTree(sb, versionGroup.ToList(), module, versionGroup.Key);
                sb.AppendLine("    </div>");
                sb.AppendLine("  </div>");
                sb.AppendLine("</div>");
            }

            string content = template.Replace("#EVOLUTIONCHARTS", sb.ToString());
            File.WriteAllText(Path.Combine(docPath, "charts.html"), content);
        }

        /// <summary>
        /// Copies pet sprites to the documentation assets folder.
        /// </summary>
        private static void CopyPetSprites(List<Pet> pets, string modulePath, string assetsPath, Module module)
        {
            // Create a missing.png placeholder
            CreateMissingSpritePlaceholder(assetsPath);

            var uniquePetNames = pets.Select(p => p.Name).Distinct();
            var nameFormat = module?.NameFormat ?? SpriteUtils.DefaultNameFormat;

            foreach (var petName in uniquePetNames)
            {
                try
                {
                    // Use new sprite loading system with high definition support
                    bool moduleHighDefinitionSprites = module?.HighDefinitionSprites ?? false;
                    var sprite = SpriteUtils.LoadSingleSprite(petName, modulePath, nameFormat, moduleHighDefinitionSprites);
                    if (sprite != null)
                    {
                        string safeFileName = GetSafeFileName(petName) + ".png";
                        string outputPath = Path.Combine(assetsPath, safeFileName);
                        
                        // Save the sprite to the assets folder
                        sprite.Save(outputPath, ImageFormat.Png);
                        System.Diagnostics.Debug.WriteLine($"[ChartGenerator] Copied sprite for {petName} to {outputPath}");
                    }
                    else
                    {
                        System.Diagnostics.Debug.WriteLine($"[ChartGenerator] No sprite found for pet {petName}");
                    }
                }
                catch (System.Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[ChartGenerator] Error copying sprite for {petName}: {ex.Message}");
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
                System.Diagnostics.Debug.WriteLine($"[ChartGenerator] Error creating missing.png: {ex.Message}");
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

        public static void GenerateEvolutionTree(StringBuilder sb, List<Pet> pets, Module module, int version)
        {
            var petsByStage = pets.GroupBy(p => p.Stage).OrderBy(g => g.Key).ToDictionary(g => g.Key, g => g.ToList());

            int petHeight = 120;
            int petSize = 80;
            int startX = 50;
            int startY = 50;

            int minStage = petsByStage.Keys.Min();
            int maxStage = petsByStage.Keys.Max();
            int maxPetsInStage = petsByStage.Values.Max(petList => petList.Count);

            // Reorder pets within each stage to minimize line crossings
            OptimizePetOrdering(petsByStage, pets, version);

            // Calcule os espaçamentos dinâmicos
            int[] stageWidths = CalculateStageWidths(petsByStage, pets, version);

            // Calcule as posições X acumuladas para cada stage
            int[] stageXs = new int[maxStage - minStage + 1];
            stageXs[0] = startX;
            for (int i = 1; i < stageXs.Length; i++)
                stageXs[i] = stageXs[i - 1] + stageWidths[i - 1];

            int svgWidth = stageXs.Last() + petSize + 100;
            int svgHeight = startY + (maxPetsInStage * petHeight) + 100;

            sb.AppendLine($"<svg width=\"{svgWidth}\" height=\"{svgHeight}\" xmlns=\"http://www.w3.org/2000/svg\">");
            sb.AppendLine("  <defs>");
            sb.AppendLine("    <style>");
            sb.AppendLine("      .pet-square { cursor: pointer; }");
            sb.AppendLine("      .pet-name { font-family: Arial, sans-serif; font-size: 9px; font-weight: bold; text-anchor: middle; fill: white; text-shadow: 1px 1px 1px rgba(0,0,0,0.8); }");
            sb.AppendLine("      .stage-label { font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; text-anchor: middle; fill: #222; }");
            sb.AppendLine("    </style>");
            sb.AppendLine("  </defs>");

            // Random color for each pet's contour/lines
            var petContourColors = new Dictionary<string, string>();
            string[] contourColors = { "#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6", "#e67e22", "#1abc9c", "#34495e", "#95a5a6", "#c0392b" };
            int colorIndex = 0;
            foreach (var pet in pets)
            {
                petContourColors[pet.Name] = contourColors[colorIndex % contourColors.Length];
                colorIndex++;
            }

            // Add module name format as a data attribute to the SVG for JavaScript access
            string nameFormat = PetUtils.FixedNameFormat; // Use fixed format instead of module?.NameFormat ?? "$"
            sb.AppendLine($"  <metadata>");
            sb.AppendLine($"    <moduleNameFormat>{nameFormat}</moduleNameFormat>");
            sb.AppendLine($"  </metadata>");

            // Stage labels (agora no fundo)
            int stageLabelY = svgHeight - 20;
            for (int stage = minStage; stage <= maxStage; stage++)
            {
                if (!petsByStage.ContainsKey(stage)) continue;
                int stageX = stageXs[stage - minStage] + petSize / 2;
                sb.AppendLine($"  <text x=\"{stageX}\" y=\"{stageLabelY}\" class=\"stage-label\">{GeneratorUtils.GetStageDisplayName(stage)}</text>");
            }

            // Pet boxes
            for (int stage = minStage; stage <= maxStage; stage++)
            {
                if (!petsByStage.ContainsKey(stage)) continue;
                var stagePets = petsByStage[stage]; // Use the reordered pets
                int stageX = stageXs[stage - minStage];
                int totalStageHeight = stagePets.Count * petHeight;
                int maxStageHeight = maxPetsInStage * petHeight;
                int centerOffset = (maxStageHeight - totalStageHeight) / 2;

                for (int i = 0; i < stagePets.Count; i++)
                {
                    var pet = stagePets[i];
                    int petY = startY + centerOffset + (i * petHeight);
                    DrawPetSquare(sb, pet, stageX, petY, petSize, module, version, petContourColors[pet.Name]);
                }
            }

            // Passe stageXs para DrawEvolutionLines
            DrawEvolutionLines(sb, pets, petsByStage, stageXs, startY, petHeight, petSize, version, maxPetsInStage, minStage, petContourColors);

            sb.AppendLine("</svg>");
        }

        public static void OptimizePetOrdering(Dictionary<int, List<Pet>> petsByStage, List<Pet> pets, int version)
        {
            // Start from the earliest stage and work forward
            var stages = petsByStage.Keys.OrderBy(s => s).ToList();

            for (int stageIndex = 0; stageIndex < stages.Count - 1; stageIndex++)
            {
                int currentStage = stages[stageIndex];
                int nextStage = stages[stageIndex + 1];

                if (!petsByStage.ContainsKey(currentStage) || !petsByStage.ContainsKey(nextStage))
                    continue;

                var currentStagePets = petsByStage[currentStage];
                var nextStagePets = petsByStage[nextStage];

                // Calculate optimal positions for next stage pets based on their evolution sources
                var nextStageOptimal = new List<(Pet pet, double optimalPosition)>();

                for (int i = 0; i < nextStagePets.Count; i++)
                {
                    var nextPet = nextStagePets[i];
                    var sourcePositions = new List<int>();

                    // Find all pets in current stage that evolve to this pet
                    for (int j = 0; j < currentStagePets.Count; j++)
                    {
                        var currentPet = currentStagePets[j];
                        if (currentPet.Evolve != null &&
                            currentPet.Evolve.Any(e => e.To == nextPet.Name &&
                                                     pets.Any(p => p.Name == e.To && p.Version == version)))
                        {
                            sourcePositions.Add(j);
                        }
                    }

                    // Calculate optimal position (average of source positions, or keep current if no sources)
                    double optimalPos = sourcePositions.Count > 0 ? sourcePositions.Average() : i;
                    nextStageOptimal.Add((nextPet, optimalPos));
                }

                // Sort next stage pets by their optimal positions
                nextStageOptimal.Sort((a, b) => a.optimalPosition.CompareTo(b.optimalPosition));

                // Update the list with the optimized order
                petsByStage[nextStage] = nextStageOptimal.Select(x => x.pet).ToList();
            }
        }

        public static void DrawPetSquare(StringBuilder sb, Pet pet, int x, int y, int size, Module module, int version, string contourColor)
        {
            string petId = GeneratorUtils.CleanPetId(pet.Name);
            string attributeColor = GeneratorUtils.GetAttributeColor(pet.Attribute ?? "");
            string spriteFileName = GetSafeFileName(pet.Name) + ".png";

            // Serialize pet data for modal - handle missing properties safely
            var petData = new
            {
                name = pet.Name ?? "Unknown",
                stage = pet.Stage,
                version = pet.Version,
                attribute = pet.Attribute ?? "",
                atkMain = pet.AtkMain,
                atkAlt = pet.AtkAlt,
                time = pet.Time,
                energy = pet.Energy,
                minWeight = pet.MinWeight,
                evolWeight = pet.EvolWeight,
                stomach = pet.Stomach,
                hungerLoss = pet.HungerLoss,
                poopTimer = pet.PoopTimer,
                sleeps = pet.Sleeps ?? "",
                wakes = pet.Wakes ?? "",
                special = pet.Special,
                specialKey = pet.SpecialKey ?? "",
                power = pet.Power,
                hp = pet.Hp,
                strengthLoss = pet.StrengthLoss,
                conditionHearts = pet.ConditionHearts,
                healDoses = pet.HealDoses,
                jogressAvailable = pet.JogressAvaliable
            };

            string petDataJson = System.Text.Json.JsonSerializer.Serialize(petData).Replace("\"", "&quot;");

            sb.AppendLine($"  <g class=\"pet-square\" onclick=\"showPetModal(evt, this)\" data-pet=\"{petId}\" data-pet-info=\"{petDataJson}\">");
            sb.AppendLine($"    <rect x=\"{x}\" y=\"{y}\" width=\"{size}\" height=\"{size}\" fill=\"{attributeColor}\" stroke=\"{contourColor}\" stroke-width=\"3\" rx=\"8\"/>");
            sb.AppendLine($"    <rect x=\"{x + 2}\" y=\"{y + 2}\" width=\"{size - 4}\" height=\"{size - 4}\" fill=\"none\" stroke=\"white\" stroke-width=\"1\" rx=\"6\"/>");
            int imageSize = size - 25;
            int imageX = x + 12;
            int imageY = y + 8;
            sb.AppendLine($"    <foreignObject x=\"{imageX}\" y=\"{imageY}\" width=\"{imageSize}\" height=\"{imageSize}\">");
            sb.AppendLine($"      <img src=\"assets/{spriteFileName}\" width=\"{imageSize}\" height=\"{imageSize}\" style=\"image-rendering: pixelated; object-fit: contain;\" onerror=\"this.src='../missing.png'\"/>");
            sb.AppendLine("    </foreignObject>");
            int textX = x + size / 2;
            int textY = y + size - 8;
            string[] nameWords = pet.Name.Split(' ');
            if (nameWords.Length > 1 && pet.Name.Length > 12)
            {
                sb.AppendLine($"    <text x=\"{textX}\" y=\"{textY - 8}\" class=\"pet-name\">{nameWords[0]}</text>");
                sb.AppendLine($"    <text x=\"{textX}\" y=\"{textY + 2}\" class=\"pet-name\">{string.Join(" ", nameWords.Skip(1))}</text>");
            }
            else
            {
                sb.AppendLine($"    <text x=\"{textX}\" y=\"{textY}\" class=\"pet-name\">{pet.Name}</text>");
            }
            sb.AppendLine("  </g>");
        }

        public static void DrawEvolutionLines(
            StringBuilder sb,
            List<Pet> pets,
            Dictionary<int, List<Pet>> petsByStage,
            int[] stageXs,
            int startY,
            int petHeight,
            int petSize,
            int version,
            int maxPetsInStage,
            int minStage,
            Dictionary<string, string> petContourColors)
        {
            sb.AppendLine("  <g class=\"evolution-lines\">");

            // Track horizontal offsets by stage to separate vertical lines from different pets
            var horizontalOffsetByStage = new Dictionary<int, int>();

            // Track connections to each target to handle vertical offsets
            var targetConnections = new Dictionary<string, List<(Pet source, List<Evolution> evolutions, int sourceY, string strokeColor)>>();

            // First pass: collect all connections to each target
            foreach (var pet in pets.Where(p => p.Evolve != null && p.Evolve.Count > 0))
            {
                var stagePets = petsByStage[pet.Stage];
                int petIndex = stagePets.IndexOf(pet);
                int fromY = GetPetCenterY(startY, petHeight, maxPetsInStage, stagePets.Count, petIndex, petSize);
                string strokeColor = petContourColors[pet.Name];

                var evolutions = pet.Evolve
                    .Select(evo => new
                    {
                        Evo = evo,
                        Target = pets.FirstOrDefault(p2 => p2.Name == evo.To && p2.Version == version)
                    })
                    .Where(e => e.Target != null)
                    .ToList();

                if (evolutions.Count == 0) continue;

                // Group evolutions by target
                var evolutionsByTarget = evolutions
                    .GroupBy(e => e.Target.Name)
                    .Select(g => new
                    {
                        Target = g.First().Target,
                        Evolutions = g.Select(x => x.Evo).ToList()
                    })
                    .ToList();

                foreach (var group in evolutionsByTarget)
                {
                    string targetKey = group.Target.Name;
                    if (!targetConnections.ContainsKey(targetKey))
                        targetConnections[targetKey] = new List<(Pet, List<Evolution>, int, string)>();

                    targetConnections[targetKey].Add((pet, group.Evolutions, fromY, strokeColor));
                }
            }

            // Second pass: draw all connections with proper offsets
            foreach (var pet in pets.Where(p => p.Evolve != null && p.Evolve.Count > 0))
            {
                var stagePets = petsByStage[pet.Stage];
                int petIndex = stagePets.IndexOf(pet);
                int fromX = stageXs[pet.Stage - minStage] + petSize;
                int fromY = GetPetCenterY(startY, petHeight, maxPetsInStage, stagePets.Count, petIndex, petSize);

                string strokeColor = petContourColors[pet.Name];

                var evolutions = pet.Evolve
                    .Select(evo => new
                    {
                        Evo = evo,
                        Target = pets.FirstOrDefault(p2 => p2.Name == evo.To && p2.Version == version)
                    })
                    .Where(e => e.Target != null)
                    .ToList();

                if (evolutions.Count == 0) continue;

                // Group evolutions by target
                var evolutionsByTarget = evolutions
                    .GroupBy(e => e.Target.Name)
                    .Select(g => new
                    {
                        Target = g.First().Target,
                        Evolutions = g.Select(x => x.Evo).ToList()
                    })
                    .ToList();

                // Get horizontal offset for this stage column - reduced spacing
                if (!horizontalOffsetByStage.ContainsKey(pet.Stage))
                    horizontalOffsetByStage[pet.Stage] = 0;

                int horizontalOffset = horizontalOffsetByStage[pet.Stage];
                horizontalOffsetByStage[pet.Stage] += 8; // Reduced from 18 to 8 for closer lines

                // Calculate line positions
                int lineStartX = fromX;
                int lineEndX = stageXs[pet.Stage - minStage] + petSize + 40 + horizontalOffset; // Reduced base offset
                int lineY = fromY;

                // Draw horizontal line from pet to vertical junction
                sb.AppendLine($"    <line x1=\"{lineStartX}\" y1=\"{lineY}\" x2=\"{lineEndX}\" y2=\"{lineY}\" stroke=\"{strokeColor}\" stroke-width=\"3\"/>"); // Thicker line

                // Calculate target Y positions with proper vertical spacing
                var targetData = new List<(object group, int finalY)>();

                foreach (var group in evolutionsByTarget)
                {
                    var targetStagePets = petsByStage[group.Target.Stage];
                    int targetIndex = targetStagePets.IndexOf(group.Target);
                    int baseY = GetPetCenterY(startY, petHeight, maxPetsInStage, targetStagePets.Count, targetIndex, petSize);

                    // Calculate vertical offset based on position among all connections to this target
                    var allConnectionsToTarget = targetConnections[group.Target.Name];
                    int connectionIndex = allConnectionsToTarget.FindIndex(c => c.source == pet);

                    int finalY = baseY;
                    if (allConnectionsToTarget.Count > 1)
                    {
                        int spacing = 20; // Increased spacing between connections to same target
                        int totalHeight = (allConnectionsToTarget.Count - 1) * spacing;
                        int startOffset = -totalHeight / 2;
                        finalY = baseY + startOffset + (connectionIndex * spacing);
                    }

                    targetData.Add((group, finalY));
                }

                var targetYs = targetData.Select(t => t.finalY).ToList();
                int minY = Math.Min(lineY, targetYs.Min());
                int maxY = Math.Max(lineY, targetYs.Max());

                // Draw vertical line connecting all targets
                if (evolutionsByTarget.Count > 1 || Math.Abs(lineY - targetYs[0]) > 2)
                {
                    sb.AppendLine($"    <line x1=\"{lineEndX}\" y1=\"{minY}\" x2=\"{lineEndX}\" y2=\"{maxY}\" stroke=\"{strokeColor}\" stroke-width=\"3\"/>"); // Thicker line
                }

                // Draw lines to each target with criteria
                for (int idx = 0; idx < targetData.Count; idx++)
                {
                    var (groupObj, finalTargetY) = targetData[idx];
                    var group = evolutionsByTarget[idx]; // Use the original group from evolutionsByTarget
                    int toStage = group.Target.Stage;
                    int toX = stageXs[toStage - minStage];

                    // Horizontal line to target with arrow
                    sb.AppendLine($"    <line x1=\"{lineEndX}\" y1=\"{finalTargetY}\" x2=\"{toX - 4}\" y2=\"{finalTargetY}\" stroke=\"{strokeColor}\" stroke-width=\"3\" marker-end=\"url(#arrowhead)\"/>"); // Thicker line

                    int evoCount = group.Evolutions.Count;

                    if (evoCount > 1)
                    {
                        // Show badge for multiple evolutions to same target - moved closer to target
                        var criteriaTexts = group.Evolutions
                            .Select(evo => GenerateCriteriaText(evo))
                            .ToList();

                        string criteriaData = System.Text.Json.JsonSerializer.Serialize(criteriaTexts)
                            .Replace("\"", "&quot;");

                        int badgeRadius = 10;
                        int badgeX = toX - 30; // Moved much closer to target
                        int badgeY = finalTargetY - badgeRadius;

                        sb.AppendLine($@"
    <g class='evo-badge' 
       data-evos=""{criteriaData}""
       onclick=""showEvoModal(evt, this)""
       style='cursor:pointer'>
      <circle cx='{badgeX}' cy='{badgeY + badgeRadius}' r='{badgeRadius}' fill='#fff' stroke='{strokeColor}' stroke-width='2'/>
      <text x='{badgeX}' y='{badgeY + badgeRadius + 4}' text-anchor='middle' font-size='12' font-family='Arial' fill='{strokeColor}' font-weight='bold'>{evoCount}</text>
    </g>
");
                    }
                    else if (evoCount == 1)
                    {
                        // Show compact criteria panel with up to 3 lines
                        var criteriaLines = GenerateCriteriaText(group.Evolutions[0])
                            .Split('\n')
                            .Where(l => !string.IsNullOrWhiteSpace(l) && l != "no criteria")
                            .ToList();

                        if (criteriaLines.Count > 0)
                        {
                            // Allow up to 3 lines, with 2 criteria per line
                            var displayLines = new List<string>();
                            for (int i = 0; i < Math.Min(criteriaLines.Count, 6); i += 2) // Max 3 lines, 6 criteria total
                            {
                                if (i + 1 < criteriaLines.Count)
                                    displayLines.Add(criteriaLines[i] + " | " + criteriaLines[i + 1]); // Use | separator
                                else
                                    displayLines.Add(criteriaLines[i]);

                                if (displayLines.Count >= 3) break; // Max 3 lines
                            }

                            // Improved sizing for better readability
                            int maxLineLength = displayLines.Max(l => l.Length);
                            int boxWidth = Math.Min(200, Math.Max(80, maxLineLength * 4 + 12)); // Increased multiplier
                            int boxHeight = 10 * displayLines.Count + 6; // Better height for 3 lines
                            int boxX = lineEndX + 12; // Closer to junction
                            int boxY = finalTargetY - boxHeight / 2;

                            sb.AppendLine($"    <g>");
                            sb.AppendLine($"      <rect x=\"{boxX}\" y=\"{boxY}\" width=\"{boxWidth}\" height=\"{boxHeight}\" " +
                                          $"fill=\"#fff\" stroke=\"{strokeColor}\" stroke-width=\"1\" rx=\"2\"/>");

                            for (int i = 0; i < displayLines.Count; i++)
                            {
                                int textY = boxY + 8 + i * 10; // Proper line spacing
                                sb.AppendLine($"      <text x=\"{boxX + boxWidth / 2}\" y=\"{textY}\" " +
                                              $"font-family=\"Arial\" font-size=\"8\" text-anchor=\"middle\" fill=\"#222\">{displayLines[i]}</text>");
                            }
                            sb.AppendLine($"    </g>");
                        }
                    }
                }
            }

            sb.AppendLine("  </g>");
        }

        // Função auxiliar para centralizar o pet na coluna
        public static int GetPetCenterY(int startY, int petHeight, int maxPetsInStage, int petsInStage, int petIndex, int petSize)
        {
            int totalStageHeight = petsInStage * petHeight;
            int maxStageHeight = maxPetsInStage * petHeight;
            int centerOffset = (maxStageHeight - totalStageHeight) / 2;
            return startY + centerOffset + (petIndex * petHeight) + petSize / 2;
        }

        public static string GetEvolutionRequirementsText(Evolution evolution)
        {
            var requirements = new List<string>();
            if (evolution.Mistakes != null && evolution.Mistakes.Length > 0)
                requirements.Add($"M:{evolution.Mistakes[0]}");
            if (evolution.Training != null && evolution.Training.Length > 0)
            {
                if (evolution.Training.Length == 1)
                    requirements.Add($"T:{evolution.Training[0]}");
                else
                    requirements.Add($"T:{evolution.Training[0]}-{evolution.Training[1]}");
            }
            if (evolution.Battles != null && evolution.Battles.Length > 0)
                requirements.Add("Battles");
            if (evolution.WinRatio != null && evolution.WinRatio.Length > 0)
                requirements.Add("WinRatio");
            if (evolution.WinCount != null && evolution.WinCount.Length > 0)
                requirements.Add("WinCount"); // New field
            if (evolution.Overfeed != null && evolution.Overfeed.Length > 0)
                requirements.Add($"O:{evolution.Overfeed[0]}");
            if (evolution.SleepDisturbances != null && evolution.SleepDisturbances.Length > 0)
                requirements.Add($"S:{evolution.SleepDisturbances[0]}");
            if (!string.IsNullOrEmpty(evolution.Item))
                requirements.Add($"Item:{evolution.Item}");
            if (!string.IsNullOrEmpty(evolution.Jogress))
                requirements.Add($"Jogress:{evolution.Jogress}");
            if (evolution.Trophies != null && evolution.Trophies.Length > 0)
                requirements.Add("Trophies"); // New field
            if (evolution.VitalValues != null && evolution.VitalValues.Length > 0)
                requirements.Add("VitalValues"); // New field
            if (evolution.Weigth != null && evolution.Weigth.Length > 0)
                requirements.Add("Weight"); // New field
            if (evolution.QuestsCompleted != null && evolution.QuestsCompleted.Length > 0)
                requirements.Add("QuestsCompleted"); // New field
            if (evolution.Pvp != null && evolution.Pvp.Length > 0)
                requirements.Add("PVP"); // New field
            return string.Join(", ", requirements.Take(2));
        }

        public static string FormatTrainingRange(int[] training)
        {
            if (training == null || training.Length == 0) return "031";
            if (training.Length == 1)
                return training[0] == 999999 ? "" : training[0].ToString("D3");
            string min = training[0] == 999999 ? "0" : training[0].ToString();
            string max = training[1] == 999999 ? "31" : training[1].ToString();
            return $"{min}{max}";
        }

        public static int[] CalculateStageWidths(Dictionary<int, List<Pet>> petsByStage, List<Pet> pets, int version)
        {
            // Espaçamento padrão e reduzido
            int defaultWidth = 300;
            int compactWidth = 120;

            int minStage = petsByStage.Keys.Min();
            int maxStage = petsByStage.Keys.Max();
            int[] stageWidths = new int[maxStage - minStage];

            for (int stage = minStage; stage < maxStage; stage++)
            {
                bool allNoCriteria = true;
                if (petsByStage.ContainsKey(stage))
                {
                    foreach (var pet in petsByStage[stage])
                    {
                        var evolutions = pet.Evolve?.Where(e => pets.Any(p2 => p2.Name == e.To && p2.Stage == stage + 1 && p2.Version == version)).ToList();
                        if (evolutions != null && evolutions.Count > 0)
                        {
                            foreach (var evo in evolutions)
                            {
                                if (!string.IsNullOrEmpty(GetEvolutionRequirementsText(evo)))
                                {
                                    allNoCriteria = false;
                                    break;
                                }
                            }
                        }
                        if (!allNoCriteria) break;
                    }
                }
                stageWidths[stage - minStage] = allNoCriteria ? compactWidth : defaultWidth;
            }
            return stageWidths;
        }

        public static string GenerateCriteriaText(Evolution evo)
        {
            var lines = new List<string>();

            if (evo != null)
            {
                if (evo.ConditionHearts != null)
                {
                    var formatRange = string.Join(",", evo.ConditionHearts.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Condition Hearts: {formatRange}");
                }
                if (evo.Training != null)
                {
                    var formatRange = string.Join(",", evo.Training.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Training: {formatRange}");
                }
                if (evo.Battles != null)
                {
                    var formatRange = string.Join(",", evo.Battles.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Battles: {formatRange}");
                }
                if (evo.WinRatio != null)
                {
                    var formatRange = string.Join(",", evo.WinRatio.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Win Ratio: {formatRange}");
                }
                if (evo.WinCount != null)
                {
                    var formatRange = string.Join(",", evo.WinCount.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Win Count: {formatRange}");
                }
                if (evo.Mistakes != null)
                {
                    var formatRange = string.Join(",", evo.Mistakes.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Mistakes: {formatRange}");
                }
                if (evo.Level != null)
                {
                    var formatRange = string.Join(",", evo.Level.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Level: {formatRange}");
                }
                if (evo.Overfeed != null)
                {
                    var formatRange = string.Join(",", evo.Overfeed.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Overfeed: {formatRange}");
                }
                if (evo.SleepDisturbances != null)
                {
                    var formatRange = string.Join(",", evo.SleepDisturbances.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Sleep Disturbances: {formatRange}");
                }
                if (evo.Area != null) lines.Add($"Area: {(evo.Area == 999999 ? "+" : evo.Area.ToString())}");
                if (evo.Stage != null) lines.Add($"Stage: {(evo.Stage == 999999 ? "+" : evo.Stage.ToString())}");
                if (evo.Version != null) lines.Add($"Version: {(evo.Version == 999999 ? "+" : evo.Version.ToString())}");
                if (!string.IsNullOrEmpty(evo.Attribute)) lines.Add($"Attribute: {evo.Attribute}");
                if (!string.IsNullOrEmpty(evo.Jogress)) lines.Add($"Jogress: {evo.Jogress}");
                if (evo.JogressPrefix != null) lines.Add($"Jogress Prefix: {(evo.JogressPrefix.Value ? "Yes" : "No")}");
                if (evo.SpecialEncounter != null) lines.Add($"Special Encounter: {evo.SpecialEncounter}");
                if (evo.Stage5 != null)
                {
                    var formatRange = string.Join(",", evo.Stage5.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Stage-5: {formatRange}");
                }
                if (evo.Stage6 != null)
                {
                    var formatRange = string.Join(",", evo.Stage6.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Stage-6: {formatRange}");
                }
                if (evo.Stage7 != null)
                {
                    var formatRange = string.Join(",", evo.Stage7.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Stage-7: {formatRange}");
                }
                if (evo.Stage8 != null)
                {
                    var formatRange = string.Join(",", evo.Stage8.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Stage-8: {formatRange}");
                }
                if (evo.Item != null) lines.Add($"Item: {evo.Item}");
                if (evo.TimeRange != null && evo.TimeRange.Length > 0 && (!string.IsNullOrWhiteSpace(evo.TimeRange[0]) || (evo.TimeRange.Length > 1 && !string.IsNullOrWhiteSpace(evo.TimeRange[1]))))
                {
                    string t0 = evo.TimeRange.Length > 0 ? evo.TimeRange[0] : "";
                    string t1 = evo.TimeRange.Length > 1 ? evo.TimeRange[1] : "";
                    lines.Add($"Time Range: {t0} - {t1}");
                }
                if (evo.Trophies != null)
                {
                    var formatRange = string.Join(",", evo.Trophies.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Trophies: {formatRange}");
                }
                if (evo.VitalValues != null)
                {
                    var formatRange = string.Join(",", evo.VitalValues.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Vital Values: {formatRange}");
                }
                if (evo.Weigth != null)
                {
                    var formatRange = string.Join(",", evo.Weigth.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Weight: {formatRange}");
                }
                if (evo.QuestsCompleted != null)
                {
                    var formatRange = string.Join(",", evo.QuestsCompleted.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Quests Completed: {formatRange}");
                }
                if (evo.Pvp != null)
                {
                    var formatRange = string.Join(",", evo.Pvp.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"PVP: {formatRange}");
                }

                // Add G-Cell criteria
                if (evo.GCellHatch != null) lines.Add($"G-Cell Hatch: {(evo.GCellHatch.Value ? "Required" : "No")}");
                if (evo.BlueGCells != null)
                {
                    var formatRange = string.Join(",", evo.BlueGCells.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Blue G-Cells: {formatRange}");
                }
                if (evo.YellowGCells != null)
                {
                    var formatRange = string.Join(",", evo.YellowGCells.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Yellow G-Cells: {formatRange}");
                }
                if (evo.RedGCells != null)
                {
                    var formatRange = string.Join(",", evo.RedGCells.Select(v => v == 999999 ? "+" : v.ToString()));
                    lines.Add($"Red G-Cells: {formatRange}");
                }
            }
            if (lines.Count == 0)
                return "no criteria";
            return string.Join("\n", lines);
        }
    }
}
